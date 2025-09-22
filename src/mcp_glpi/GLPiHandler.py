import mcp.types as types
from .config import get_config
import logging

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
        elif (self.command == "glpi_status"):
            status_info = (
                f"GLPI URL: {self.config.url}\n"
                f"App Token: {'✅ Configurado' if self.config.app_token else '❌ No configurado'}\n"
                f"User Token: {'✅ Configurado' if self.config.user_token else '❌ No configurado'}\n"
                f"Server: {self.config.server_name} v{self.config.server_version}\n"
                f"Debug: {'Activo' if self.config.debug_mode else 'Inactivo'}"
            )
            return [types.TextContent(type="text", text=status_info)]
        else:
            return [types.TextContent(type="text", text=f"Herramienta desconocida: {self.command}")]