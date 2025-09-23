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

_creation_properties = {
    "name": {
        "type": "string",
        "description": "Nombre del elemento a crear",
    },
    "content": {
        "type": "string",
        "description": "Descripcion o contenido principal",
    },
    "status": {
        "type": ["integer", "string", "null"],
        "description": "Codigo o etiqueta del estado",
    },
    "impact": {
        "type": ["integer", "string", "null"],
        "description": "Codigo o etiqueta del impacto",
    },
    "priority": {
        "type": ["integer", "string", "null"],
        "description": "Codigo o etiqueta de la prioridad",
    },
    "urgency": {
        "type": ["integer", "string", "null"],
        "description": "Codigo o etiqueta de la urgencia",
    },
    "category_id": {
        "type": ["integer", "null"],
        "minimum": 0,
        "description": "Identificador de la categoria (itilcategories_id)",
    },
    "entity_id": {
        "type": ["integer", "null"],
        "minimum": 0,
        "description": "Identificador de la entidad (entities_id)",
    },
    "additional": {
        "type": "object",
        "additionalProperties": True,
        "description": "Campos adicionales que se enviaran tal cual a la API",
    },
}

_comment_base_properties = {
    "content": {
        "type": "string",
        "description": "Contenido del comentario o seguimiento",
    },
    "is_private": {
        "type": ["boolean", "string", "integer", "null"],
        "description": "Marca el comentario como privado",
    },
    "additional": {
        "type": "object",
        "additionalProperties": True,
        "description": "Campos adicionales para el seguimiento",
    },
}

_solution_base_properties = {
    "content": {
        "type": "string",
        "description": "Descripcion de la solucion",
    },
    "solution_type_id": {
        "type": ["integer", "string", "null"],
        "description": "Identificador del tipo de solucion (solutiontypes_id)",
    },
    "additional": {
        "type": "object",
        "additionalProperties": True,
        "description": "Campos adicionales para la solucion",
    },
}


def _listing_schema(description: str) -> dict:
    return {
        "type": "object",
        "properties": copy.deepcopy(_listing_properties),
        "required": [],
        "description": description,
    }


def _creation_schema(description: str) -> dict:
    schema = {
        "type": "object",
        "properties": copy.deepcopy(_creation_properties),
        "required": ["name"],
        "description": description,
    }
    return schema


def _comment_schema(item_field: str, item_label: str) -> dict:
    properties = {
        item_field: {
            "type": ["integer", "string"],
            "description": f"Identificador del {item_label}",
        }
    }
    properties.update(copy.deepcopy(_comment_base_properties))
    properties.setdefault("is_private", {}).setdefault(
        "description", "Marca el comentario como privado"
    )
    return {
        "type": "object",
        "properties": properties,
        "required": [item_field, "content"],
    }


def _solution_schema(item_field: str, item_label: str) -> dict:
    properties = {
        item_field: {
            "type": ["integer", "string"],
            "description": f"Identificador del {item_label}",
        }
    }
    properties.update(copy.deepcopy(_solution_base_properties))
    return {
        "type": "object",
        "properties": properties,
        "required": [item_field, "content"],
    }


def _actor_schema(actor_id_field: str, actor_label: str) -> dict:
    return {
        "type": "object",
        "properties": {
            actor_id_field: {
                "type": ["integer", "string"],
                "description": f"ID del {actor_label}",
            },
            "type": {
                "type": ["integer", "string", "null"],
                "description": "Tipo de rol (1 solicitante, 2 asignado, 3 observador)",
            },
            "use_notification": {
                "type": ["boolean", "string", "integer", "null"],
                "description": "Si debe enviar notificaciones",
            },
            "is_dynamic": {
                "type": ["boolean", "string", "integer", "null"],
                "description": "Marca el actor como dinamico",
            },
            "alternative_email": {
                "type": ["string", "null"],
                "description": "Correo alternativo para el actor",
            },
        },
        "required": [actor_id_field],
        "additionalProperties": True,
    }


def _actors_property(actor_schema: dict, label: str) -> dict:
    return {
        "description": label,
        "anyOf": [
            {"type": "array", "items": actor_schema},
            actor_schema,
        ],
    }


def _assignment_schema(
    item_field: str,
    item_label: str,
    actors_key: str,
    actor_schema: dict,
    description: str,
) -> dict:
    return {
        "type": "object",
        "properties": {
            item_field: {
                "type": ["integer", "string"],
                "description": f"Identificador del {item_label}",
            },
            actors_key: _actors_property(actor_schema, f"Listado de {actors_key} a asignar"),
        },
        "required": [item_field, actors_key],
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
    types.Tool(
        name="create_ticket",
        description="Crea un ticket en GLPI usando glpi_client",
        inputSchema=_creation_schema(
            "Parametros para crear un ticket (los campos adicionales van en 'additional')",
        ),
    ),
    types.Tool(
        name="create_change",
        description="Crea un cambio en GLPI usando glpi_client",
        inputSchema=_creation_schema(
            "Parametros para crear un cambio (los campos adicionales van en 'additional')",
        ),
    ),
    types.Tool(
        name="add_ticket_comment",
        description="Agrega un comentario (seguimiento) a un ticket",
        inputSchema=_comment_schema("ticket_id", "ticket"),
    ),
    types.Tool(
        name="add_ticket_solution",
        description="Registra una solucion para un ticket",
        inputSchema=_solution_schema("ticket_id", "ticket"),
    ),
    types.Tool(
        name="assign_ticket_users",
        description="Asigna usuarios a un ticket",
        inputSchema=_assignment_schema(
            "ticket_id",
            "ticket",
            "users",
            _actor_schema("users_id", "usuario"),
            "Parametros para asignar usuarios a un ticket",
        ),
    ),
    types.Tool(
        name="assign_ticket_groups",
        description="Asigna grupos a un ticket",
        inputSchema=_assignment_schema(
            "ticket_id",
            "ticket",
            "groups",
            _actor_schema("groups_id", "grupo"),
            "Parametros para asignar grupos a un ticket",
        ),
    ),
    types.Tool(
        name="add_change_comment",
        description="Agrega un comentario (seguimiento) a un cambio",
        inputSchema=_comment_schema("change_id", "cambio"),
    ),
    types.Tool(
        name="add_change_solution",
        description="Registra una solucion para un cambio",
        inputSchema=_solution_schema("change_id", "cambio"),
    ),
    types.Tool(
        name="assign_change_users",
        description="Asigna usuarios a un cambio",
        inputSchema=_assignment_schema(
            "change_id",
            "cambio",
            "users",
            _actor_schema("users_id", "usuario"),
            "Parametros para asignar usuarios a un cambio",
        ),
    ),
    types.Tool(
        name="assign_change_groups",
        description="Asigna grupos a un cambio",
        inputSchema=_assignment_schema(
            "change_id",
            "cambio",
            "groups",
            _actor_schema("groups_id", "grupo"),
            "Parametros para asignar grupos a un cambio",
        ),
    ),
]
