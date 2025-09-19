import mcp.types as types

class CommandHandler:
    def __init__(self, command: str):
        self.command = command

    def execute(self):
        if (self.command == "echo"):
            return [types.TextContent(type="text", text=f"Echo: {self.command}")]
        else:
            return [types.TextContent(type="text", text=f"Herramienta desconocida: {self.command}")]