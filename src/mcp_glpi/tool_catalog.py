"""Single source of truth for MCP tool metadata."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Dict, List

import mcp.types as types

from .glpi.generic import ITEMTYPE_CATALOG


@dataclass(frozen=True)
class ToolSpec:
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler_name: str


_entity_id_property = {
    "type": ["integer", "string", "null"],
    "minimum": 0,
    "description": (
        "Codigo (id) de la entidad GLPI en la que ejecutar esta operacion. "
        "Si se indica, cambia la entidad activa de la sesion antes de operar "
        "(equivalente a changeActiveEntities); si se omite, se usa la entidad "
        "activa por defecto de la sesion. Use 'entity_list' para obtener "
        "los codigos disponibles. Tambien acepta el *nombre* de la entidad "
        "(texto no numerico): se busca entre las entidades del usuario y se "
        "resuelve automaticamente a su id (ver el recurso "
        "'mcp-glpi://docs/glpi-entity-profile-resolution' para el detalle "
        "del algoritmo y los casos de ambiguedad)."
    ),
}

_profile_id_property = {
    "type": ["integer", "string", "null"],
    "description": (
        "Codigo (id) del perfil GLPI a activar antes de ejecutar esta "
        "operacion (equivalente a changeActiveProfile). El perfil activo "
        "determina los permisos (crear/leer/editar) con los que se ejecuta "
        "la operacion; la entidad activa (ver 'entity_id') solo determina "
        "sobre que registros se opera. Si se omite, se usa el perfil activo "
        "por defecto de la sesion. Use 'profile_list' para ver los perfiles "
        "disponibles y sus entidades asociadas. Si vas a combinar "
        "'profile_id' y 'entity_id' en la misma llamada, el perfil se "
        "cambia primero. Tambien acepta el *nombre* del perfil (texto no "
        "numerico): se resuelve automaticamente a su id, y si no se indico "
        "'entity_id' se selecciona la primera entidad de ese perfil (ver el "
        "recurso 'mcp-glpi://docs/glpi-entity-profile-resolution')."
    ),
}

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
    "entity_id": _entity_id_property,
    "profile_id": _profile_id_property,
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
        "type": ["integer", "string", "null"],
        "minimum": 0,
        "description": (
            "Identificador de la entidad (entities_id) para el objeto creado; "
            "ademas cambia la entidad activa de la sesion antes de crear "
            "(equivalente a changeActiveEntities). Opcional: si se omite, se "
            "usa la entidad activa por defecto de la sesion."
        ),
    },
    "profile_id": _profile_id_property,
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
    "entity_id": _entity_id_property,
    "profile_id": _profile_id_property,
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
    "entity_id": _entity_id_property,
    "profile_id": _profile_id_property,
}

_def_bool = ["boolean", "string", "integer", "null"]


def _listing_schema(description: str) -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": copy.deepcopy(_listing_properties),
        "required": [],
        "description": description,
    }


def _sub_item_listing_schema(item_field: str, item_label: str, description: str) -> Dict[str, Any]:
    properties = {
        item_field: {
            "type": ["integer", "string"],
            "description": f"Identificador del {item_label}",
        },
        "limit": copy.deepcopy(_listing_properties["limit"]),
        "offset": copy.deepcopy(_listing_properties["offset"]),
        "sort_by": copy.deepcopy(_listing_properties["sort_by"]),
        "order": copy.deepcopy(_listing_properties["order"]),
        "output": copy.deepcopy(_listing_properties["output"]),
        "fields": copy.deepcopy(_listing_properties["fields"]),
        "entity_id": _entity_id_property,
        "profile_id": _profile_id_property,
    }
    return {
        "type": "object",
        "properties": properties,
        "required": [item_field],
        "description": description,
    }


_SUPPORTED_ITEMTYPES = sorted(ITEMTYPE_CATALOG.keys())


def _item_type_list_schema() -> Dict[str, Any]:
    return {"type": "object", "properties": {}, "required": []}


def _item_subtype_list_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "itemtype": {
                "type": ["string", "null"],
                "description": (
                    "Filtra los subtypes por este itemtype (uno de "
                    f"{_SUPPORTED_ITEMTYPES}). Si se omite, lista los subtypes "
                    "de todos los itemtypes soportados."
                ),
            },
        },
        "required": [],
        "description": "Lista los subtypes soportados, con una breve descripcion de cada uno",
    }


def _item_list_schema() -> Dict[str, Any]:
    properties = {
        "itemtype": {
            "type": "string",
            "enum": _SUPPORTED_ITEMTYPES,
            "description": "Itemtype de GLPI soportado. Use 'item_type_list' para ver todos.",
        },
    }
    properties.update(copy.deepcopy(_listing_properties))
    return {
        "type": "object",
        "properties": properties,
        "required": ["itemtype"],
        "description": (
            "Acceso generico de solo lectura: lista elementos de un itemtype "
            "soportado (equivalente a GET /{itemtype}). Para obtener un "
            "elemento puntual por id use 'item_get'."
        ),
    }


def _item_get_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "itemtype": {
                "type": "string",
                "enum": _SUPPORTED_ITEMTYPES,
                "description": "Itemtype de GLPI soportado. Use 'item_type_list' para ver todos.",
            },
            "id": {
                "type": ["integer", "string"],
                "minimum": 0,
                "description": "Identificador del elemento a obtener.",
            },
            "fields": copy.deepcopy(_listing_properties["fields"]),
            "expand_dropdowns": copy.deepcopy(_listing_properties["expand_dropdowns"]),
            "entity_id": _entity_id_property,
            "profile_id": _profile_id_property,
        },
        "required": ["itemtype", "id"],
        "description": (
            "Acceso generico de solo lectura a un elemento puntual de un "
            "itemtype soportado (equivalente a GET /{itemtype}/{id}). Para "
            "listar varios use 'item_list'."
        ),
    }


def _item_subitem_list_schema() -> Dict[str, Any]:
    properties = {
        "itemtype": {
            "type": "string",
            "enum": _SUPPORTED_ITEMTYPES,
            "description": "Itemtype del elemento padre. Use 'item_type_list' para ver todos.",
        },
        "id": {
            "type": ["integer", "string"],
            "description": "Identificador del elemento padre.",
        },
        "subtype": {
            "type": "string",
            "description": (
                "Subtype a listar; los validos dependen del itemtype elegido. "
                "Use 'item_subtype_list' con el mismo itemtype para ver los validos."
            ),
        },
        "limit": copy.deepcopy(_listing_properties["limit"]),
        "offset": copy.deepcopy(_listing_properties["offset"]),
        "sort_by": copy.deepcopy(_listing_properties["sort_by"]),
        "order": copy.deepcopy(_listing_properties["order"]),
        "output": copy.deepcopy(_listing_properties["output"]),
        "fields": copy.deepcopy(_listing_properties["fields"]),
        "entity_id": _entity_id_property,
        "profile_id": _profile_id_property,
    }
    return {
        "type": "object",
        "properties": properties,
        "required": ["itemtype", "id", "subtype"],
        "description": (
            "Acceso generico de solo lectura a sub-items de un elemento "
            "(equivalente a GET /{itemtype}/{id}/{subtype}), para itemtype/"
            "subtype soportados."
        ),
    }


def _item_delete_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "itemtype": {
                "type": "string",
                "enum": _SUPPORTED_ITEMTYPES,
                "description": "Itemtype de GLPI soportado. Use 'item_type_list' para ver todos.",
            },
            "id": {
                "type": ["integer", "string"],
                "description": "Identificador del elemento a eliminar.",
            },
            "purge": {
                "type": _def_bool,
                "description": "Forzar purga (borrado definitivo) en lugar de enviar a la papelera",
            },
            "keep_history": {
                "type": _def_bool,
                "description": "Mantener historial de GLPI",
            },
            "entity_id": _entity_id_property,
            "profile_id": _profile_id_property,
        },
        "required": ["itemtype", "id"],
        "description": (
            "Elimina un elemento de un itemtype soportado (equivalente a "
            "DELETE /{itemtype}/{id}), a la papelera o con purga definitiva "
            "si se indica."
        ),
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
            "entity_id": _entity_id_property,
            "profile_id": _profile_id_property,
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
            "entity_id": _entity_id_property,
            "profile_id": _profile_id_property,
        },
        "required": [primary_field, secondary_field],
    }


def _unlink_schema(item_field: str, item_label: str, relation_label: str = "Change_Ticket") -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            item_field: {
                "type": ["integer", "string"],
                "description": f"Identificador del {item_label}",
            },
            "link_id": {
                "type": ["integer", "string"],
                "description": f"Identificador del enlace ({relation_label})",
            },
            "purge": {
                "type": _def_bool,
                "description": "Forzar purga del enlace",
            },
            "keep_history": {
                "type": _def_bool,
                "description": "Mantener historial de GLPI",
            },
            "entity_id": _entity_id_property,
            "profile_id": _profile_id_property,
        },
        "required": [item_field, "link_id"],
    }


def _delete_schema(item_field: str, item_label: str) -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            item_field: {
                "type": ["integer", "string"],
                "description": f"Identificador del {item_label}",
            },
            "purge": {
                "type": _def_bool,
                "description": "Forzar purga (borrado definitivo) en lugar de enviar a la papelera",
            },
            "keep_history": {
                "type": _def_bool,
                "description": "Mantener historial de GLPI",
            },
            "entity_id": _entity_id_property,
            "profile_id": _profile_id_property,
        },
        "required": [item_field],
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
            "entity_id": _entity_id_property,
            "profile_id": _profile_id_property,
        },
        "required": [item_field, "fields"],
    }


def _file_upload_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": (
                    "Ruta local del archivo a subir, en el sistema de archivos "
                    "de la maquina donde corre el servidor MCP."
                ),
            },
            "name": {
                "type": ["string", "null"],
                "description": "Titulo/nombre del documento en GLPI (Document.name).",
            },
            "file_name": {
                "type": ["string", "null"],
                "description": (
                    "Nombre de archivo a registrar en GLPI. Si se omite, se usa "
                    "el nombre base de 'file_path'."
                ),
            },
            "additional": {
                "type": "object",
                "additionalProperties": True,
                "description": "Campos adicionales del Document que se enviaran tal cual (por ejemplo entities_id).",
            },
            "entity_id": _entity_id_property,
            "profile_id": _profile_id_property,
        },
        "required": ["file_path"],
        "description": "Sube un archivo local como Document de GLPI (multipart/form-data).",
    }


def _file_download_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "document_id": {
                "type": ["integer", "string"],
                "description": "Identificador (id) del Document a descargar.",
            },
            "destination_path": {
                "type": "string",
                "description": (
                    "Ruta local de destino donde escribir el archivo, en el "
                    "sistema de archivos de la maquina donde corre el servidor MCP. "
                    "Puede ser la ruta completa del archivo, o una carpeta ya "
                    "existente (en ese caso se usa el nombre de archivo registrado en GLPI)."
                ),
            },
            "entity_id": _entity_id_property,
            "profile_id": _profile_id_property,
        },
        "required": ["document_id", "destination_path"],
        "description": "Descarga un Document de GLPI y lo escribe en una ruta local.",
    }


def _file_link_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "document_id": {
                "type": ["integer", "string"],
                "description": "Identificador (id) del Document a vincular.",
            },
            "item_type": {
                "type": "string",
                "enum": _SUPPORTED_ITEMTYPES,
                "description": "Itemtype al que se vinculara el documento.",
            },
            "item_id": {
                "type": ["integer", "string"],
                "description": "Identificador (id) del elemento al que se vinculara el documento.",
            },
            "additional": {
                "type": "object",
                "additionalProperties": True,
                "description": "Campos adicionales de Document_Item que se enviaran tal cual",
            },
            "entity_id": _entity_id_property,
            "profile_id": _profile_id_property,
        },
        "required": ["document_id", "item_type", "item_id"],
        "description": "Crea la relacion Document_Item entre un documento y un elemento GLPI.",
    }


TOOL_SPECS: List[ToolSpec] = [
    ToolSpec(
        name="session_validate",
        description="Muestra informacion sobre el estado de la sesion con GLPI",
        input_schema={"type": "object", "properties": {}, "required": []},
        handler_name="_session_validate",
    ),
    ToolSpec(
        name="profile_list",
        description="Lista los perfiles del usuario logueado y las entidades asociadas",
        input_schema={"type": "object", "properties": {}, "required": []},
        handler_name="_profile_list",
    ),
    ToolSpec(
        name="entity_list",
        description=(
            "Lista las entidades GLPI disponibles para el usuario logueado "
            "(id, nombre y si es recursiva). Util para obtener el codigo de "
            "entidad a usar con el parametro 'entity_id' de otras herramientas."
        ),
        input_schema={
            "type": "object",
            "properties": {
                "recursive": {
                    "type": ["boolean", "string", "integer", "null"],
                    "description": "Incluir entidades hijas de forma recursiva",
                },
            },
            "required": [],
        },
        handler_name="_entity_list",
    ),
    ToolSpec(
        name="ticket_list",
        description="Lista tickets de GLPI con opciones de filtrado basicas; responde JSON por defecto",
        input_schema=_listing_schema("Parametros para listar tickets usando glpi_client"),
        handler_name="_ticket_list",
    ),
    ToolSpec(
        name="change_list",
        description="Lista cambios de GLPI con opciones de filtrado basicas; responde JSON por defecto",
        input_schema=_listing_schema("Parametros para listar cambios usando glpi_client"),
        handler_name="_change_list",
    ),
    ToolSpec(
        name="ticket_add",
        description="Crea un ticket en GLPI usando glpi_client",
        input_schema=_creation_schema(
            "Parametros para crear un ticket (los campos adicionales van en 'additional')"
        ),
        handler_name="_ticket_add",
    ),
    ToolSpec(
        name="change_add",
        description="Crea un cambio en GLPI usando glpi_client",
        input_schema=_creation_schema(
            "Parametros para crear un cambio (los campos adicionales van en 'additional')"
        ),
        handler_name="_change_add",
    ),
    ToolSpec(
        name="ticket_follow_add",
        description="Agrega un comentario (seguimiento) a un ticket",
        input_schema=_comment_schema("ticket_id", "ticket"),
        handler_name="_ticket_follow_add",
    ),
    ToolSpec(
        name="ticket_follow_list",
        description="Lista los comentarios (seguimientos, ITILFollowup) de un ticket",
        input_schema=_sub_item_listing_schema(
            "ticket_id", "ticket", "Parametros para listar seguimientos de un ticket"
        ),
        handler_name="_ticket_follow_list",
    ),
    ToolSpec(
        name="ticket_solution_add",
        description="Registra una solucion para un ticket",
        input_schema=_solution_schema("ticket_id", "ticket"),
        handler_name="_ticket_solution_add",
    ),
    ToolSpec(
        name="ticket_solution_list",
        description="Lista las soluciones (ITILSolution) de un ticket",
        input_schema=_sub_item_listing_schema(
            "ticket_id", "ticket", "Parametros para listar soluciones de un ticket"
        ),
        handler_name="_ticket_solution_list",
    ),
    ToolSpec(
        name="ticket_user_assign",
        description="Asigna usuarios a un ticket",
        input_schema=_assignment_schema(
            "ticket_id",
            "ticket",
            "users",
            _actor_schema("users_id", "usuario"),
            "Parametros para asignar usuarios a un ticket",
        ),
        handler_name="_ticket_user_assign",
    ),
    ToolSpec(
        name="ticket_group_assign",
        description="Asigna grupos a un ticket",
        input_schema=_assignment_schema(
            "ticket_id",
            "ticket",
            "groups",
            _actor_schema("groups_id", "grupo"),
            "Parametros para asignar grupos a un ticket",
        ),
        handler_name="_ticket_group_assign",
    ),
    ToolSpec(
        name="change_follow_add",
        description="Agrega un comentario (seguimiento) a un cambio",
        input_schema=_comment_schema("change_id", "cambio"),
        handler_name="_change_follow_add",
    ),
    ToolSpec(
        name="change_follow_list",
        description="Lista los comentarios (seguimientos, ITILFollowup) de un cambio",
        input_schema=_sub_item_listing_schema(
            "change_id", "cambio", "Parametros para listar seguimientos de un cambio"
        ),
        handler_name="_change_follow_list",
    ),
    ToolSpec(
        name="change_solution_add",
        description="Registra una solucion para un cambio",
        input_schema=_solution_schema("change_id", "cambio"),
        handler_name="_change_solution_add",
    ),
    ToolSpec(
        name="change_solution_list",
        description="Lista las soluciones (ITILSolution) de un cambio",
        input_schema=_sub_item_listing_schema(
            "change_id", "cambio", "Parametros para listar soluciones de un cambio"
        ),
        handler_name="_change_solution_list",
    ),
    ToolSpec(
        name="change_user_assign",
        description="Asigna usuarios a un cambio",
        input_schema=_assignment_schema(
            "change_id",
            "cambio",
            "users",
            _actor_schema("users_id", "usuario"),
            "Parametros para asignar usuarios a un cambio",
        ),
        handler_name="_change_user_assign",
    ),
    ToolSpec(
        name="change_group_assign",
        description="Asigna grupos a un cambio",
        input_schema=_assignment_schema(
            "change_id",
            "cambio",
            "groups",
            _actor_schema("groups_id", "grupo"),
            "Parametros para asignar grupos a un cambio",
        ),
        handler_name="_change_group_assign",
    ),
    ToolSpec(
        name="change_ticket_link",
        description="Vincula un ticket existente a un cambio",
        input_schema=_link_schema("change_id", "cambio", "ticket_id", "ticket"),
        handler_name="_change_ticket_link",
    ),
    ToolSpec(
        name="ticket_change_link",
        description="Vincula un cambio existente a un ticket",
        input_schema=_link_schema("ticket_id", "ticket", "change_id", "cambio"),
        handler_name="_ticket_change_link",
    ),
    ToolSpec(
        name="change_ticket_unlink",
        description="Elimina la relacion Change_Ticket desde un cambio",
        input_schema=_unlink_schema("change_id", "cambio"),
        handler_name="_change_ticket_unlink",
    ),
    ToolSpec(
        name="ticket_change_unlink",
        description="Elimina la relacion Change_Ticket desde un ticket",
        input_schema=_unlink_schema("ticket_id", "ticket"),
        handler_name="_ticket_change_unlink",
    ),
    ToolSpec(
        name="change_update",
        description="Actualiza campos de un cambio",
        input_schema=_update_schema("change_id", "cambio"),
        handler_name="_change_update",
    ),
    ToolSpec(
        name="ticket_update",
        description="Actualiza campos de un ticket",
        input_schema=_update_schema("ticket_id", "ticket"),
        handler_name="_ticket_update",
    ),
    ToolSpec(
        name="ticket_delete",
        description="Elimina un ticket (a la papelera, o con purga definitiva si se indica)",
        input_schema=_delete_schema("ticket_id", "ticket"),
        handler_name="_ticket_delete",
    ),
    ToolSpec(
        name="change_delete",
        description="Elimina un cambio (a la papelera, o con purga definitiva si se indica)",
        input_schema=_delete_schema("change_id", "cambio"),
        handler_name="_change_delete",
    ),
    ToolSpec(
        name="item_type_list",
        description=(
            "Lista los itemtypes de GLPI soportados por las herramientas genericas "
            "'item_list'/'item_subitem_list', con una breve descripcion de cada uno"
        ),
        input_schema=_item_type_list_schema(),
        handler_name="_item_type_list",
    ),
    ToolSpec(
        name="item_subtype_list",
        description=(
            "Lista los subtypes soportados por 'item_subitem_list' (opcionalmente "
            "filtrados por itemtype), con una breve descripcion de cada uno"
        ),
        input_schema=_item_subtype_list_schema(),
        handler_name="_item_subtype_list",
    ),
    ToolSpec(
        name="item_list",
        description=(
            "Acceso generico de solo lectura: lista elementos de un itemtype "
            "soportado de GLPI. Use 'item_type_list' para ver los itemtypes "
            "soportados, o 'item_get' para consultar un elemento puntual."
        ),
        input_schema=_item_list_schema(),
        handler_name="_item_list",
    ),
    ToolSpec(
        name="item_get",
        description=(
            "Acceso generico de solo lectura a un elemento puntual (por id) "
            "de un itemtype soportado de GLPI. Use 'item_type_list' para ver "
            "los itemtypes soportados, o 'item_list' para listar varios."
        ),
        input_schema=_item_get_schema(),
        handler_name="_item_get",
    ),
    ToolSpec(
        name="item_subitem_list",
        description=(
            "Acceso generico de solo lectura a los sub-items de un elemento "
            "GLPI soportado. Use 'item_subtype_list' para ver las combinaciones "
            "itemtype/subtype soportadas."
        ),
        input_schema=_item_subitem_list_schema(),
        handler_name="_item_subitem_list",
    ),
    ToolSpec(
        name="item_delete",
        description=(
            "Elimina un elemento de un itemtype soportado (a la papelera, o "
            "con purga definitiva si se indica). Use 'item_type_list' para "
            "ver los itemtypes soportados."
        ),
        input_schema=_item_delete_schema(),
        handler_name="_item_delete",
    ),
    ToolSpec(
        name="file_upload",
        description=(
            "Sube un archivo local como Document de GLPI. Use 'item_list'/'item_get' "
            "con itemtype='Document' para buscar/consultar documentos, y 'file_link' "
            "para vincularlo a un ticket o cambio."
        ),
        input_schema=_file_upload_schema(),
        handler_name="_file_upload",
    ),
    ToolSpec(
        name="file_download",
        description=(
            "Descarga un Document de GLPI y lo escribe en una ruta local. Use "
            "'item_list'/'item_get' con itemtype='Document' para encontrar el id a descargar."
        ),
        input_schema=_file_download_schema(),
        handler_name="_file_download",
    ),
    ToolSpec(
        name="file_link",
        description=(
            "Vincula un Document existente a un ticket o cambio (Document_Item). Use "
            "'item_subitem_list' con subtype='Document_Item' para ver los documentos ya vinculados."
        ),
        input_schema=_file_link_schema(),
        handler_name="_file_link",
    ),
    ToolSpec(
        name="file_unlink",
        description="Elimina la relacion Document_Item entre un documento y el elemento al que estaba vinculado",
        input_schema=_unlink_schema("document_id", "documento", relation_label="Document_Item"),
        handler_name="_file_unlink",
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
