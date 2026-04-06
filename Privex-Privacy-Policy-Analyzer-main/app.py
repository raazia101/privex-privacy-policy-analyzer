from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from scraper import get_policy_text
from extractor import split_sentences, simple_extract, calculate_risk_score, simplify_policy
from database import PrivacyDatabase
import os
from dotenv import load_dotenv
import time
from logger import logger, log_api_request, log_analysis, log_rag_operation

def generate_privacy_insights(extracted_data, risk):
    """Generate comprehensive privacy insights and recommendations"""
    insights = {
        "recommendations": [],
        "concerns": [],
        "positive_aspects": [],
        "key_findings": []
    }
    
    # Data collection insights
    data_categories = extracted_data.get("data_categories", {})
    sensitive_categories = ["personal_identifiers", "contact_information", "financial_data", "health_data"]
    
    sensitive_found = []
    for category in sensitive_categories:
        if data_categories.get(category):
            sensitive_found.append(category.replace('_', ' ').title())
    
    if sensitive_found:
        insights["concerns"].append(f"Collects sensitive data: {', '.join(sensitive_found)}")
        insights["recommendations"].append("Review what sensitive data is necessary and consider minimizing collection")
    
    # Sharing practices insights
    sharing_practices = extracted_data.get("sharing_practices", {})
    if sharing_practices.get("marketing_partners"):
        insights["concerns"].append("Shares data with marketing partners")
        insights["recommendations"].append("Check if you can opt out of marketing data sharing")
    
    if sharing_practices.get("third_parties"):
        insights["concerns"].append("Shares data with third parties")
        insights["recommendations"].append("Review which third parties have access to your data")
    
    # User rights insights
    user_rights = extracted_data.get("user_rights", [])
    if user_rights:
        insights["positive_aspects"].append(f"Policy mentions {len(user_rights)} user rights")
        if any('consent' in right.lower() for right in user_rights):
            insights["positive_aspects"].append("Consent mechanisms are mentioned")
        if any('opt out' in right.lower() for right in user_rights):
            insights["positive_aspects"].append("Opt-out options are available")
    else:
        insights["concerns"].append("Limited user rights mentioned in policy")
        insights["recommendations"].append("Contact the company to understand your data rights")
    
    # Risk-based insights
    risk_level = risk.get("risk_level", "UNKNOWN")
    if risk_level == "HIGH":
        insights["recommendations"].extend([
            "Exercise caution when sharing personal information",
            "Consider using privacy-focused alternatives",
            "Review and adjust privacy settings if available"
        ])
    elif risk_level == "MEDIUM":
        insights["recommendations"].extend([
            "Be mindful of what information you share",
            "Regularly review privacy settings"
        ])
    
    # International transfers
    if extracted_data.get("international_transfers"):
        insights["concerns"].append("Data is transferred internationally")
        insights["recommendations"].append("Understand which countries your data is transferred to")
    
    # Key findings summary
    total_data_types = len(extracted_data.get("data_collected", []))
    total_sharing_partners = len(extracted_data.get("shared_with", []))
    total_purposes = len(extracted_data.get("purpose", []))
    
    insights["key_findings"] = [
        f"Collects {total_data_types} types of data",
        f"Shares with {total_sharing_partners} types of recipients",
        f"Uses data for {total_purposes} purposes",
        f"Overall risk level: {risk_level}"
    ]
    
    return insights

def create_detailed_summary(extracted_data, risk, insights):
    """Create a comprehensive, human-readable summary"""
    summary_parts = []
    
    # Data collection summary
    data_categories = extracted_data.get("data_categories", {})
    active_categories = [k.replace('_', ' ').title() for k, v in data_categories.items() if v]
    
    if active_categories:
        summary_parts.append(f"This privacy policy indicates data collection across {len(active_categories)} categories: {', '.join(active_categories)}.")
    
    # Sharing practices summary
    sharing_practices = extracted_data.get("sharing_practices", {})
    sharing_types = [k.replace('_', ' ').title() for k, v in sharing_practices.items() if v]
    
    if sharing_types:
        summary_parts.append(f"The policy mentions sharing data through {len(sharing_types)} types of arrangements: {', '.join(sharing_types)}.")
    
    # Purpose summary
    data_purposes = extracted_data.get("data_purposes", {})
    purpose_types = [k.replace('_', ' ').title() for k, v in data_purposes.items() if v]
    
    if purpose_types:
        summary_parts.append(f"Data is used for {len(purpose_types)} main purposes: {', '.join(purpose_types)}.")
    
    # User rights summary
    user_rights = extracted_data.get("user_rights", [])
    if user_rights:
        summary_parts.append(f"The policy provides information about {len(user_rights)} user rights and protections.")
    else:
        summary_parts.append("The policy provides limited information about user rights.")
    
    # Risk assessment
    risk_level = risk.get("risk_level", "UNKNOWN")
    risk_score = risk.get("risk_score", 0)
    summary_parts.append(f"Overall Privacy Risk Assessment: {risk_level} (Score: {risk_score}/30).")
    
    # Recommendations
    recommendations = insights.get("recommendations", [])
    if recommendations:
        summary_parts.append(f"Key recommendations: {'; '.join(recommendations[:3])}.")
    
    return " ".join(summary_parts)

# Try to import RAG components
try:
    from rag_enhanced import RAGPrivacyAnalyzer
    RAG_AVAILABLE = True
except ImportError as e:
    logger.warning(f"RAG components not available: {e}")
    RAG_AVAILABLE = False
    RAGPrivacyAnalyzer = None

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)  # allows Chrome extension to access backend

# Initialize database
db = PrivacyDatabase()

# Initialize RAG analyzer if enabled and available
ENABLE_RAG = os.getenv('ENABLE_RAG', 'False').lower() == 'true' and RAG_AVAILABLE
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if ENABLE_RAG and RAG_AVAILABLE:
    try:
        rag_analyzer = RAGPrivacyAnalyzer(api_key=OPENAI_API_KEY)
        rag_analyzer.build_knowledge_index()
        logger.info("RAG analyzer initialized successfully")
        log_rag_operation(logger, "initialization", "RAG analyzer ready")
    except Exception as e:
        logger.error(f"Failed to initialize RAG analyzer: {e}")
        log_rag_operation(logger, "initialization", error=str(e))
        rag_analyzer = None
        ENABLE_RAG = False
else:
    rag_analyzer = None
    if RAG_AVAILABLE:
        logger.info("RAG analyzer disabled by configuration")
    else:
        logger.info("RAG analyzer not available - missing dependencies")

@app.route("/")
def home():
    """Home page with extension info"""
    rag_status = "Enabled" if ENABLE_RAG else "Disabled"
    return f"""
    <h1>Privacy Policy Analyzer Backend</h1>
    <p>API server is running. Use the Chrome extension to analyze privacy policies.</p>
    <p><strong>RAG Analysis:</strong> {rag_status}</p>
    <ul>
        <li><a href="/api/dashboard">Dashboard API</a></li>
        <li><a href="/api/export">Export Data</a></li>
        <li><a href="/dashboard">Modern Dashboard</a></li>
        <li><a href="/dashboard-legacy">Legacy Dashboard</a></li>
    </ul>
    """

@app.route("/dashboard")
def dashboard_react():
    """Serve the modern React dashboard"""
    return render_template("dashboard-react.html")

@app.route("/dashboard-legacy")
def dashboard_legacy():
    """Serve the legacy dashboard"""
    return render_template("dashboard.html")

@app.route("/api/analyze", methods=["POST"])
def analyze():
    start_time = time.time()
    url = None
    method = "basic"
    
    try:
        data = request.json
        url = data.get("url")
        use_rag = data.get("use_rag", ENABLE_RAG)

        if not url:
            log_api_request(logger, "POST", "/api/analyze", 400, "No URL provided")
            return jsonify({"error": "No URL provided"}), 400

        logger.info(f"Starting analysis for URL: {url}")
        
        # Step 1: Scrape privacy policy text
        text = get_policy_text(url)

        if not text:
            error_msg = "Failed to extract text from privacy policy"
            log_analysis(logger, url, method, error=error_msg, duration=time.time() - start_time)
            return jsonify({"error": error_msg}), 500

        # Step 2: Choose analysis method
        if use_rag and rag_analyzer:
            method = "rag_enhanced"
            log_rag_operation(logger, "analysis", f"Starting RAG analysis for {url}")
            
            # Use RAG-enhanced analysis
            extracted_data = rag_analyzer.analyze_policy_with_rag(text, url)
            
            # Convert to expected format
            result_data = {
                "data_collected": extracted_data.get("data_collected", []),
                "shared_with": extracted_data.get("shared_with", []),
                "purpose": extracted_data.get("purpose", [])
            }
            
            # Use enhanced risk score
            risk_info = extracted_data.get("enhanced_risk_score", {})
            risk = {
                "risk_score": risk_info.get("total_score", 0),
                "risk_level": risk_info.get("risk_level", "UNKNOWN"),
                "factors": risk_info.get("factors", []),
                "breakdown": risk_info.get("breakdown", {})
            }
            
            # Enhanced summary
            summary = f"""
            RAG-Enhanced Analysis Complete:
            
            Risk Level: {risk['risk_level']} (Score: {risk['risk_score']})
            
            Data Types Found: {len(result_data['data_collected'])}
            Third Parties: {len(result_data['shared_with'])}
            Purposes: {len(result_data['purpose'])}
            
            Compliance Issues: {len(extracted_data.get('compliance_issues', []))}
            Recommendations: {len(extracted_data.get('recommendations', []))}
            
            Key Findings:
            {chr(10).join(f'• {issue}' for issue in extracted_data.get('compliance_issues', [])[:3])}
            """
            
            # Add RAG-specific data
            result = {
                "status": "success",
                "data": result_data,
                "risk": risk,
                "summary": summary,
                "rag_analysis": {
                    "compliance_issues": extracted_data.get("compliance_issues", []),
                    "recommendations": extracted_data.get("recommendations", []),
                    "risk_factors": extracted_data.get("risk_factors", [])
                },
                "analysis_method": "rag_enhanced"
            }
            
            log_rag_operation(logger, "analysis", f"RAG analysis completed for {url}")
        else:
            # Use basic analysis
            sentences = split_sentences(text)
            extracted_data = simple_extract(sentences)
            risk = calculate_risk_score(extracted_data)
            simple_summary = simplify_policy(extracted_data, risk)

            result = {
                "status": "success",
                "data": extracted_data,
                "risk": risk,
                "summary": simple_summary,
                "analysis_method": "basic"
            }
        
        # Save to database
        try:
            db.save_analysis(url, result)
            logger.info(f"Analysis saved to database for {url}")
        except Exception as db_error:
            logger.error(f"Failed to save analysis to database: {db_error}")

        duration = time.time() - start_time
        log_analysis(
            logger, url, method, 
            risk_level=result.get("risk", {}).get("risk_level"),
            data_points=len(result.get("data", {}).get("data_collected", [])),
            duration=duration
        )
        
        log_api_request(logger, "POST", "/api/analyze", 200)
        return jsonify(result)

    except Exception as e:
        duration = time.time() - start_time
        error_msg = str(e)
        logger.error(f"Unexpected error in analyze endpoint: {error_msg}")
        log_analysis(logger, url or "unknown", method, error=error_msg, duration=duration)
        log_api_request(logger, "POST", "/api/analyze", 500, error_msg)
        return jsonify({"error": error_msg}), 500

@app.route("/api/analyze/detailed", methods=["POST"])
def analyze_detailed():
    """Enhanced analysis endpoint with comprehensive privacy insights"""
    start_time = time.time()
    url = None
    method = "enhanced"
    
    try:
        data = request.json
        url = data.get("url")
        use_rag = data.get("use_rag", ENABLE_RAG)

        if not url:
            log_api_request(logger, "POST", "/api/analyze/detailed", 400, "No URL provided")
            return jsonify({"error": "No URL provided"}), 400

        logger.info(f"Starting detailed analysis for URL: {url}")
        
        # Step 1: Scrape privacy policy text
        text = get_policy_text(url)

        if not text:
            error_msg = "Failed to extract text from privacy policy"
            log_analysis(logger, url, method, error=error_msg, duration=time.time() - start_time)
            return jsonify({"error": error_msg}), 500

        # Step 2: Enhanced extraction
        sentences = split_sentences(text)
        extracted_data = simple_extract(sentences)
        risk = calculate_risk_score(extracted_data)
        
        # Step 3: Generate comprehensive insights
        insights = generate_privacy_insights(extracted_data, risk)
        
        # Step 4: Create detailed summary
        detailed_summary = create_detailed_summary(extracted_data, risk, insights)

        result = {
            "status": "success",
            "url": url,
            "analysis_timestamp": time.time(),
            "data_collection": {
                "summary": f"Collects {len(extracted_data.get('data_collected', []))} types of data across {len([k for k, v in extracted_data.get('data_categories', {}).items() if v])} categories",
                "categories": extracted_data.get("data_categories", {}),
                "total_data_points": len(extracted_data.get('data_collected', [])),
                "sensitive_data_present": any(extracted_data.get('data_categories', {}).get(cat) for cat in ['personal_identifiers', 'contact_information', 'financial_data', 'health_data'])
            },
            "sharing_practices": {
                "summary": f"Shares data with {len(extracted_data.get('shared_with', []))} types of recipients",
                "categories": extracted_data.get("sharing_practices", {}),
                "total_sharing_partners": len(extracted_data.get('shared_with', [])),
                "shares_with_marketing": bool(extracted_data.get('sharing_practices', {}).get('marketing_partners')),
                "shares_with_third_parties": bool(extracted_data.get('sharing_practices', {}).get('third_parties'))
            },
            "data_purposes": {
                "summary": f"Uses data for {len(extracted_data.get('purpose', []))} different purposes",
                "categories": extracted_data.get("data_purposes", {}),
                "total_purposes": len(extracted_data.get('purpose', [])),
                "uses_for_marketing": bool(extracted_data.get('data_purposes', {}).get('marketing')),
                "uses_for_analytics": bool(extracted_data.get('data_purposes', {}).get('analytics'))
            },
            "user_rights": {
                "rights_mentioned": extracted_data.get("user_rights", []),
                "total_rights": len(extracted_data.get('user_rights', [])),
                "has_consent_mechanisms": any('consent' in right.lower() for right in extracted_data.get('user_rights', [])),
                "has_opt_out_options": any('opt out' in right.lower() for right in extracted_data.get('user_rights', []))
            },
            "data_retention": {
                "policies_found": extracted_data.get("retention_period", []),
                "has_retention_policy": bool(extracted_data.get('retention_period', [])),
                "policy_count": len(extracted_data.get('retention_period', []))
            },
            "international_transfers": {
                "mentions": extracted_data.get("international_transfers", []),
                "has_international_transfers": bool(extracted_data.get('international_transfers', [])),
                "transfer_count": len(extracted_data.get('international_transfers', []))
            },
            "risk_assessment": {
                "overall_score": risk.get("risk_score", 0),
                "risk_level": risk.get("risk_level", "UNKNOWN"),
                "risk_factors": risk.get("factors", []),
                "score_breakdown": risk.get("breakdown", {}),
                "recommendations": insights.get("recommendations", []),
                "compliance_concerns": insights.get("concerns", [])
            },
            "summary": detailed_summary,
            "insights": insights,
            "analysis_method": "enhanced"
        }
        
        # Save to database
        try:
            db.save_analysis(url, result)
            logger.info(f"Detailed analysis saved to database for {url}")
        except Exception as db_error:
            logger.error(f"Failed to save detailed analysis to database: {db_error}")

        duration = time.time() - start_time
        log_analysis(
            logger, url, method, 
            risk_level=result.get("risk_assessment", {}).get("risk_level"),
            data_points=result.get("data_collection", {}).get("total_data_points", 0),
            duration=duration
        )
        
        log_api_request(logger, "POST", "/api/analyze/detailed", 200)
        return jsonify(result)

    except Exception as e:
        duration = time.time() - start_time
        error_msg = str(e)
        logger.error(f"Unexpected error in detailed analyze endpoint: {error_msg}")
        log_analysis(logger, url or "unknown", method, error=error_msg, duration=duration)
        log_api_request(logger, "POST", "/api/analyze/detailed", 500, error_msg)
        return jsonify({"error": error_msg}), 500

@app.route("/api/graph", methods=["POST"])
def graph():
    data = request.json
    url = data.get("url")

    # Step 1: Extract text
    text = get_policy_text(url)

    if not text:
        return jsonify({"nodes": [], "edges": []})

    # Step 2: NLP extraction
    sentences = split_sentences(text)
    extracted_data = simple_extract(sentences)

    # REMOVE DUPLICATES using set()
    unique_data = list(set(extracted_data.get("data_collected", [])))
    unique_third = list(set(extracted_data.get("shared_with", [])))
    unique_purpose = list(set(extracted_data.get("purpose", [])))

    # Base nodes
    nodes = [
        {"id": "User", "label": "User"},
        {"id": "Website", "label": "Website"}
    ]

    edges = [
        {"from": "User", "to": "Website", "label": "Provides Data"}
    ]

    # Data collected nodes
    for d in unique_data:
        nodes.append({"id": f"data_{d}", "label": d})
        edges.append({"from": "Website", "to": f"data_{d}", "label": "Collects"})

    # Third party nodes
    for t in unique_third:
        nodes.append({"id": f"third_{t}", "label": t})
        edges.append({"from": "Website", "to": f"third_{t}", "label": "Shares With"})

    # Purpose nodes
    for p in unique_purpose:
        nodes.append({"id": f"purpose_{p}", "label": p})
        edges.append({"from": "Website", "to": f"purpose_{p}", "label": "Used For"})

    return jsonify({
        "nodes": nodes,
        "edges": edges
    })

@app.route("/api/dashboard", methods=["GET"])
def dashboard_data():
    """Get dashboard statistics and data"""
    try:
        data = db.get_dashboard_data()
        log_api_request(logger, "GET", "/api/dashboard", 200)
        return jsonify(data)
    except Exception as e:
        error_msg = f"Failed to get dashboard data: {str(e)}"
        logger.error(error_msg)
        log_api_request(logger, "GET", "/api/dashboard", 500, error_msg)
        return jsonify({"error": error_msg}), 500

@app.route("/api/site/<path:url>", methods=["GET"])
def site_details(url):
    """Get detailed information for a specific site"""
    try:
        details = db.get_site_details(f"https://{url}")
        if not details:
            log_api_request(logger, "GET", f"/api/site/{url}", 404, "Site not found")
            return jsonify({"error": "Site not found"}), 404
        log_api_request(logger, "GET", f"/api/site/{url}", 200)
        return jsonify(details)
    except Exception as e:
        error_msg = f"Failed to get site details: {str(e)}"
        logger.error(error_msg)
        log_api_request(logger, "GET", f"/api/site/{url}", 500, error_msg)
        return jsonify({"error": error_msg}), 500

@app.route("/api/export", methods=["GET"])
def export_data():
    """Export all data as JSON"""
    try:
        data = db.get_dashboard_data()
        log_api_request(logger, "GET", "/api/export", 200)
        return jsonify(data)
    except Exception as e:
        error_msg = f"Failed to export data: {str(e)}"
        logger.error(error_msg)
        log_api_request(logger, "GET", "/api/export", 500, error_msg)
        return jsonify({"error": error_msg}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
