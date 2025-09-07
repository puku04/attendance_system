"""
Centralized logging configuration for the attendance system
"""

import logging
import os
from datetime import datetime

class AttendanceLogger:
    """Centralized logging class for consistent error handling"""
    
    def __init__(self, name=None):
        self.logger = logging.getLogger(name or __name__)
        self._setup_logging()
    
    def _setup_logging(self):
        """Setup logging configuration"""
        if not self.logger.handlers:
            # Create logs directory if it doesn't exist
            log_dir = 'logs'
            os.makedirs(log_dir, exist_ok=True)
            
            # Create formatter
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            
            # File handler
            file_handler = logging.FileHandler(
                os.path.join(log_dir, f'attendance_{datetime.now().strftime("%Y%m%d")}.log')
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(logging.INFO)
            
            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.WARNING)
            
            # Add handlers
            self.logger.addHandler(file_handler)
            self.logger.addHandler(console_handler)
            self.logger.setLevel(logging.INFO)
    
    def info(self, message, extra=None):
        """Log info message"""
        self.logger.info(message, extra=extra)
    
    def warning(self, message, extra=None):
        """Log warning message"""
        self.logger.warning(message, extra=extra)
    
    def error(self, message, extra=None):
        """Log error message"""
        self.logger.error(message, extra=extra)
    
    def critical(self, message, extra=None):
        """Log critical message"""
        self.logger.critical(message, extra=extra)
    
    def debug(self, message, extra=None):
        """Log debug message"""
        self.logger.debug(message, extra=extra)

# Global logger instance
attendance_logger = AttendanceLogger('attendance_system')

def get_logger(name=None):
    """Get a logger instance"""
    return AttendanceLogger(name)