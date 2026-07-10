"""Session read operations."""

from typing import Any, Dict

from .common import open_handler


def get_full_session_data() -> Dict[str, Any]:
    with open_handler() as handler:
        session = handler.get_full_session()
        session_id = getattr(handler, "session_token", "") or None
        return {
            "session_token": session_id,
            "user": {
                "username": session.get("glpiname"),
                "first_name": session.get("glpifirstname"),
                "last_name": session.get("glpirealname"),
                "active_entity": session.get("glpiactive_entity_name"),
            },
            "session": session,
        }


def get_full_session() -> str:
    session_data = get_full_session_data()
    session_id = session_data.get("session_token") or "N/A"
    user = session_data.get("user", {})
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
        f"- Usuario: {user.get('username') or 'N/A'}",
        f"- Nombre: {user.get('first_name') or 'N/A'}",
        f"- Apellido: {user.get('last_name') or 'N/A'}",
        f"- Entidad: {user.get('active_entity') or 'N/A'}",
    ]
    return "\n".join(lines)
