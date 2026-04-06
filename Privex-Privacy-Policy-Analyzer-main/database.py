import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional

class PrivacyDatabase:
    def __init__(self, db_path: str = "privacy_data.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the database with required tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Sites table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sites (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT UNIQUE NOT NULL,
                    domain TEXT NOT NULL,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_analyzed TIMESTAMP,
                    cookie_banner_detected BOOLEAN DEFAULT FALSE,
                    privacy_policy_url TEXT,
                    risk_level TEXT DEFAULT 'UNKNOWN',
                    risk_score INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'PENDING'
                )
            ''')
            
            # Analysis results table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    site_id INTEGER,
                    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    data_collected TEXT,  -- JSON array
                    shared_with TEXT,     -- JSON array
                    purposes TEXT,        -- JSON array
                    risk_score INTEGER,
                    risk_level TEXT,
                    summary TEXT,
                    raw_response TEXT,    -- Full JSON response
                    FOREIGN KEY (site_id) REFERENCES sites (id)
                )
            ''')
            
            # Third parties table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS third_parties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    category TEXT,
                    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    site_count INTEGER DEFAULT 0
                )
            ''')
            
            # Data types table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type_name TEXT UNIQUE NOT NULL,
                    category TEXT,
                    sensitivity_level TEXT DEFAULT 'MEDIUM'
                )
            ''')
            
            # Site-third party relationships
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS site_third_parties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    site_id INTEGER,
                    third_party_id INTEGER,
                    purpose TEXT,
                    first_detected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (site_id) REFERENCES sites (id),
                    FOREIGN KEY (third_party_id) REFERENCES third_parties (id)
                )
            ''')
            
            # Site-data type relationships
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS site_data_types (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    site_id INTEGER,
                    data_type_id INTEGER,
                    collection_method TEXT,
                    purpose TEXT,
                    first_detected TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (site_id) REFERENCES sites (id),
                    FOREIGN KEY (data_type_id) REFERENCES data_types (id)
                )
            ''')
            
            conn.commit()
    
    def upsert_site(self, url: str, **kwargs) -> int:
        """Insert or update a site record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Extract domain from URL
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            
            cursor.execute('''
                INSERT OR REPLACE INTO sites 
                (url, domain, last_analyzed, cookie_banner_detected, 
                 privacy_policy_url, risk_level, risk_score, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                url,
                domain,
                datetime.now(),
                kwargs.get('cookie_banner_detected', False),
                kwargs.get('privacy_policy_url'),
                kwargs.get('risk_level', 'UNKNOWN'),
                kwargs.get('risk_score', 0),
                kwargs.get('status', 'PENDING')
            ))
            
            site_id = cursor.lastrowid
            conn.commit()
            return site_id
    
    def save_analysis(self, site_url: str, analysis_data: Dict) -> int:
        """Save analysis results for a site"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get or create site
            cursor.execute('SELECT id FROM sites WHERE url = ?', (site_url,))
            result = cursor.fetchone()
            
            if result:
                site_id = result[0]
            else:
                site_id = self.upsert_site(site_url)
            
            # Save analysis
            cursor.execute('''
                INSERT INTO analyses 
                (site_id, data_collected, shared_with, purposes, 
                 risk_score, risk_level, summary, raw_response)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                site_id,
                json.dumps(analysis_data.get('data', {}).get('data_collected', [])),
                json.dumps(analysis_data.get('data', {}).get('shared_with', [])),
                json.dumps(analysis_data.get('data', {}).get('purpose', [])),
                analysis_data.get('risk', {}).get('risk_score', 0),
                analysis_data.get('risk', {}).get('risk_level', 'UNKNOWN'),
                analysis_data.get('summary', ''),
                json.dumps(analysis_data)
            ))
            
            # Update site with latest analysis
            cursor.execute('''
                UPDATE sites SET 
                    last_analyzed = ?,
                    risk_level = ?,
                    risk_score = ?,
                    status = 'ANALYZED'
                WHERE id = ?
            ''', (
                datetime.now(),
                analysis_data.get('risk', {}).get('risk_level', 'UNKNOWN'),
                analysis_data.get('risk', {}).get('risk_score', 0),
                site_id
            ))
            
            # Process third parties and data types
            self._process_third_parties(site_id, analysis_data.get('data', {}))
            self._process_data_types(site_id, analysis_data.get('data', {}))
            
            conn.commit()
            return cursor.lastrowid
    
    def _process_third_parties(self, site_id: int, data: Dict):
        """Process and store third party information"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            third_parties = data.get('shared_with', [])
            for third_party in third_parties:
                # Insert third party if not exists
                cursor.execute('''
                    INSERT OR IGNORE INTO third_parties (name, category)
                    VALUES (?, ?)
                ''', (third_party, 'unknown'))
                
                # Get third party ID
                cursor.execute('SELECT id FROM third_parties WHERE name = ?', (third_party,))
                third_party_id = cursor.fetchone()[0]
                
                # Link to site
                cursor.execute('''
                    INSERT OR IGNORE INTO site_third_parties (site_id, third_party_id)
                    VALUES (?, ?)
                ''', (site_id, third_party_id))
                
                # Update site count
                cursor.execute('''
                    UPDATE third_parties 
                    SET site_count = site_count + 1
                    WHERE id = ?
                ''', (third_party_id,))
    
    def _process_data_types(self, site_id: int, data: Dict):
        """Process and store data type information"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            data_types = data.get('data_collected', [])
            for data_type in data_types:
                # Determine sensitivity level
                sensitivity = self._get_sensitivity_level(data_type)
                
                # Insert data type if not exists
                cursor.execute('''
                    INSERT OR IGNORE INTO data_types (type_name, sensitivity_level)
                    VALUES (?, ?)
                ''', (data_type, sensitivity))
                
                # Get data type ID
                cursor.execute('SELECT id FROM data_types WHERE type_name = ?', (data_type,))
                data_type_id = cursor.fetchone()[0]
                
                # Link to site
                cursor.execute('''
                    INSERT OR IGNORE INTO site_data_types (site_id, data_type_id)
                    VALUES (?, ?)
                ''', (site_id, data_type_id))
    
    def _get_sensitivity_level(self, data_type: str) -> str:
        """Determine sensitivity level for a data type"""
        high_sensitivity = ['email', 'phone', 'location', 'personal information', 'name']
        low_sensitivity = ['cookie', 'device information', 'usage data']
        
        data_type_lower = data_type.lower()
        if any(hs in data_type_lower for hs in high_sensitivity):
            return 'HIGH'
        elif any(ls in data_type_lower for ls in low_sensitivity):
            return 'LOW'
        else:
            return 'MEDIUM'
    
    def get_dashboard_data(self) -> Dict:
        """Get aggregated data for dashboard"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Site statistics
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_sites,
                    SUM(CASE WHEN risk_level = 'HIGH' THEN 1 ELSE 0 END) as high_risk,
                    SUM(CASE WHEN risk_level = 'MEDIUM' THEN 1 ELSE 0 END) as medium_risk,
                    SUM(CASE WHEN risk_level = 'LOW' THEN 1 ELSE 0 END) as low_risk,
                    SUM(CASE WHEN cookie_banner_detected = 1 THEN 1 ELSE 0 END) as with_cookie_banners
                FROM sites
            ''')
            
            stats = cursor.fetchone()
            
            # Recent sites with analysis
            cursor.execute('''
                SELECT s.url, s.risk_level, s.risk_score, s.cookie_banner_detected,
                       a.data_collected, a.shared_with, a.purposes, a.summary
                FROM sites s
                LEFT JOIN analyses a ON s.id = a.site_id
                WHERE s.status = 'ANALYZED'
                ORDER BY s.last_analyzed DESC
                LIMIT 20
            ''')
            
            sites_data = []
            for row in cursor.fetchall():
                sites_data.append({
                    'url': row[0],
                    'risk_level': row[1],
                    'risk_score': row[2],
                    'cookie_banner_detected': bool(row[3]),
                    'data_collected': json.loads(row[4]) if row[4] else [],
                    'shared_with': json.loads(row[5]) if row[5] else [],
                    'purposes': json.loads(row[6]) if row[6] else [],
                    'summary': row[7]
                })
            
            # Top third parties
            cursor.execute('''
                SELECT name, site_count
                FROM third_parties
                WHERE site_count > 0
                ORDER BY site_count DESC
                LIMIT 10
            ''')
            
            top_third_parties = [{'name': row[0], 'site_count': row[1]} for row in cursor.fetchall()]
            
            # Data type frequency
            cursor.execute('''
                SELECT dt.type_name, COUNT(sdt.site_id) as site_count
                FROM data_types dt
                JOIN site_data_types sdt ON dt.id = sdt.data_type_id
                GROUP BY dt.type_name
                ORDER BY site_count DESC
                LIMIT 10
            ''')
            
            data_type_frequency = [{'type': row[0], 'site_count': row[1]} for row in cursor.fetchall()]
            
            return {
                'stats': {
                    'total_sites': stats[0],
                    'high_risk_sites': stats[1],
                    'medium_risk_sites': stats[2],
                    'low_risk_sites': stats[3],
                    'sites_with_cookie_banners': stats[4]
                },
                'recent_sites': sites_data,
                'top_third_parties': top_third_parties,
                'data_type_frequency': data_type_frequency
            }
    
    def get_site_details(self, url: str) -> Optional[Dict]:
        """Get detailed information for a specific site"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT s.*, a.data_collected, a.shared_with, a.purposes, 
                       a.risk_score, a.risk_level, a.summary, a.raw_response
                FROM sites s
                LEFT JOIN analyses a ON s.id = a.site_id
                WHERE s.url = ?
                ORDER BY a.analysis_date DESC
                LIMIT 1
            ''', (url,))
            
            result = cursor.fetchone()
            if not result:
                return None
            
            return {
                'url': result[1],
                'domain': result[2],
                'first_seen': result[3],
                'last_analyzed': result[4],
                'cookie_banner_detected': bool(result[5]),
                'privacy_policy_url': result[6],
                'risk_level': result[7],
                'risk_score': result[8],
                'status': result[9],
                'data_collected': json.loads(result[10]) if result[10] else [],
                'shared_with': json.loads(result[11]) if result[11] else [],
                'purposes': json.loads(result[12]) if result[12] else [],
                'summary': result[14],
                'full_analysis': json.loads(result[15]) if result[15] else {}
            }
