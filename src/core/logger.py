import logging
import os
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get log level from environment (default: INFO)
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
log_level_mapping = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL
}

# Configure logger
log = logging.getLogger(__name__)
log.setLevel(log_level_mapping.get(log_level, logging.INFO))

# Create logs directory if it doesn't exist
logs_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(logs_dir, exist_ok=True)

# File formatter
file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Combined log handler
combined_log_path = os.path.join(logs_dir, 'combined.log')
combined_handler = RotatingFileHandler(combined_log_path, maxBytes=10*1024*1024, backupCount=5)
combined_handler.setFormatter(file_formatter)
log.addHandler(combined_handler)

# Error log handler
error_log_path = os.path.join(logs_dir, 'error.log')
error_handler = RotatingFileHandler(error_log_path, maxBytes=10*1024*1024, backupCount=5)
error_handler.setLevel(logging.ERROR)
error_handler.setFormatter(file_formatter)
log.addHandler(error_handler)

# Console formatter
console_formatter = logging.Formatter('%(levelname)s: %(message)s')

# Console handler
console_handler = logging.StreamHandler()
console_handler.setFormatter(console_formatter)
log.addHandler(console_handler)