"""
Modelos de respuesta para GLPI Wrapper.
"""

from dataclasses import dataclass


@dataclass
class ResponseRange:
    """Rango de una consulta.

    Algunos métodos de la API producen una respuesta en el header que describe
    el rango de la consulta. Esos datos se recopilan y se encapsulan en este
    tipo de objeto.

    Para obtenerlo usa la propiedad :meth:`~RequestHandler.response_range`
    de :class:`RequestHandler`.

    Attributes
    ----------
    start: int
        La consulta se recuperó comenzando en el número `start`.
    end: int
        La consulta se recuperó sin elementos después del número `end`.
    count: int
        Número de elementos devueltos.
    max: int
        Número máximo posible de elementos para este tipo de elemento.
    """

    start: int
    end: int
    count: int
    max: int

    def __repr__(self):
        """Representación string del rango."""
        return f"{str(self.start)}-{str(self.end)}/{self.count} Max: {self.max}"