"""
RAG-Enhanced Privacy Policy Analyzer
This module implements Retrieval-Augmented Generation for better privacy policy analysis.
"""

import os
import json
import sqlite3
from typing import List, Dict, Optional
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss
from sklearn.metrics.pairwise import cosine_similarity
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

class RAGPrivacyAnalyzer:
    def __init__(self, api_key: str = None):
        """
        Initialize RAG analyzer with embedding model and LLM
        """
        # Load embedding model
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize OpenAI (or use local LLM)
        if api_key and OpenAI:
            self.client = OpenAI(api_key=api_key)
            self.use_local_llm = False
        else:
            self.client = None
            self.use_local_llm = True
        
        # Knowledge base for privacy regulations
        self.privacy_knowledge = self._load_privacy_knowledge()
        
        # FAISS index for similarity search
        self.index = None
        self.policy_texts = []
        
    def _load_privacy_knowledge(self) -> Dict:
        """Load privacy regulation knowledge base"""
        return {
            "gdpr": {
                "principles": [
                    "Lawfulness, fairness and transparency",
                    "Purpose limitation",
                    "Data minimization",
                    "Accuracy",
                    "Storage limitation",
                    "Integrity and confidentiality",
                    "Accountability"
                ],
                "rights": [
                    "Right to be informed",
                    "Right of access",
                    "Right to rectification",
                    "Right to erasure",
                    "Right to restrict processing",
                    "Right to data portability",
                    "Right to object"
                ],
                "key_terms": [
                    "personal data", "processing", "controller", "processor",
                    "data subject", "consent", "legitimate interest"
                ]
            },
            "ccpa": {
                "rights": [
                    "Right to know",
                    "Right to delete",
                    "Right to opt-out",
                    "Right to non-discrimination"
                ],
                "key_terms": [
                    "personal information", "sale", "sharing", "opt-out",
                    "do not sell", "consumer privacy act"
                ]
            },
            "risk_indicators": {
                "high": [
                    "sell your personal information",
                    "share with third parties",
                    "track across websites",
                    "profiling",
                    "automated decision making",
                    "cross-border transfer"
                ],
                "medium": [
                    "analytics",
                    "marketing",
                    "personalization",
                    "advertising",
                    "cookies"
                ],
                "low": [
                    "necessary for service",
                    "security",
                    "fraud prevention",
                    "legal compliance"
                ]
            }
        }
    
    def build_knowledge_index(self):
        """Build FAISS index with privacy knowledge"""
        knowledge_texts = []
        
        # Add GDPR principles
        for principle in self.privacy_knowledge["gdpr"]["principles"]:
            knowledge_texts.append(f"GDPR Principle: {principle}")
        
        # Add CCPA rights
        for right in self.privacy_knowledge["ccpa"]["rights"]:
            knowledge_texts.append(f"CCPA Right: {right}")
        
        # Add risk indicators
        for risk_level, indicators in self.privacy_knowledge["risk_indicators"].items():
            for indicator in indicators:
                knowledge_texts.append(f"Risk Indicator ({risk_level}): {indicator}")
        
        # Create embeddings
        embeddings = self.embedding_model.encode(knowledge_texts)
        
        # Build FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings.astype('float32'))
        
        self.knowledge_texts = knowledge_texts
        print(f"Built knowledge index with {len(knowledge_texts)} entries")
    
    def add_policy_to_index(self, policy_text: str, url: str):
        """Add a privacy policy to the search index"""
        # Split policy into chunks
        chunks = self._chunk_text(policy_text)
        
        for chunk in chunks:
            embedding = self.embedding_model.encode([chunk])
            if self.index is None:
                dimension = embedding.shape[1]
                self.index = faiss.IndexFlatL2(dimension)
            
            self.index.add(embedding.astype('float32'))
            self.policy_texts.append({
                "text": chunk,
                "url": url,
                "type": "policy"
            })
    
    def _chunk_text(self, text: str, chunk_size: int = 500) -> List[str]:
        """Split text into chunks for processing"""
        sentences = text.split('. ')
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) < chunk_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def search_similar_policies(self, query: str, k: int = 5) -> List[Dict]:
        """Search for similar policy clauses"""
        if self.index is None:
            return []
        
        query_embedding = self.embedding_model.encode([query])
        distances, indices = self.index.search(query_embedding.astype('float32'), k)
        
        results = []
        for i, (dist, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < len(self.policy_texts):
                result = self.policy_texts[idx]
                result["similarity"] = 1 - (dist / 2)  # Convert L2 distance to similarity
                results.append(result)
        
        return results
    
    def analyze_policy_with_rag(self, policy_text: str, url: str) -> Dict:
        """
        Analyze privacy policy using RAG approach
        """
        # Add policy to index
        self.add_policy_to_index(policy_text, url)
        
        # Split into sentences for analysis
        sentences = self._chunk_text(policy_text, chunk_size=200)
        
        analysis = {
            "data_collected": [],
            "shared_with": [],
            "purpose": [],
            "risk_factors": [],
            "compliance_issues": [],
            "recommendations": []
        }
        
        for sentence in sentences:
            # Search for similar knowledge
            similar_items = self.search_similar_policies(sentence, k=3)
            
            # Extract data collection info
            data_entities = self._extract_data_entities(sentence)
            analysis["data_collected"].extend(data_entities)
            
            # Extract third parties
            third_parties = self._extract_third_parties(sentence)
            analysis["shared_with"].extend(third_parties)
            
            # Extract purposes
            purposes = self._extract_purposes(sentence)
            analysis["purpose"].extend(purposes)
            
            # Risk analysis using knowledge base
            risk_analysis = self._analyze_risk_with_knowledge(sentence, similar_items)
            analysis["risk_factors"].extend(risk_analysis)
            
            # Compliance checking
            compliance_issues = self._check_compliance(sentence, similar_items)
            analysis["compliance_issues"].extend(compliance_issues)
        
        # Remove duplicates
        for key in ["data_collected", "shared_with", "purpose", "risk_factors", "compliance_issues"]:
            analysis[key] = list(set(analysis[key]))
        
        # Generate recommendations using LLM
        analysis["recommendations"] = self._generate_recommendations(analysis)
        
        # Calculate enhanced risk score
        analysis["enhanced_risk_score"] = self._calculate_enhanced_risk_score(analysis)
        
        return analysis
    
    def _extract_data_entities(self, text: str) -> List[str]:
        """Extract data entities using enhanced patterns"""
        data_patterns = {
            "personal_info": ["name", "email", "phone", "address", "date of birth"],
            "location": ["location", "gps", "geolocation", "ip address"],
            "behavioral": ["browsing history", "clicks", "searches", "interactions"],
            "device": ["device id", "browser type", "operating system", "cookies"],
            "financial": ["payment", "credit card", "bank account", "billing"]
        }
        
        entities = []
        text_lower = text.lower()
        
        for category, patterns in data_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    entities.append(f"{category}:{pattern}")
        
        return entities
    
    def _extract_third_parties(self, text: str) -> List[str]:
        """Extract third-party services"""
        third_party_patterns = [
            "google", "facebook", "amazon", "microsoft", "apple",
            "analytics", "advertising", "marketing", "payment processor",
            "cloud provider", "cdn", "third party", "partner", "affiliate"
        ]
        
        found = []
        text_lower = text.lower()
        
        for pattern in third_party_patterns:
            if pattern in text_lower:
                found.append(pattern)
        
        return found
    
    def _extract_purposes(self, text: str) -> List[str]:
        """Extract data usage purposes"""
        purpose_patterns = {
            "analytics": ["analytics", "statistics", "measurement", "improvement"],
            "marketing": ["marketing", "advertising", "promotion", "personalization"],
            "security": ["security", "fraud", "prevention", "detection"],
            "legal": ["legal", "compliance", "regulatory", "obligation"],
            "service": ["service", "functionality", "operation", "maintenance"]
        }
        
        purposes = []
        text_lower = text.lower()
        
        for category, patterns in purpose_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    purposes.append(category)
        
        return purposes
    
    def _analyze_risk_with_knowledge(self, sentence: str, similar_items: List[Dict]) -> List[str]:
        """Analyze risk using knowledge base"""
        risks = []
        sentence_lower = sentence.lower()
        
        # Check against risk indicators
        for risk_level, indicators in self.privacy_knowledge["risk_indicators"].items():
            for indicator in indicators:
                if indicator in sentence_lower:
                    risks.append(f"{risk_level}_risk:{indicator}")
        
        # Check similar items for risk patterns
        for item in similar_items:
            if item.get("type") == "knowledge" and "Risk Indicator" in item.get("text", ""):
                risks.append(f"similar_risk:{item['text']}")
        
        return risks
    
    def _check_compliance(self, sentence: str, similar_items: List[Dict]) -> List[str]:
        """Check compliance with privacy regulations"""
        issues = []
        sentence_lower = sentence.lower()
        
        # GDPR compliance checks
        gdpr_issues = []
        if "personal data" in sentence_lower and "consent" not in sentence_lower:
            gdpr_issues.append("Potential GDPR issue: Personal data processing without explicit consent")
        
        if "share" in sentence_lower and "third party" in sentence_lower:
            gdpr_issues.append("Potential GDPR issue: Data sharing without proper disclosure")
        
        # CCPA compliance checks
        ccpa_issues = []
        if "sell" in sentence_lower and "personal information" in sentence_lower:
            ccpa_issues.append("Potential CCPA issue: Sale of personal information")
        
        if "opt-out" not in sentence_lower and "advertising" in sentence_lower:
            ccpa_issues.append("Potential CCPA issue: No opt-out mechanism mentioned")
        
        issues.extend(gdpr_issues)
        issues.extend(ccpa_issues)
        
        return issues
    
    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate recommendations using LLM or rule-based approach"""
        recommendations = []
        
        # Risk-based recommendations
        high_risk_factors = [r for r in analysis["risk_factors"] if "high_risk" in r]
        if high_risk_factors:
            recommendations.append("High-risk data practices detected. Consider limiting data sharing.")
        
        # Compliance recommendations
        if analysis["compliance_issues"]:
            recommendations.append("Review compliance issues with legal counsel.")
        
        # Data minimization recommendations
        if len(analysis["data_collected"]) > 5:
            recommendations.append("Consider data minimization - collect only necessary data.")
        
        # Third-party recommendations
        if len(analysis["shared_with"]) > 3:
            recommendations.append("Limit third-party data sharing to essential services only.")
        
        return recommendations
    
    def _calculate_enhanced_risk_score(self, analysis: Dict) -> Dict:
        """Calculate enhanced risk score using multiple factors"""
        score = 0
        factors = []
        
        # Data collection score
        data_score = min(len(analysis["data_collected"]) * 2, 20)
        score += data_score
        factors.append(f"Data collection: {data_score}")
        
        # Third-party sharing score
        third_party_score = len(analysis["shared_with"]) * 3
        score += third_party_score
        factors.append(f"Third-party sharing: {third_party_score}")
        
        # Risk factors score
        high_risk_count = len([r for r in analysis["risk_factors"] if "high_risk" in r])
        risk_score = high_risk_count * 5
        score += risk_score
        factors.append(f"Risk factors: {risk_score}")
        
        # Compliance issues score
        compliance_score = len(analysis["compliance_issues"]) * 4
        score += compliance_score
        factors.append(f"Compliance issues: {compliance_score}")
        
        # Determine risk level
        if score >= 30:
            risk_level = "CRITICAL"
        elif score >= 20:
            risk_level = "HIGH"
        elif score >= 10:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        return {
            "total_score": score,
            "risk_level": risk_level,
            "factors": factors,
            "breakdown": {
                "data_collection": data_score,
                "third_party_sharing": third_party_score,
                "risk_factors": risk_score,
                "compliance_issues": compliance_score
            }
        }

# Example usage
if __name__ == "__main__":
    # Initialize RAG analyzer
    rag_analyzer = RAGPrivacyAnalyzer()
    
    # Build knowledge index
    rag_analyzer.build_knowledge_index()
    
    # Example policy text
    sample_policy = """
    We collect your personal information including name, email, and location.
    We share this data with third-party advertising partners for marketing purposes.
    We use cookies to track your browsing behavior across websites.
    We may sell your personal information to data brokers.
    """
    
    # Analyze policy
    result = rag_analyzer.analyze_policy_with_rag(sample_policy, "https://example.com")
    
    print("RAG Analysis Results:")
    print(json.dumps(result, indent=2))
