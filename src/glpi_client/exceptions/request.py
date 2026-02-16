"""
Excepciones relacionadas con requests HTTP.
"""

import requests
from .base import GLPIError


class GLPIRequestError(GLPIError):
    """Error en request HTTP a la API de GLPI.

    Se produce cuando la API devuelve un error HTTP o cuando
    la respuesta no es la esperada.

    Attributes
    ----------
    error_code: int
        El código de respuesta HTTP
    error_message: str
        El mensaje de error devuelto por la API (puede estar vacío)
    request_headers: dict
        Headers del request
    payload: str | bytes
        Payload del request
    url: str
        La URL final de respuesta
    method: str
        El método HTTP del request
    response: requests.Response
        El objeto response completo para debugging adicional
    """

    def __init__(self, response: requests.Response, *args):
        """Inicializar GLPIRequestError con información del response.
        
        Parameters
        ----------
        response : requests.Response
            El objeto response que falló
        *args
            Argumentos adicionales para la excepción
        """
        self.error_code = response.status_code
        self.error_message = response.text
        self.request_headers = response.request.headers
        self.payload = response.request.body
        self.url = response.url
        self.method = response.request.method
        self.response = response
        self.args = args

    def __repr__(self):
        """Representación corta del error."""
        url = ".../" + self.url.split("/")[-1] if "/" in self.url else self.url
        msg = f"GLPIRequestError({url=}, method={self.method}, code={self.error_code})="
        error = self.error_message[: (80 - len(msg))]
        return msg + error

    def __str__(self):
        """Representación completa del error."""
        url = ".../" + self.url.split("/")[-1] if "/" in self.url else self.url
        msg = f"GLPIRequestError({url=}, method={self.method}, code={self.error_code})=\n"
        error = self.error_message
        return msg + error