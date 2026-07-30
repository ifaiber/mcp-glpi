"""Single source of truth for MCP tool metadata."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Any, Dict, List

import mcp.types as types

from .glpi.assistance import ASSISTANCE_ITEMTYPES
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
        "activa por defecto de la sesion. Use 'entityprofile_list' para "
        "obtener los codigos disponibles (cada perfil trae su lista de "
        "entidades asociadas). Tambien acepta el *nombre* de la entidad "
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
        "por defecto de la sesion. Use 'entityprofile_list' para ver los "
        "perfiles disponibles y sus entidades asociadas. Si vas a combinar "
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
                    "Filtra los subtypes conocidos por este itemtype (por "
                    f"ejemplo, {_SUPPORTED_ITEMTYPES}, aunque no esta "
                    "limitado a esta lista). Si se omite, lista los subtypes "
                    "conocidos de todos los itemtypes documentados."
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
            "description": (
                "Itemtype de GLPI (cualquier itemtype valido de GLPI, no "
                f"esta limitado a una lista fija; ejemplos conocidos: "
                f"{_SUPPORTED_ITEMTYPES}). Use 'item_type_list' para ver "
                "ejemplos. GLPI valida existencia y permisos al ejecutar."
            ),
        },
    }
    properties.update(copy.deepcopy(_listing_properties))
    return {
        "type": "object",
        "properties": properties,
        "required": ["itemtype"],
        "description": (
            "Acceso generico de solo lectura: lista elementos de un itemtype "
            "de GLPI (equivalente a GET /{itemtype}). Para obtener un "
            "elemento puntual por id use 'item_get'."
        ),
    }


def _item_get_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "itemtype": {
                "type": "string",
                "description": (
                    "Itemtype de GLPI (cualquier itemtype valido de GLPI; "
                    f"ejemplos conocidos: {_SUPPORTED_ITEMTYPES}). Use "
                    "'item_type_list' para ver ejemplos."
                ),
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
            "itemtype de GLPI (equivalente a GET /{itemtype}/{id}). Para "
            "listar varios use 'item_list'."
        ),
    }


def _item_subitem_list_schema() -> Dict[str, Any]:
    properties = {
        "itemtype": {
            "type": "string",
            "description": (
                "Itemtype del elemento padre (cualquier itemtype valido de "
                f"GLPI; ejemplos conocidos: {_SUPPORTED_ITEMTYPES}). Use "
                "'item_type_list' para ver ejemplos."
            ),
        },
        "id": {
            "type": ["integer", "string"],
            "description": "Identificador del elemento padre.",
        },
        "subtype": {
            "type": "string",
            "description": (
                "Subtype a listar (cualquier subtype valido de GLPI para ese "
                "itemtype, no esta limitado a una lista fija). Use "
                "'item_subtype_list' con el mismo itemtype para ver ejemplos "
                "conocidos."
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
            "(equivalente a GET /{itemtype}/{id}/{subtype}); GLPI valida si "
            "el itemtype/subtype/permiso es correcto al ejecutar."
        ),
    }


def _item_delete_schema() -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "itemtype": {
                "type": "string",
                "description": (
                    "Itemtype de GLPI (cualquier itemtype valido de GLPI; "
                    f"ejemplos conocidos: {_SUPPORTED_ITEMTYPES}). Use "
                    "'item_type_list' para ver ejemplos."
                ),
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
            "Elimina un elemento de GLPI (equivalente a DELETE /{itemtype}/"
            "{id}), a la papelera o con purga definitiva si se indica."
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


def _assistance_subitem_base_properties() -> Dict[str, Any]:
    return {
        "itemtype": {
            "type": "string",
            "enum": sorted(ASSISTANCE_ITEMTYPES.keys()),
            "description": "Itemtype del Ticket o Change al que pertenece el sub-item.",
        },
        "id": {
            "type": ["integer", "string"],
            "description": "Identificador del Ticket o Change segun 'itemtype'.",
        },
    }


def _assistance_followup_schema() -> Dict[str, Any]:
    properties = _assistance_subitem_base_properties()
    properties.update(copy.deepcopy(_comment_base_properties))
    return {
        "type": "object",
        "properties": properties,
        "required": ["itemtype", "id", "content"],
        "description": (
            "Parametros para agregar un comentario (ITILFollowup) a un Ticket "
            "o Change. A diferencia de Ticket_User/Change_User, ITILFollowup ya "
            "es itemtype-generico en GLPI (campos 'itemtype'/'items_id'), asi "
            "que solo cambia el valor de 'itemtype' segun corresponda."
        ),
    }


def _assistance_followup_update_schema() -> Dict[str, Any]:
    properties = _assistance_subitem_base_properties()
    properties["followup_id"] = {
        "type": ["integer", "string"],
        "description": "Identificador del comentario (ITILFollowup) a actualizar.",
    }
    properties.update(copy.deepcopy(_comment_base_properties))
    return {
        "type": "object",
        "properties": properties,
        "required": ["itemtype", "id", "followup_id", "content"],
        "description": (
            "Parametros para actualizar un comentario (ITILFollowup) existente "
            "en un Ticket o Change. Misma forma que assistance_item_followup_add, "
            "con el agregado de 'followup_id' (el id propio del comentario)."
        ),
    }


def _assistance_solution_schema() -> Dict[str, Any]:
    properties = _assistance_subitem_base_properties()
    properties.update(copy.deepcopy(_solution_base_properties))
    return {
        "type": "object",
        "properties": properties,
        "required": ["itemtype", "id", "content"],
        "description": (
            "Parametros para agregar una solucion (ITILSolution) a un Ticket "
            "o Change. Igual que ITILFollowup, ITILSolution ya es "
            "itemtype-generico en GLPI (campos 'itemtype'/'items_id')."
        ),
    }


def _assistance_solution_update_schema() -> Dict[str, Any]:
    properties = _assistance_subitem_base_properties()
    properties["solution_id"] = {
        "type": ["integer", "string"],
        "description": "Identificador de la solucion (ITILSolution) a actualizar.",
    }
    properties.update(copy.deepcopy(_solution_base_properties))
    return {
        "type": "object",
        "properties": properties,
        "required": ["itemtype", "id", "solution_id", "content"],
        "description": (
            "Parametros para actualizar una solucion (ITILSolution) existente "
            "en un Ticket o Change. Misma forma que assistance_item_solution_add, "
            "con el agregado de 'solution_id' (el id propio de la solucion)."
        ),
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


def _assistance_assignment_schema(
    actor_id_field: str,
    actor_label: str,
    actors_key: str,
    subtype_hint: str,
) -> Dict[str, Any]:
    actor_schema = _actor_schema(actor_id_field, actor_label)
    return {
        "type": "object",
        "properties": {
            "itemtype": {
                "type": "string",
                "enum": sorted(ASSISTANCE_ITEMTYPES.keys()),
                "description": f"Itemtype al que se asignan los {actors_key} (Ticket o Change).",
            },
            "id": {
                "type": ["integer", "string"],
                "description": "Identificador del Ticket o Change segun 'itemtype'.",
            },
            actors_key: _actors_property(actor_schema, f"Listado de {actors_key} a asignar"),
            "entity_id": _entity_id_property,
            "profile_id": _profile_id_property,
        },
        "required": ["itemtype", "id", actors_key],
        "description": (
            f"Parametros para asignar {actors_key} a un Ticket o Change. El campo "
            f"GLPI (tickets_id/changes_id) y el subtype ({subtype_hint}) "
            "se derivan automaticamente de 'itemtype'."
        ),
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


def _assistance_ticketchange_link_id_property() -> Dict[str, Any]:
    return {
        "type": ["integer", "string"],
        "description": (
            "Identificador del lado complementario: un change_id si "
            "itemtype es 'Ticket', o un ticket_id si itemtype es 'Change'."
        ),
    }


def _assistance_ticketchange_link_schema() -> Dict[str, Any]:
    properties = _assistance_subitem_base_properties()
    properties["link_id"] = _assistance_ticketchange_link_id_property()
    properties["additional"] = {
        "type": "object",
        "additionalProperties": True,
        "description": "Campos adicionales que se enviaran tal cual",
    }
    properties["entity_id"] = _entity_id_property
    properties["profile_id"] = _profile_id_property
    return {
        "type": "object",
        "properties": properties,
        "required": ["itemtype", "id", "link_id"],
        "description": (
            "Vincula un Ticket y un Change (Change_Ticket). Reemplaza a "
            "ticket_change_link/change_ticket_link: itemtype+id identifican "
            "un lado, link_id identifica el lado complementario."
        ),
    }


def _assistance_ticketchange_unlink_schema() -> Dict[str, Any]:
    properties = _assistance_subitem_base_properties()
    properties["link_id"] = _assistance_ticketchange_link_id_property()
    properties["purge"] = {
        "type": _def_bool,
        "description": "Forzar purga del enlace",
    }
    properties["keep_history"] = {
        "type": _def_bool,
        "description": "Mantener historial de GLPI",
    }
    properties["entity_id"] = _entity_id_property
    properties["profile_id"] = _profile_id_property
    return {
        "type": "object",
        "properties": properties,
        "required": ["itemtype", "id", "link_id"],
        "description": (
            "Elimina la relacion Change_Ticket entre un ticket y un cambio. "
            "Misma forma que assistance_item_ticketchange_link (itemtype+id "
            "identifican un lado, link_id el lado complementario); el id "
            "propio de la relacion Change_Ticket se resuelve internamente "
            "antes de eliminarla."
        ),
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
                "description": (
                    "Itemtype al que se vinculara el documento (cualquier "
                    f"itemtype valido de GLPI; ejemplos conocidos: "
                    f"{_SUPPORTED_ITEMTYPES})."
                ),
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
        name="entityprofile_list",
        description=(
            "Lista los perfiles del usuario logueado, cada uno con sus "
            "entidades asociadas (id, nombre, is_recursive). Util para "
            "obtener los codigos a usar con 'profile_id'/'entity_id' de "
            "otras herramientas."
        ),
        input_schema={"type": "object", "properties": {}, "required": []},
        handler_name="_entityprofile_list",
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
        name="assistance_item_user_add",
        description=(
            "Asigna usuarios a un Ticket o Change (Ticket_User/Change_User). "
            "Reemplaza a ticket_user_assign/change_user_assign: itemtype "
            "decide internamente el campo (tickets_id/changes_id) y el "
            "subtype (Ticket_User/Change_User) correctos."
        ),
        input_schema=_assistance_assignment_schema(
            "users_id", "usuario", "users", "Ticket_User/Change_User"
        ),
        handler_name="_assistance_item_user_add",
    ),
    ToolSpec(
        name="assistance_item_group_add",
        description=(
            "Asigna grupos a un Ticket o Change (Group_Ticket/Change_Group). "
            "Reemplaza a ticket_group_assign/change_group_assign: itemtype "
            "decide internamente el campo (tickets_id/changes_id) y el "
            "subtype (Group_Ticket/Change_Group) correctos."
        ),
        input_schema=_assistance_assignment_schema(
            "groups_id", "grupo", "groups", "Group_Ticket/Change_Group"
        ),
        handler_name="_assistance_item_group_add",
    ),
    ToolSpec(
        name="assistance_item_followup_add",
        description=(
            "Agrega un comentario (ITILFollowup) a un Ticket o Change. "
            "Reemplaza a ticket_follow_add/change_follow_add: ITILFollowup ya "
            "es itemtype-generico en GLPI, asi que solo cambia el valor de "
            "'itemtype' segun corresponda."
        ),
        input_schema=_assistance_followup_schema(),
        handler_name="_assistance_item_followup_add",
    ),
    ToolSpec(
        name="assistance_item_followup_update",
        description=(
            "Actualiza un comentario (ITILFollowup) existente en un Ticket o "
            "Change. Misma forma que assistance_item_followup_add, con "
            "'followup_id' (id propio del comentario) agregado."
        ),
        input_schema=_assistance_followup_update_schema(),
        handler_name="_assistance_item_followup_update",
    ),
    ToolSpec(
        name="assistance_item_solution_add",
        description=(
            "Registra una solucion (ITILSolution) en un Ticket o Change. "
            "Reemplaza a ticket_solution_add/change_solution_add: ITILSolution ya "
            "es itemtype-generico en GLPI (igual que ITILFollowup), asi que solo "
            "cambia el valor de 'itemtype' segun corresponda."
        ),
        input_schema=_assistance_solution_schema(),
        handler_name="_assistance_item_solution_add",
    ),
    ToolSpec(
        name="assistance_item_solution_update",
        description=(
            "Actualiza una solucion (ITILSolution) existente en un Ticket o "
            "Change. Misma forma que assistance_item_solution_add, con "
            "'solution_id' (id propio de la solucion) agregado."
        ),
        input_schema=_assistance_solution_update_schema(),
        handler_name="_assistance_item_solution_update",
    ),
    ToolSpec(
        name="assistance_item_ticketchange_link",
        description=(
            "Vincula un ticket y un cambio existentes (Change_Ticket). "
            "Reemplaza a ticket_change_link/change_ticket_link: ambos eran "
            "mecanicamente identicos (mismo POST /Change_Ticket), solo con "
            "nombres/orden de parametros distintos. itemtype+id identifican "
            "un lado, link_id identifica el lado complementario."
        ),
        input_schema=_assistance_ticketchange_link_schema(),
        handler_name="_assistance_item_ticketchange_link",
    ),
    ToolSpec(
        name="assistance_item_ticketchange_unlink",
        description=(
            "Elimina la relacion Change_Ticket entre un ticket y un cambio. "
            "Reemplaza a ticket_change_unlink/change_ticket_unlink. Misma "
            "forma que assistance_item_ticketchange_link (itemtype+id "
            "identifican un lado, link_id el lado complementario); resuelve "
            "internamente el id de la relacion antes de eliminarla."
        ),
        input_schema=_assistance_ticketchange_unlink_schema(),
        handler_name="_assistance_item_ticketchange_unlink",
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
