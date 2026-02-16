"""
GLPI Wrapper - A Python wrapper for the GLPI REST API.

This library provides a clean, Pythonic interface to interact with GLPI
(IT Asset Management) systems through their REST API.

Basic usage:
    >>> from glpi_client import RequestHandler
    >>> with RequestHandler('http://glpi', 'app_token', 'user_token') as client:
    ...     tickets = client.get_all_tickets()
    ...     change = client.create_change("Server upgrade", "Migrating to new OS")
"""

__version__ = "2.0.0"
__author__ = "GLPI Wrapper Contributors"
__license__ = "MIT"

# Import main classes for easy access
from .core import RequestHandler
from .exceptions import GLPIError, GLPIRequestError
from .models import SortOrder, ResponseRange

# Make these available at package level
__all__ = [
    'RequestHandler',
    'GLPIError', 
    'GLPIRequestError',
    'SortOrder',
    'ResponseRange'
]