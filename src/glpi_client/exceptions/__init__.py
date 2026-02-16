"""
Excepciones personalizadas para GLPI Wrapper.
"""

from .base import GLPIError
from .request import GLPIRequestError

__all__ = ['GLPIError', 'GLPIRequestError']