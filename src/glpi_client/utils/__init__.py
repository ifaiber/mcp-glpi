"""
Utilidades y helpers para GLPI Wrapper.
"""

from .decorators import retry_on_failure
from .helpers import add_criteria_to_parameters

__all__ = ['retry_on_failure', 'add_criteria_to_parameters']