"""
Unit tests for Privacy Policy Analyzer Flask App
"""

import unittest
import json
from unittest.mock import patch, MagicMock
import sys
import os

# Add the parent directory to the path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from database import PrivacyDatabase

class TestPrivacyAnalyzer(unittest.TestCase):
    def setUp(self):
        """Set up test client"""
        self.app = app.test_client()
        self.app.testing = True
        
    def test_home_endpoint(self):
        """Test the home endpoint"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Privacy Policy Analyzer Backend', response.data)
        
    def test_analyze_endpoint_no_url(self):
        """Test analyze endpoint with no URL"""
        response = self.app.post('/api/analyze', 
                               json={},
                               content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'No URL provided')
        
    @patch('app.get_policy_text')
    @patch('app.split_sentences')
    @patch('app.simple_extract')
    @patch('app.calculate_risk_score')
    @patch('app.simplify_policy')
    @patch('app.db')
    def test_analyze_endpoint_basic_success(self, mock_db, mock_simplify, 
                                       mock_risk, mock_extract, 
                                       mock_sentences, mock_text):
        """Test successful basic analysis"""
        # Mock the dependencies
        mock_text.return_value = "Sample privacy policy text"
        mock_sentences.return_value = ["Sample sentence"]
        mock_extract.return_value = {
            "data_collected": ["email"],
            "shared_with": ["google"],
            "purpose": ["analytics"]
        }
        mock_risk.return_value = {
            "risk_score": 10,
            "risk_level": "LOW"
        }
        mock_simplify.return_value = "Simple summary"
        mock_db.save_analysis.return_value = 1
        
        response = self.app.post('/api/analyze',
                               json={"url": "https://example.com"},
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertEqual(data['analysis_method'], 'basic')
        self.assertIn('data', data)
        self.assertIn('risk', data)
        
    @patch('app.get_policy_text')
    def test_analyze_endpoint_no_text(self, mock_text):
        """Test analyze endpoint when no text can be extracted"""
        mock_text.return_value = None
        
        response = self.app.post('/api/analyze',
                               json={"url": "https://example.com"},
                               content_type='application/json')
        
        self.assertEqual(response.status_code, 500)
        data = json.loads(response.data)
        self.assertIn('error', data)
        
    def test_dashboard_endpoint(self):
        """Test dashboard endpoint"""
        with patch('app.db') as mock_db:
            mock_db.get_dashboard_data.return_value = {
                "stats": {"total_sites": 5},
                "recent_sites": [],
                "top_third_parties": [],
                "data_type_frequency": []
            }
            
            response = self.app.get('/api/dashboard')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertIn('stats', data)
            
    def test_export_endpoint(self):
        """Test export endpoint"""
        with patch('app.db') as mock_db:
            mock_db.get_dashboard_data.return_value = {"exported": "data"}
            
            response = self.app.get('/api/export')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            self.assertEqual(data, {"exported": "data"})
            
    @patch('app.db')
    def test_site_details_endpoint_found(self, mock_db):
        """Test site details endpoint when site is found"""
        mock_db.get_site_details.return_value = {
            "url": "https://example.com",
            "risk_level": "LOW",
            "data_collected": ["email"]
        }
        
        response = self.app.get('/api/site/example.com')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data['url'], 'https://example.com')
        
    @patch('app.db')
    def test_site_details_endpoint_not_found(self, mock_db):
        """Test site details endpoint when site is not found"""
        mock_db.get_site_details.return_value = None
        
        response = self.app.get('/api/site/notfound.com')
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.data)
        self.assertEqual(data['error'], 'Site not found')

class TestDatabase(unittest.TestCase):
    def setUp(self):
        """Set up test database"""
        self.db = PrivacyDatabase(':memory:')  # Use in-memory database for tests
        
    def test_database_initialization(self):
        """Test that database tables are created"""
        # Test that we can query the database without errors
        result = self.db.get_dashboard_data()
        self.assertIsInstance(result, dict)
        self.assertIn('stats', result)
        
    def test_save_and_retrieve_analysis(self):
        """Test saving and retrieving analysis"""
        test_data = {
            "status": "success",
            "data": {
                "data_collected": ["email", "name"],
                "shared_with": ["google"],
                "purpose": ["analytics"]
            },
            "risk": {
                "risk_score": 15,
                "risk_level": "MEDIUM"
            }
        }
        
        # Save analysis
        analysis_id = self.db.save_analysis("https://test.com", test_data)
        self.assertIsNotNone(analysis_id)
        
        # Retrieve analysis
        details = self.db.get_site_details("https://test.com")
        self.assertIsNotNone(details)
        self.assertEqual(details['url'], 'https://test.com')
        self.assertEqual(details['risk_level'], 'MEDIUM')
        
    def test_get_dashboard_data(self):
        """Test getting dashboard statistics"""
        # Add some test data
        test_data = {
            "status": "success",
            "data": {"data_collected": ["email"]},
            "risk": {"risk_score": 10, "risk_level": "LOW"}
        }
        
        self.db.save_analysis("https://low.com", test_data)
        
        test_data_high = {
            "status": "success", 
            "data": {"data_collected": ["email", "location", "name"]},
            "risk": {"risk_score": 30, "risk_level": "HIGH"}
        }
        self.db.save_analysis("https://high.com", test_data_high)
        
        dashboard_data = self.db.get_dashboard_data()
        self.assertEqual(dashboard_data['stats']['total_sites'], 2)
        self.assertEqual(dashboard_data['stats']['high_risk_sites'], 1)
        self.assertEqual(dashboard_data['stats']['low_risk_sites'], 1)

if __name__ == '__main__':
    unittest.main()
