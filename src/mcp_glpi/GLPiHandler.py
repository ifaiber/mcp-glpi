import mcp.types as types
from common.config import get_config
import logging
import glpi.session

logger = logging.getLogger(__name__)

class CommandHandler:
    def __init__(self, command: str, arguments: dict = None):
        self.command = command
        self.arguments = arguments or {}
        self.config = get_config()

    def execute(self):
        if (self.command == "echo"):
            # Obtener el mensaje de los argumentos
            message = self.arguments.get("message", "No message provided")
            return [types.TextContent(type="text", text=f"Echo: {message}")]
        elif (self.command == "validate_session"):
            return self.validate_session()
        else:
            return [types.T(type="text", text=f"Herramienta desconocida: {self.command}")]
        
    def validate_session(self):
        session_info = glpi.session.get_full_session()
        if session_info:
            return [types.TextContent(type="text", text=str(session_info))]
        else:
            return [types.TextContent(type="text", text="Sesión no válida")]
