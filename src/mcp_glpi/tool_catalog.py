"""Single source of truth for MCP tool metadata."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Dict, List

import mcp.types as types


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler_name: str


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
        "description": "Formato de la respuesta; por defecto 'dict' para JSON",
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

_pr_links_property = {
    "description": "URL(s) de Pull Request o cambios relacionados; acepta string o lista",
    "anyOf": [
        {"type": "string"},
        {"type": "array", "items": {"type": "string"}},
        {"type": "null"},
    ],
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

_def_bool = ["boolean", "string", "integer", "null"]


def _listing_schema(description: str) -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": copy.deepcopy(_listing_properties),
        "required": [],
        "description": description,
    }


def _creation_schema(description: str) -> Dict[str, Any]:
    properties = copy.deepcopy(_creation_properties)
    properties["pr_links"] = copy.deepcopy(_pr_links_property)
    return {
        "type": "object",
        "properties": properties,
        "required": ["name"],
        "description": description,
    }


def _comment_schema(item_field: str, item_label: str) -> Dict[str, Any]:
    properties = {
        item_field: {
            "type": ["integer", "string"],
            "description": f"Identificador del {item_label}",
        }
    }
    properties.update(copy.deepcopy(_comment_base_properties))
    return {
        "type": "object",
        "properties": properties,
        "required": [item_field, "content"],
    }


def _solution_schema(item_field: str, item_label: str) -> Dict[str, Any]:
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


def _actor_schema(actor_id_field: str, actor_label: str) -> Dict[str, Any]:
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


def _actors_property(actor_schema: Dict[str, Any], label: str) -> Dict[str, Any]:
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
    actor_schema: Dict[str, Any],
    description: str,
) -> Dict[str, Any]:
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


def _link_schema(
    primary_field: str,
    primary_label: str,
    secondary_field: str,
    secondary_label: str,
) -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            primary_field: {
                "type": ["integer", "string"],
                "description": f"Identificador del {primary_label}",
            },
            secondary_field: {
                "type": ["integer", "string"],
                "description": f"Identificador del {secondary_label}",
            },
            "additional": {
                "type": "object",
                "additionalProperties": True,
                "description": "Campos adicionales que se enviaran tal cual",
            },
        },
        "required": [primary_field, secondary_field],
    }


def _unlink_schema(item_field: str, item_label: str) -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            item_field: {
                "type": ["integer", "string"],
                "description": f"Identificador del {item_label}",
            },
            "link_id": {
                "type": ["integer", "string"],
                "description": "Identificador del enlace (Change_Ticket)",
            },
            "purge": {
                "type": _def_bool,
                "description": "Forzar purga del enlace",
            },
            "keep_history": {
                "type": _def_bool,
                "description": "Mantener historial de GLPI",
            },
        },
        "required": [item_field, "link_id"],
    }


def _update_schema(item_field: str, item_label: str) -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            item_field: {
                "type": ["integer", "string"],
                "description": f"Identificador del {item_label}",
            },
            "fields": {
                "type": "object",
                "additionalProperties": True,
                "description": "Campos a actualizar",
            },
            "pr_links": copy.deepcopy(_pr_links_property),
        },
        "required": [item_field, "fields"],
    }


TOOL_SPECS: List[ToolSpec] = [
    ToolSpec(
        name="echo",
        description="Devuelve el texto que se le proporciona (util para pruebas)",
        input_schema={
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Mensaje a devolver",
                }
            },
            "required": ["message"],
        },
        handler_name="_echo",
    ),
    ToolSpec(
        name="validate_session",
        description="Muestra informacion sobre el estado de la sesion con GLPI",
        input_schema={"type": "object", "properties": {}, "required": []},
        handler_name="validate_session",
    ),
    ToolSpec(
        name="my_profiles",
        description="Lista los perfiles del usuario logueado y las entidades asociadas",
        input_schema={"type": "object", "properties": {}, "required": []},
        handler_name="_my_profiles",
    ),
    ToolSpec(
        name="list_tickets",
        description="Lista tickets de GLPI con opciones de filtrado basicas; responde JSON por defecto",
        input_schema=_listing_schema("Parametros para listar tickets usando glpi_client"),
        handler_name="_list_tickets",
    ),
    ToolSpec(
        name="list_changes",
        description="Lista cambios de GLPI con opciones de filtrado basicas; responde JSON por defecto",
        input_schema=_listing_schema("Parametros para listar cambios usando glpi_client"),
        handler_name="_list_changes",
    ),
    ToolSpec(
        name="create_ticket",
        description="Crea un ticket en GLPI usando glpi_client",
        input_schema=_creation_schema(
            "Parametros para crear un ticket (los campos adicionales van en 'additional')"
        ),
        handler_name="_create_ticket",
    ),
    ToolSpec(
        name="create_change",
        description="Crea un cambio en GLPI usando glpi_client",
        input_schema=_creation_schema(
            "Parametros para crear un cambio (los campos adicionales van en 'additional')"
        ),
        handler_name="_create_change",
    ),
    ToolSpec(
        name="add_ticket_comment",
        description="Agrega un comentario (seguimiento) a un ticket",
        input_schema=_comment_schema("ticket_id", "ticket"),
        handler_name="_add_ticket_comment",
    ),
    ToolSpec(
        name="add_ticket_solution",
        description="Registra una solucion para un ticket",
        input_schema=_solution_schema("ticket_id", "ticket"),
        handler_name="_add_ticket_solution",
    ),
    ToolSpec(
        name="assign_ticket_users",
        description="Asigna usuarios a un ticket",
        input_schema=_assignment_schema(
            "ticket_id",
            "ticket",
            "users",
            _actor_schema("users_id", "usuario"),
            "Parametros para asignar usuarios a un ticket",
        ),
        handler_name="_assign_ticket_users",
    ),
    ToolSpec(
        name="assign_ticket_groups",
        description="Asigna grupos a un ticket",
        input_schema=_assignment_schema(
            "ticket_id",
            "ticket",
            "groups",
            _actor_schema("groups_id", "grupo"),
            "Parametros para asignar grupos a un ticket",
        ),
        handler_name="_assign_ticket_groups",
    ),
    ToolSpec(
        name="add_change_comment",
        description="Agrega un comentario (seguimiento) a un cambio",
        input_schema=_comment_schema("change_id", "cambio"),
        handler_name="_add_change_comment",
    ),
    ToolSpec(
        name="add_change_solution",
        description="Registra una solucion para un cambio",
        input_schema=_solution_schema("change_id", "cambio"),
        handler_name="_add_change_solution",
    ),
    ToolSpec(
        name="assign_change_users",
        description="Asigna usuarios a un cambio",
        input_schema=_assignment_schema(
            "change_id",
            "cambio",
            "users",
            _actor_schema("users_id", "usuario"),
            "Parametros para asignar usuarios a un cambio",
        ),
        handler_name="_assign_change_users",
    ),
    ToolSpec(
        name="assign_change_groups",
        description="Asigna grupos a un cambio",
        input_schema=_assignment_schema(
            "change_id",
            "cambio",
            "groups",
            _actor_schema("groups_id", "grupo"),
            "Parametros para asignar grupos a un cambio",
        ),
        handler_name="_assign_change_groups",
    ),
    ToolSpec(
        name="link_change_to_ticket",
        description="Vincula un ticket existente a un cambio",
        input_schema=_link_schema("change_id", "cambio", "ticket_id", "ticket"),
        handler_name="_link_change_to_ticket",
    ),
    ToolSpec(
        name="link_ticket_to_change",
        description="Vincula un cambio existente a un ticket",
        input_schema=_link_schema("ticket_id", "ticket", "change_id", "cambio"),
        handler_name="_link_ticket_to_change",
    ),
    ToolSpec(
        name="unlink_change_ticket",
        description="Elimina la relacion Change_Ticket desde un cambio",
        input_schema=_unlink_schema("change_id", "cambio"),
        handler_name="_unlink_change_ticket",
    ),
    ToolSpec(
        name="unlink_ticket_change",
        description="Elimina la relacion Change_Ticket desde un ticket",
        input_schema=_unlink_schema("ticket_id", "ticket"),
        handler_name="_unlink_ticket_change",
    ),
    ToolSpec(
        name="update_change",
        description="Actualiza campos de un cambio",
        input_schema=_update_schema("change_id", "cambio"),
        handler_name="_update_change",
    ),
    ToolSpec(
        name="update_ticket",
        description="Actualiza campos de un ticket",
        input_schema=_update_schema("ticket_id", "ticket"),
        handler_name="_update_ticket",
    ),
]


def build_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name=spec.name,
            description=spec.description,
            inputSchema=copy.deepcopy(spec.input_schema),
        )
        for spec in TOOL_SPECS
    ]
