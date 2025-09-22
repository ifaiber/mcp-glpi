import mcp.types as types

tools = [
    types.Tool(
        name="echo",
        description="Devuelve el texto que se le proporciona (útil para testing)",
        inputSchema={
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "El mensaje a devolver"
                }
            },
            "required": ["message"]
        }
    ),
    types.Tool(
        name="glpi_status",
        description="Muestra el estado de la configuración GLPI",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": []
        }
    )
]