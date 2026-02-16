"""
Clase base para el manejo de requests HTTP.
"""

import inspect
import json
import logging
import time
from typing import Dict, Optional, Any, List, Tuple, Union

import requests

from ..exceptions import GLPIError, GLPIRequestError
from ..models import ResponseRange

logger = logging.getLogger(__name__)


class BaseHTTPHandler:
    """Clase base que maneja las operaciones HTTP básicas con GLPI.
    
    Esta clase proporciona la funcionalidad fundamental para hacer requests
    HTTP a la API de GLPI, incluyendo manejo de sesiones, headers, y errores.
    """

    def __init__(
        self,
        host_url: str,
        app_token: str,
        user_api_token: str,
        verify_tls: bool = True,
    ):
        """Inicializar el handler HTTP.
        
        Parameters
        ----------
        host_url : str
            URL del servidor GLPI
        app_token : str
            Token de aplicación
        user_api_token : str
            Token de usuario API  
        verify_tls : bool, default True
            Si verificar certificados TLS
        """
        # Validación de parámetros
        if not host_url or not isinstance(host_url, str):
            raise ValueError("host_url must be a non-empty string")
        if not app_token or not isinstance(app_token, str):
            raise ValueError("app_token must be a non-empty string")
        if not user_api_token or not isinstance(user_api_token, str):
            raise ValueError("user_api_token must be a non-empty string")
        
        # Normalizar URL
        self.host_url = host_url.rstrip('/')
        self.app_token = app_token.strip()
        self.user_api_token = user_api_token.strip()
        self.__session_token = None
        self.verify_tls = verify_tls
        self.__session = None
        self.__response_header = None

    @property
    def session_token(self) -> str:
        """Retorna el token de sesión actual.

        Returns
        -------
        str
            Token de sesión para la conexión actual a la API
            
        Raises
        ------
        GLPIError
            Si el handler no ha sido iniciado
        """
        if self.__session_token is None:
            raise GLPIError(
                "Request handler was not initiated! Please call init_session"
                " if you want to start a new session."
            )
        return self.__session_token

    @property
    def response_range(self) -> ResponseRange:
        """Retorna el ResponseRange de la última llamada a la API.

        Returns
        -------
        ResponseRange
            Información de rango de la respuesta anterior
            
        Raises
        ------
        GLPIError
            Si no se ha hecho ningún request o no hay información de rango
        """
        if self.__response_header is None:
            raise GLPIError("No request made")
        elif (
            "Content-Range" not in self.__response_header
            or "Accept-Range" not in self.__response_header
        ):
            raise GLPIError("The previous request did not return a range")
        else:
            import re
            content_range = self.__response_header["Content-Range"]
            match = re.match(
                r"(?P<start>\d+)-(?P<end>\d+)/(?P<count>\d+)", content_range
            )
            s = self.__response_header["Accept-Range"].strip().split()[1]
            accept_range = int(s)
            return ResponseRange(
                int(match.group("start")),
                int(match.group("end")),
                int(match.group("count")),
                accept_range,
            )

    def _get_method_url(self, request_type: str) -> str:
        """Construye la URL completa para un endpoint."""
        return f"{self.host_url}/apirest.php/{request_type}"

    def _header_dict(self, extra: Dict[str, str]) -> Dict[str, str]:
        """Construye el diccionario de headers base."""
        d = {
            "Content-Type": "application/json",
            "App-Token": self.app_token,
        }
        d.update(extra)
        return d

    def _do_get(
        self,
        action: str,
        header: Dict[str, str],
        parameters: Union[Dict[str, Any], List[Tuple[str, Any]]] = None,
        data: Union[Dict[str, Any], List[Tuple[str, Any]]] = None,
    ) -> requests.Response:
        """Ejecuta un request GET."""
        url = self._get_method_url(action)
        headers = self._header_dict(header)
        logger.debug(f"Calling GET method {action} on {url}")
        logger.debug(f"Headers: {headers}")
        logger.debug(f"Parameters: {parameters}")
        
        if self.__session is None:
            self.__session = requests.Session()
        
        start_time = time.time()
        try:
            response = self.__session.get(
                url, headers=headers, verify=self.verify_tls, params=parameters, data=data
            )
            duration = time.time() - start_time
            logger.debug(f"Request completed in {duration:.2f}s with status {response.status_code}")
            
            self.__response_header = response.headers
            if response.status_code >= 400:
                logger.error(f"Request failed with status {response.status_code}: {response.text}")
                raise GLPIRequestError(response)
            return response
        except requests.RequestException as e:
            duration = time.time() - start_time
            logger.error(f"Request failed after {duration:.2f}s: {e}")
            raise

    def _do_method(
        self,
        method: str,
        api_method_url: str,
        data: Union[Dict[str, Any], List[Tuple[str, Any]]] = None,
        headers: Dict[str, str] = None,
        files=None,
        on_error_raise=True,
    ) -> requests.Response:
        """Ejecuta un request HTTP genérico."""
        if headers is None:
            headers = {}
        headers["Session-Token"] = self.session_token
        url = self._get_method_url(api_method_url)
        headers = self._header_dict(headers)
        if self.__session is None:
            self.__session = requests.Session()
        logger.debug(
            f"Calling method {method} on {api_method_url} with {data=} and {headers=}"
        )
        response = getattr(self.__session, method)(
            url, headers=headers, verify=self.verify_tls, json=data, files=files
        )
        if on_error_raise:
            if response.status_code >= 400:
                raise GLPIRequestError(response)
        return response

    def _get_json(
        self,
        method: str,
        parameters: Union[Dict[str, Any], List[Tuple[str, Any]]] = None,
        data: Union[Dict[str, Any], List[Tuple[str, Any]]] = None,
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Ejecuta un request y retorna la respuesta como JSON."""
        response = self._do_get(
            method, {"Session-Token": self.session_token}, parameters, data
        )
        try:
            return response.json()
        except json.JSONDecodeError:
            if len(response.text.strip()) == 0:
                message = "GLPI produced a blank response."
            else:
                message = f"Expected a JSON got a {response.text}"
            raise GLPIRequestError(response, message)

    @staticmethod
    def _keys_to_int(dict_: Dict):
        """Convierte claves string numéricas a int."""
        for k, v in list(dict_.items()):
            try:
                i = int(k)
                del dict_[k]
                dict_[i] = v
            except ValueError:
                pass

    def _get_request_parameters(self, rename: Dict[str, str] = None):
        """Construye parámetros de request desde los argumentos del método llamador."""
        if rename is None:
            rename = {}
        currentframe = inspect.currentframe()
        try:
            frame = inspect.getouterframes(currentframe)[1]
            try:
                method = getattr(self, frame.function)
                sig = inspect.signature(method)
                request_parameters = []
                for parameter in sig.parameters.values():
                    parameter_name = parameter.name
                    parameter_value = frame.frame.f_locals[parameter_name]
                    if parameter_name in rename:
                        parameter_name = rename[parameter_name]
                    if (
                        parameter.default is not inspect.Parameter.empty
                        and parameter_value != parameter.default
                    ):
                        if (
                            type(parameter_value) == list
                            or type(parameter_value) == tuple
                        ):
                            for item in parameter_value:
                                request_parameters.append((parameter_name + "[]", item))
                        else:
                            request_parameters.append((parameter_name, parameter_value))
                return request_parameters
            finally:
                del frame
        finally:
            del currentframe