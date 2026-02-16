"""
Gestión de documentos en GLPI.
"""

import json
import logging
from typing import Optional, IO

from .session import SessionManager
from ..exceptions import GLPIError

logger = logging.getLogger(__name__)


class DocumentManager(SessionManager):
    """Maneja las operaciones con documentos en GLPI."""

    def upload_document(
        self, file: IO, name: str = None, file_name: str = None
    ) -> dict:
        """Sube un documento a GLPI."""
        manifest = json.dumps({"input": {"name": name, "_filename": [file_name]}})

        url = self._get_method_url("Document/")
        headers = self._header_dict({"Session-Token": self.session_token})
        if self._BaseHTTPHandler__session is None:
            import requests
            self._BaseHTTPHandler__session = requests.Session()
        if file_name is None:
            file_name = file.name
        del headers["Content-Type"]
        r = self._BaseHTTPHandler__session.post(
            url,
            headers=headers,
            verify=self.verify_tls,
            files={"filename[0]": (file_name, file)},
            data={"uploadManifest": manifest},
        )
        r.raise_for_status()
        return r.json()

    def download_document(self, id_: int) -> bytes:
        """Retorna un Document identificado por id como bytes."""
        response = self._do_method(
            "get",
            f"Document/{id_}",
            headers={"Accept": "application/octet-stream"},
            on_error_raise=False,
        )
        return response.content

    def download_user_profile_picture(self, id_: int) -> bytes:
        """Retorna la foto de perfil de un User identificado por id como bytes."""
        response = self._do_method(
            "get",
            f"User/{id_}/Picture",
            on_error_raise=False,
        )
        if response.status_code == 204:
            raise GLPIError("User doesn't have a profile picture")
        return response.content