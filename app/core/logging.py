"""
Structured logging configuration for the application.

Provides consistent logging format with correlation IDs for request tracking.
"""
import logging
import sys
from typing import Any, Dict
import json
from datetime import datetime

from app.config import settings


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs in structured JSON format.
    
    This makes logs easier to parse and search in log aggregation systems.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format.
            
        Returns:
            JSON-formatted log string.
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        return json.dumps(log_data)


def setup_logging() -> None:
    """
    Configure application logging with appropriate handlers and formatters.
    
    Sets up structured logging to stdout with the configured log level.
    """
   
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
   
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
   
    if settings.is_production:
        formatter = StructuredFormatter()
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    handler.setFormatter(formatter)
    
    
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(handler)
    
    
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.
    
    Args:
        name: Name of the module requesting the logger.
        
    Returns:
        Configured logger instance.
    """
    return logging.getLogger(name)