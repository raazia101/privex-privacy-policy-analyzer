# Privacy Policy Analyzer - Enhanced with RAG

A comprehensive Chrome extension and dashboard system that automatically detects cookie consent banners, analyzes privacy policies, and tracks data collection across websites.

## Features

###  Automatic Detection
- **Cookie Banner Detection**: Automatically detects cookie consent banners on websites
- **Privacy Policy Scraping**: Automatically finds and analyzes privacy policies
- **Real-time Monitoring**: Continuously monitors websites as you browse

###  Comprehensive Dashboard
- **Risk Analysis**: Visual dashboard showing risk levels across sites
- **Data Collection Tracking**: Tracks what data each site collects
- **Third-party Sharing**: Monitors data sharing with third parties
- **Historical Data**: Maintains history of analyzed sites

###  RAG-Enhanced Analysis
- **Contextual Understanding**: Uses Retrieval-Augmented Generation for better analysis
- **Regulatory Compliance**: Checks GDPR and CCPA compliance
- **Semantic Search**: Finds similar privacy policies and patterns
- **Enhanced Risk Scoring**: More accurate risk assessment

## Architecture

### Chrome Extension
- **Content Script**: Detects cookie banners and privacy policy links
- **Background Service**: Manages automatic analysis and data storage
- **Popup Interface**: Manual analysis and quick insights

### Backend System
- **Flask API**: RESTful API for analysis and dashboard data
- **SQLite Database**: Persistent storage for site analysis
- **RAG Engine**: Advanced privacy policy analysis

### Dashboard
- **React-based UI**: Modern, responsive dashboard
- **Real-time Updates**: Live data visualization
- **Interactive Charts**: Risk distribution and data patterns

## Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- Chrome browser

### Backend Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd Privacy-Policy-Analyzer
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Download NLTK data:
```bash
python -c "import nltk; nltk.download('punkt')"
```

4. Start the Flask server:
```bash
python app.py
```

The backend will be available at `http://localhost:5000`

### Chrome Extension Setup

1. Open Chrome and go to `chrome://extensions/`
2. Enable "Developer mode"
3. Click "Load unpacked" and select the `extension` folder
4. The extension will be available in your toolbar

### Dashboard Access

Visit `http://localhost:5000` to access the dashboard

## Usage

### Automatic Mode
1. Browse the web normally
2. The extension automatically detects cookie banners
3. Privacy policies are analyzed in the background
4. Data appears in the dashboard

### Manual Mode
1. Click the extension icon
2. Click "Analyze Current Site"
3. View results in the popup
4. Click "View Graph" for visual representation

### Dashboard
1. Visit `http://localhost:5000`
2. View overall statistics
3. Browse analyzed sites
4. Check risk distributions
5. Export data as needed

## RAG Enhancement

The system includes an optional RAG (Retrieval-Augmented Generation) module for enhanced analysis:

### Features
- **Knowledge Base**: Built-in GDPR and CCPA regulations
- **Semantic Search**: Find similar policy clauses
- **Compliance Checking**: Automated regulatory compliance
- **Enhanced Risk Scoring**: Multi-factor risk assessment

### Enabling RAG
1. Install additional dependencies:
```bash
pip install sentence-transformers faiss-cpu openai
```

2. Set up OpenAI API key (optional):
```python
rag_analyzer = RAGPrivacyAnalyzer(api_key="your-openai-key")
```

3. Use the enhanced analyzer:
```python
result = rag_analyzer.analyze_policy_with_rag(policy_text, url)
```

## API Endpoints

### Analysis Endpoints
- `POST /api/analyze` - Analyze a privacy policy
- `POST /api/graph` - Get graph data for visualization

### Dashboard Endpoints
- `GET /api/dashboard` - Get dashboard statistics
- `GET /api/site/<url>` - Get detailed site information
- `GET /api/export` - Export all data

## Database Schema

### Tables
- **sites**: Website information and analysis status
- **analyses**: Detailed analysis results
- **third_parties**: Third-party services
- **data_types**: Types of data collected
- **site_third_parties**: Relationships between sites and third parties
- **site_data_types**: Relationships between sites and data types

## Configuration

### Extension Permissions
The extension requires:
- `activeTab` - Access current tab
- `scripting` - Inject content scripts
- `storage` - Store analysis data
- `tabs` - Manage tabs
- `host_permissions` - Access all websites

### Backend Configuration
- Flask runs on port 5000
- Database file: `privacy_data.db`
- CORS enabled for Chrome extension

## Development

### Project Structure
```
Privacy-Policy-Analyzer/
├── app.py              # Flask application
├── database.py         # Database operations
├── extractor.py        # Basic NLP extraction
├── scraper.py          # Web scraping utilities
├── rag_enhanced.py     # RAG enhancement module
├── extension/          # Chrome extension
│   ├── manifest.json
│   ├── content.js      # Content script
│   ├── background.js   # Service worker
│   ├── popup.js        # Popup logic
│   └── popup.html      # Popup UI
├── templates/          # Flask templates
│   └── dashboard.html  # Dashboard UI
└── requirements.txt    # Python dependencies
```

### Adding New Features
1. Extend the database schema in `database.py`
2. Add new API endpoints in `app.py`
3. Update the dashboard UI in `templates/dashboard.html`
4. Modify extension logic as needed

## Privacy & Security

### Data Handling
- All data is stored locally in SQLite database
- No data is sent to external servers (except optional OpenAI API)
- Extension only analyzes publicly available privacy policies

### Security Considerations
- Content scripts run in isolated worlds
- Background service has limited permissions
- Database access is restricted to local application

## Troubleshooting

### Common Issues
1. **Extension not loading**: Check manifest.json syntax
2. **Backend not responding**: Ensure Flask server is running
3. **No analysis results**: Check privacy policy accessibility
4. **Dashboard not updating**: Refresh the page

### Debug Mode
Enable debug mode in `app.py`:
```python
app.run(debug=True, port=5000)
```

### Logs
- Extension logs: Chrome Developer Tools → Extensions
- Backend logs: Flask console output
- Database: SQLite file location

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request
