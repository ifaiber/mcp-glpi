"""
RequestHandler principal que combina toda la funcionalidad.
"""

from .search import SearchManager
from .documents import DocumentManager


class RequestHandler(SearchManager, DocumentManager):
    """RequestHandler que encapsula la API de GLPI en una clase conveniente.

    Esta clase combina toda la funcionalidad de sesiones, ítems, búsquedas,
    y documentos en una interfaz unificada.

    Parameters
    ----------
    host_url : str
        La URL a la instancia de GLPI.
    app_token : str
        El token de aplicación.
    user_api_token : str
        El token de API del usuario.
    verify_tls : bool, default True
        Si tu servidor GLPI está usando TLS con un certificado malo,
        necesitarás establecer esto en False.

    Examples
    --------
    >>> with RequestHandler('localhost', '123456', '654321') as handler:
    ...     profiles = handler.get_my_profiles()
    ...     change = handler.create_change("Mi cambio", "Descripción")
    ...     tickets = handler.search_by_name("Ticket", "problema")
    """

    def __init__(
        self,
        host_url: str,
        app_token: str,
        user_api_token: str,
        verify_tls: bool = True,
    ):
        """Crea una nueva instancia de RequestHandler."""
        # Llamar al __init__ de las clases padre
        super().__init__(host_url, app_token, user_api_token, verify_tls)