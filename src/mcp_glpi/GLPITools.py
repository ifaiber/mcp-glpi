import copy

import mcp.types as types


_listing_properties = {
    "limit": {
        "type": ["integer", "null"],
        "minimum": 0,
        "description": "Cantidad maxima de elementos a recuperar",
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
        "description": "Incluir elementos eliminados",
    },
}


def _listing_schema(description: str) -> dict:
    return {
        "type": "object",
        "properties": copy.deepcopy(_listing_properties),
        "required": [],
        "description": description,
    }


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
        inputSchema=_listing_schema(
            "Parametros para listar tickets usando glpi_client",
        ),
    ),
    types.Tool(
        name="list_changes",
        description="Lista cambios de GLPI con opciones de filtrado basicas",
        inputSchema=_listing_schema(
            "Parametros para listar cambios usando glpi_client",
        ),
    ),
]
