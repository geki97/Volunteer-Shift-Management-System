import logging
from datetime import datetime
from pathlib import Path
from config.settings import LOG_FILE_PATH


class SafeConsoleHandler(logging.StreamHandler):
    """Console handler that degrades gracefully on limited terminal encodings."""

    def emit(self, record):
        msg = self.format(record)
        stream = self.stream
        encoding = getattr(stream, 'encoding', None) or 'utf-8'
        safe_msg = msg.encode(encoding, errors='replace').decode(encoding, errors='replace')
        stream.write(safe_msg + self.terminator)
        self.flush()

def setup_logger(name, log_file=None, level=logging.INFO):
    """
    Set up logger with file and console handlers
    
    Args:
        name: Logger name
        log_file: Optional specific log file name
        level: Logging level
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear any existing handlers
    logger.handlers = []
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = logging.Formatter(
        '%(levelname)s: %(message)s'
    )
    
    # Console handler
    console_handler = SafeConsoleHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file is None:
        log_file = f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
    
    file_path = LOG_FILE_PATH / log_file
    file_handler = logging.FileHandler(file_path, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    return logger

# Create default logger
logger = setup_logger('volunteer_system')
