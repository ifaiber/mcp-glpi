"""
Enumeraciones para GLPI Wrapper.
"""

from enum import Enum


class SortOrder(Enum):
    """Enum útil para ordenar consultas.

    Attributes
    ----------
    Ascending : str
        Orden ascendente
    Descending : str
        Orden descendente
    """

    Ascending = "ASC"
    Descending = "DESC"

    def __str__(self):
        """Retorna el valor string del enum."""
        return self.value