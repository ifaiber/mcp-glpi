import mcp.types as types


tools = [
    types.Tool(
        name="echo",
        description="Devuelve el texto que se le proporciona (util para pruebas)",
        inputSchema={
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Mensaje a devolver",
                }
            },
            "required": ["message"],
        },
    ),
    types.Tool(
        name="validate_session",
        description="Muestra informacion sobre el estado de la sesion con GLPI",
        inputSchema={
            "type": "object",
            "properties": {},
            "required": [],
        },
    ),
    types.Tool(
        name="list_tickets",
        description="Lista tickets de GLPI con opciones de filtrado basicas",
        inputSchema={
            "type": "object",
            "properties": {
                "limit": {
                    "type": ["integer", "null"],
                    "minimum": 0,
                    "description": "Cantidad maxima de tickets a recuperar",
                },
                "offset": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "Indice desde el cual comenzar la busqueda",
                },
                "sort_by": {
                    "type": "string",
                    "description": "Campo de ordenamiento (por defecto date_mod)",
                },
                "order": {
                    "type": "string",
                    "enum": ["ASC", "DESC"],
                    "description": "Direccion del ordenamiento",
                },
                "output": {
                    "type": "string",
                    "enum": ["table", "dict", "raw"],
                    "description": "Formato de la respuesta",
                },
                "fields": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Campos a incluir en la respuesta",
                },
                "filters": {
                    "type": "object",
                    "additionalProperties": {"type": "string"},
                    "description": "Filtros adicionales para la busqueda",
                },
                "expand_dropdowns": {
                    "type": "boolean",
                    "description": "Expandir valores de dropdown en la respuesta",
                },
                "include_deleted": {
                    "type": "boolean",
                    "description": "Incluir tickets eliminados",
                },
            },
            "required": [],
        },
    ),
]
