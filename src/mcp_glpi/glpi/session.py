"""Helpers for GLPI session inspection."""

from glpi_client import RequestHandler

from ..common.config import get_config


def _open_handler():
    config = get_config()
    return RequestHandler(config.url, config.app_token, config.user_token, False)


def get_full_session() -> str:
    """Return a readable summary of the active GLPI session."""

    with _open_handler() as handler:
        session = handler.get_full_session()
        session_id = getattr(handler, "session_token", "") or "N/A"
        session_line = (
            f"ID de Sesion: {session_id[:20]}..."
            if session_id != "N/A"
            else "ID de Sesion: N/A"
        )
        lines = [
            "SESION GLPI",
            session_line,
            "",
            "Informacion del usuario:",
            f"- Usuario: {session.get('glpiname') or 'N/A'}",
            f"- Nombre: {session.get('glpifirstname') or 'N/A'}",
            f"- Apellido: {session.get('glpirealname') or 'N/A'}",
            f"- Entidad: {session.get('glpiactive_entity_name') or 'N/A'}",
        ]
        return "\n".join(lines)
