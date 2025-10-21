"""
Better Paperless - Automated Paperless-ngx with LLM Integration

A comprehensive document automation system that leverages Large Language Models
to automatically process, tag, and organize documents in Paperless-ngx.
"""

__version__ = "1.0.0"
__author__ = "Better Paperless Contributors"
__license__ = "MIT"

from .core.config import Config
from .core.logger import get_logger

__all__ = ["Config", "get_logger", "__version__"]