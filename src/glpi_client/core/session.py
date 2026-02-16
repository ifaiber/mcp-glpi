"""
Gestión de sesiones GLPI.
"""

import logging
from json import JSONDecodeError
from typing import List, Dict, Any, Optional

from .base import BaseHTTPHandler
from ..exceptions import GLPIError, GLPIRequestError
from ..utils import retry_on_failure

logger = logging.getLogger(__name__)


class SessionManager(BaseHTTPHandler):
    """Maneja las operaciones de sesión con GLPI."""

    @retry_on_failure(max_retries=3, delay=1.0)
    def init_session(self):
        """Solicita un session_token para ser usado por otros métodos."""
        if self._BaseHTTPHandler__session_token is not None:
            raise GLPIError("Session already initialized.")
        auth = f"user_token {self.user_api_token}"
        r = self._do_get("initSession", {"Authorization": auth})
        self._BaseHTTPHandler__session_token = r.json()["session_token"]
        logger.info("Session initiated successfully")

    def kill_session(self, session_id: Optional[str] = None):
        """Destruye una sesión identificada por un session_token."""
        if session_id is None:
            if self._BaseHTTPHandler__session_token is None:
                raise GLPIError(
                    "Request handler was not initiated, nothing to be done."
                )
            else:
                session_id = self._BaseHTTPHandler__session_token
                self._BaseHTTPHandler__session_token = None

        try:
            self._do_get("killSession", {"Session-Token": session_id})
        except GLPIRequestError as err:
            if err.error_code == 401:
                try:
                    message = err.response.json()
                except JSONDecodeError:
                    raise err from None
                if len(message) > 0 and message[0] == "ERROR_SESSION_TOKEN_INVALID":
                    raise GLPIError("Session expired") from err
                else:
                    raise err from None
            else:
                raise
        logger.info("Session was terminated successfully.")

    def __enter__(self):
        """Context manager entry."""
        try:
            self.init_session()
            return self
        except Exception as e:
            logger.error(f"Failed to initialize session: {e}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        try:
            self.kill_session()
        except Exception as e:
            logger.warning(f"Failed to properly close session: {e}")
        
        # No suprimir excepciones del bloque `with`
        return False

    def get_my_profiles(self) -> List[Dict[str, Any]]:
        """Retorna todos los perfiles asociados al usuario actual."""
        return self._get_json("getMyProfiles")["myprofiles"]

    def get_active_profile(self) -> Dict[str, Any]:
        """Retorna el perfil activo actual."""
        return self._get_json("getActiveProfile")["active_profile"]

    def change_active_profile(self, profile_id: int) -> None:
        """Cambia el perfil activo."""
        r = self._do_method(
            "post", 
            "changeActiveProfile", 
            data={"profiles_id": profile_id}, 
            on_error_raise=False
        )
        if r.status_code == 404:
            raise GLPIError("Profile not found")

    def get_my_entities(self, recursive: bool = False) -> List[Dict[str, Any]]:
        """Retorna todas las entidades del usuario actual."""
        return self._get_json(
            "getMyEntities", parameters={"is_recursive": str(recursive).lower()}
        )["myentities"]

    def get_active_entities(self) -> Dict[str, Any]:
        """Retorna las entidades activas del usuario actual."""
        return self._get_json("getActiveEntities")["active_entity"]

    def change_active_entity(self, entity_id: int):
        """Cambia la entidad activa."""
        r = self._do_method(
            "post",
            "changeActiveEntities", 
            data={"entities_id": entity_id}, 
            on_error_raise=False
        )
        if r.status_code == 400:
            raise GLPIError(r.json()[1])

    def get_full_session(self) -> Dict[str, Any]:
        """Retorna la sesión PHP completa."""
        return self._get_json("getFullSession")["session"]

    def get_glpi_config(self) -> Dict[str, Any]:
        """Retorna la configuración de GLPI."""
        return self._get_json("getGlpiConfig")["cfg_glpi"]

    def is_session_active(self) -> bool:
        """Verifica si la sesión está activa."""
        try:
            self.get_active_profile()
            return True
        except (GLPIError, GLPIRequestError):
            return False