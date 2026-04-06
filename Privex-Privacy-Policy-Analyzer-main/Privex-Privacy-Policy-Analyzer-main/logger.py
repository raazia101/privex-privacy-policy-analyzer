"""
Logging configuration for Privacy Policy Analyzer
"""

import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

def setup_logger(name: str = "privacy_analyzer", level: str = None) -> logging.Logger:
    """
    Set up a logger with both file and console handlers
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    
    Returns:
        Configured logger instance
    """
    # Get log level from environment or use default
    if level is None:
        level = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level, logging.INFO))
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(simple_formatter)
    logger.addHandler(console_handler)
    
    # File handler with rotation
    log_file = os.getenv('LOG_FILE', 'privacy_analyzer.log')
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(getattr(logging, level, logging.DEBUG))
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    return logger

def log_api_request(logger: logging.Logger, method: str, endpoint: str, 
                   status_code: int = None, error: str = None):
    """Log API request details"""
    if error:
        logger.error(f"API {method} {endpoint} - ERROR: {error}")
    else:
        logger.info(f"API {method} {endpoint} - Status: {status_code or 'Processing'}")

def log_analysis(logger: logging.Logger, url: str, method: str, 
                risk_level: str = None, data_points: int = None, 
                duration: float = None, error: str = None):
    """Log privacy policy analysis details"""
    if error:
        logger.error(f"Analysis {method} failed for {url} - Error: {error}")
    else:
        logger.info(
            f"Analysis {method} completed for {url} - "
            f"Risk: {risk_level}, Data points: {data_points}, "
            f"Duration: {duration:.2f}s" if duration else ""
        )

def log_rag_operation(logger: logging.Logger, operation: str, 
                     details: str = None, error: str = None):
    """Log RAG-specific operations"""
    if error:
        logger.error(f"RAG {operation} - Error: {error}")
    else:
        logger.info(f"RAG {operation} - {details}" if details else f"RAG {operation}")

# Initialize main logger
logger = setup_logger()
