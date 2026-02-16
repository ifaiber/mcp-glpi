"""
Core functionality for GLPI Wrapper.
"""

from .client import RequestHandler
from .base import BaseHTTPHandler
from .session import SessionManager
from .items import ItemManager
from .search import SearchManager
from .documents import DocumentManager

__all__ = [
    'RequestHandler',
    'BaseHTTPHandler',
    'SessionManager', 
    'ItemManager',
    'SearchManager',
    'DocumentManager'
]