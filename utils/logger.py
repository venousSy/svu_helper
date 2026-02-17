import logging
import sys
from config import settings

def setup_logger():
    """
    Configures and returns the root logger with a standard format.
    """
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Console Handler
    c_handler = logging.StreamHandler(sys.stdout)
    c_handler.setLevel(logging.INFO)
    c_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    c_handler.setFormatter(c_format)
    
    # File Handler (Optional, based on requirement)
    if hasattr(settings, 'LOG_FILE') and settings.LOG_FILE:
        f_handler = logging.FileHandler(settings.LOG_FILE, encoding='utf-8')
        f_handler.setLevel(logging.INFO)
        f_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        f_handler.setFormatter(f_format)
        logger.addHandler(f_handler)

    logger.addHandler(c_handler)
    
    return logger

# Create a default logger instance
logger = setup_logger()
