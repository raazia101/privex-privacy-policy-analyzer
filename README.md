# Privex: Privacy Policy Analyzer

## Overview
Privex is an NLP-based system designed to analyze privacy policies and identify potential data-sharing risks. The system combines semantic search, web scraping, and retrieval-augmented techniques to extract meaningful insights from complex legal documents.

---

## Problem Statement
Privacy policies are often lengthy, complex, and difficult for users to interpret. As a result, users are unaware of how their data is collected, shared, and processed.

Privex addresses this challenge by applying natural language processing techniques to automatically extract, analyze, and highlight critical information related to data usage and risk.

---

## Approach

The system follows a structured pipeline:

1. **Data Collection**
   - Extracted privacy policy content using web scraping techniques  

2. **Preprocessing**
   - Cleaned and structured raw text data for analysis  

3. **Semantic Analysis**
   - Generated embeddings using SBERT  
   - Applied similarity search techniques using FAISS  
   - Incorporated Retrieval-Augmented Generation (RAG) for improved contextual understanding  

4. **Risk Evaluation**
   - Identified potentially sensitive clauses and data-sharing patterns  
   - Applied literature-informed methods to assess risk levels  

5. **Data Storage & Visualization**
   - Stored processed data in a database  
   - Displayed insights through dashboards and web interfaces  

---

## Features
- Semantic analysis of privacy policies using NLP techniques  
- Retrieval-Augmented Generation (RAG) for contextual understanding  
- Identification of data-sharing risks and sensitive clauses  
- Dashboard-based visualization of insights  
- Scalable pipeline for processing large text datasets  

---

## My Contribution
This project was developed as part of a group.

My contributions include:
- Conducted literature review to identify appropriate methods for privacy policy analysis and risk evaluation  
- Selected and adapted suitable approaches based on existing research  
- Developed the initial model and structured the risk evaluation pipeline  
- Implemented components of the NLP pipeline for semantic analysis  
- Contributed to integration of embedding-based techniques and system components  

---

## Tech Stack
- Python  
- SBERT (Sentence Transformers)  
- FAISS  
- NLP libraries (NLTK / spaCy)  
- Web scraping tools  
- SQLite / database handling  
- HTML (for frontend templates)  

---

## Project Structure

```
privex-privacy-policy-analyzer/
│
├── src/                     # Core application logic
│   ├── app.py               # Application entry point
│   ├── main.py              # Pipeline controller
│   ├── extractor.py         # Policy extraction logic
│   ├── scraper.py           # Web scraping module
│   ├── rag_enhanced.py      # RAG-based analysis
│   ├── graph_builder.py     # Relationship analysis
│   ├── database.py          # Data storage handling
│   └── logger.py            # Logging utilities
│
├── templates/               # HTML templates
├── dashboard/               # Visualization components
├── tests/                   # Test scripts
│
├── notebook.ipynb           # Experimentation and analysis
├── requirements.txt         # Dependencies
├── README.md                # Project documentation
├── .env.example             # Environment variables template
```

---

## Sample Workflow

1. Input a website or privacy policy document  
2. Extract policy text using the scraping module  
3. Process and analyze using the NLP pipeline  
4. Generate embeddings and perform similarity analysis  
5. Identify risk patterns and generate insights  
6. Visualize results through dashboards  

---

## Future Improvements
- Risk classification of privacy policies into categories  
- Real-time analysis of live websites  
- Support for multilingual privacy policies  
- Improved scalability using distributed data systems  

---

## Acknowledgements
This project was developed as part of a collaborative academic effort.

---

## Contact
For queries or collaboration, feel free to connect.
