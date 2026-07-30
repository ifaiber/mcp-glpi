"""Generic access to GLPI itemtypes and their sub-items.

Unlike the ticket/change-specific tools, this module lets a caller reach any
GLPI itemtype (and, for sub-items, any itemtype/subtype pair) through one set
of tools instead of a hand-written tool per combination. ``ITEMTYPE_CATALOG``
is a **reference list, not a restriction**: it documents itemtypes/subtypes
already verified against a real GLPI instance, exposed via `item_type_list`/
`item_subtype_list` so a caller knows good values to try. `item_list`/
`item_get`/`item_delete`/`item_subitem_list` do not enforce membership in it
-- any itemtype/subtype string is forwarded to GLPI as-is. GLPI itself is the
real gatekeeper: an itemtype that doesn't exist, a subtype invalid for that
itemtype, or a right the active profile lacks all surface as GLPI's own
error (404/400/403), not a validation error raised before the call is made.
Mostly read-only (list/get/list-subitems); `delete_item` is the one generic
mutation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Union

from glpi_client import RequestHandler as GLPIRequestHandler
from glpi_client import SortOrder

from ..common.config import get_config
from .shared import (
    EntityList,
    EntityMutationResult,
    ensure_positive_int,
    fetch_paginated_items,
    fetch_paginated_subitems,
    prepare_bool_flag,
    prepare_generic_item,
    switch_active_entity,
    switch_active_profile,
)

RequestHandler = GLPIRequestHandler


def open_handler():
    config = get_config()
    return RequestHandler(config.url, config.app_token, config.user_token, False)


ITEMTYPE_CATALOG: Dict[str, Dict[str, Any]] = {
    "Ticket": {
        "description": "Tickets de soporte de GLPI.",
        "subtypes": {
            "ITILFollowup": "Comentarios/seguimientos del ticket.",
            "ITILSolution": "Soluciones registradas para el ticket.",
            "Ticket_User": "Usuarios asignados/relacionados al ticket.",
            "Group_Ticket": "Grupos asignados/relacionados al ticket.",
            "Change_Ticket": "Relacion con cambios vinculados al ticket.",
            "Document_Item": "Documentos (archivos) vinculados al ticket.",
        },
    },
    "Change": {
        "description": "Cambios (RFC) de GLPI.",
        "subtypes": {
            "ITILFollowup": "Comentarios/seguimientos del cambio.",
            "ITILSolution": "Soluciones registradas para el cambio.",
            "Change_User": "Usuarios asignados/relacionados al cambio.",
            "Change_Group": "Grupos asignados/relacionados al cambio.",
            "Change_Ticket": "Relacion con tickets vinculados al cambio.",
            "Document_Item": "Documentos (archivos) vinculados al cambio.",
        },
    },
    "Document": {
        "description": "Documentos (archivos) adjuntos en GLPI.",
        "subtypes": {},
    },
    "Computer": {
        "description": "Equipos de computo (activos) de GLPI.",
        "subtypes": {
            "Document_Item": "Documentos (archivos) vinculados al equipo.",
            "Ticket": "Tickets relacionados con el equipo.",
            "Item_SoftwareVersion": "Versiones de software instaladas en el equipo.",
            "ComputerAntivirus": "Antivirus instalados en el equipo.",
            "ComputerVirtualMachine": "Maquinas virtuales alojadas en el equipo.",
        },
    },
    "Monitor": {
        "description": "Monitores (activos) de GLPI.",
        "subtypes": {
            "Document_Item": "Documentos (archivos) vinculados al monitor.",
            "Ticket": "Tickets relacionados con el monitor.",
        },
    },
    "Software": {
        "description": "Software (catalogo) de GLPI.",
        "subtypes": {
            "Document_Item": "Documentos (archivos) vinculados al software.",
            "SoftwareVersion": "Versiones registradas del software.",
        },
    },
    "SoftwareVersion": {
        "description": "Versiones de software de GLPI.",
        "subtypes": {},
    },
    "Project": {
        "description": "Proyectos de GLPI.",
        "subtypes": {
            "Document_Item": "Documentos (archivos) vinculados al proyecto.",
            "Ticket": "Tickets relacionados con el proyecto.",
            "ProjectTask": "Tareas del proyecto.",
        },
    },
    "ProjectTask": {
        "description": "Tareas de proyecto de GLPI.",
        "subtypes": {
            "Document_Item": "Documentos (archivos) vinculados a la tarea.",
            "Ticket": "Tickets relacionados con la tarea.",
        },
    },
    "KnowbaseItem": {
        "description": "Articulos de la base de conocimiento de GLPI.",
        "subtypes": {
            "Document_Item": "Documentos (archivos) vinculados al articulo.",
            "Ticket": "Tickets relacionados con el articulo.",
        },
    },
    "Reminder": {
        "description": "Recordatorios (notas) de GLPI.",
        "subtypes": {
            "Document_Item": "Documentos (archivos) vinculados al recordatorio.",
        },
    },
    "ContractType": {
        "description": "Tipos de contrato de GLPI.",
        "subtypes": {},
    },
    "Manufacturer": {
        "description": "Fabricantes de GLPI.",
        "subtypes": {
            "Document_Item": "Documentos (archivos) vinculados al fabricante.",
        },
    },
    "DeviceSimcard": {
        "description": "Tarjetas SIM (componentes) de GLPI.",
        "subtypes": {},
    },
}


def normalize_itemtype(itemtype: Any) -> str:
    """Validate that an itemtype was actually provided; does not restrict it.

    Any non-blank value is forwarded to GLPI as-is. GLPI decides whether the
    itemtype exists and whether the active profile can access it.
    """
    itemtype_str = str(itemtype).strip() if itemtype is not None else ""
    if not itemtype_str:
        raise ValueError("itemtype is required")
    return itemtype_str


def normalize_subtype(subtype: Any) -> str:
    """Validate that a subtype was actually provided; does not restrict it.

    Any non-blank value is forwarded to GLPI as-is. GLPI decides whether the
    subtype is a valid sub-item route for the given itemtype.
    """
    subtype_str = str(subtype).strip() if subtype is not None else ""
    if not subtype_str:
        raise ValueError("subtype is required")
    return subtype_str


def list_itemtypes() -> List[Dict[str, Any]]:
    """Known/verified itemtypes, for guidance -- not the only ones accepted."""
    return [
        {"itemtype": name, "description": meta["description"]}
        for name, meta in ITEMTYPE_CATALOG.items()
    ]


def list_subtypes(itemtype: Optional[Any] = None) -> List[Dict[str, Any]]:
    """Known/verified subtypes, for guidance -- not the only ones accepted.

    Filtering by an ``itemtype`` outside ``ITEMTYPE_CATALOG`` simply returns
    an empty list (no curated subtypes on file for it yet); it does not
    raise, since ``item_subitem_list`` itself accepts any subtype string.
    """
    if itemtype is not None:
        itemtype_str = normalize_itemtype(itemtype)
        catalog = {itemtype_str: ITEMTYPE_CATALOG[itemtype_str]} if itemtype_str in ITEMTYPE_CATALOG else {}
    else:
        catalog = ITEMTYPE_CATALOG

    result = []
    for item_name, meta in catalog.items():
        for sub_name, description in meta["subtypes"].items():
            result.append({"itemtype": item_name, "subtype": sub_name, "description": description})
    return result


def list_items(
    itemtype: Any,
    *,
    limit: Optional[int] = 20,
    offset: int = 0,
    sort_by: Optional[str] = None,
    order: Union[SortOrder, str] = SortOrder.Descending,
    output: str = "dict",
    fields: Optional[Sequence[str]] = None,
    filters: Optional[Dict[str, str]] = None,
    expand_dropdowns: bool = False,
    include_deleted: bool = False,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
):
    """Generic read: GET /{itemtype}."""
    itemtype_str = normalize_itemtype(itemtype)
    items, response_range = fetch_paginated_items(
        itemtype_str,
        open_handler,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        order=order,
        filters=filters,
        expand_dropdowns=expand_dropdowns,
        include_deleted=include_deleted,
        entity_id=entity_id,
        profile_id=profile_id,
    )
    item_list = EntityList(
        item_key="items", items=items, response_range=response_range, prepare_item=prepare_generic_item
    )
    return item_list.respond(output, fields)


def get_item(
    itemtype: Any,
    item_id: Any,
    *,
    fields: Optional[Sequence[str]] = None,
    expand_dropdowns: bool = False,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
):
    """Generic read: GET /{itemtype}/{id}."""
    itemtype_str = normalize_itemtype(itemtype)
    item_id_int = ensure_positive_int(item_id, "id")

    with open_handler() as handler:
        switch_active_profile(handler, profile_id)
        switch_active_entity(handler, entity_id)
        item = handler.get_item(itemtype_str, item_id_int, expand_dropdowns=expand_dropdowns)

    return prepare_generic_item(item, fields) if fields else item


def list_subitems(
    itemtype: Any,
    item_id: Any,
    subtype: Any,
    *,
    limit: Optional[int] = 20,
    offset: int = 0,
    sort_by: Optional[str] = None,
    order: Union[SortOrder, str] = SortOrder.Descending,
    output: str = "dict",
    fields: Optional[Sequence[str]] = None,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
):
    """Generic read: GET /{itemtype}/{id}/{subtype}."""
    itemtype_str = normalize_itemtype(itemtype)
    subtype_str = normalize_subtype(subtype)
    item_id_int = ensure_positive_int(item_id, "id")
    items, response_range = fetch_paginated_subitems(
        itemtype_str,
        item_id_int,
        subtype_str,
        open_handler,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        order=order,
        entity_id=entity_id,
        profile_id=profile_id,
    )
    item_list = EntityList(
        item_key="items", items=items, response_range=response_range, prepare_item=prepare_generic_item
    )
    return item_list.respond(output, fields)


def delete_item(
    itemtype: Any,
    item_id: Any,
    *,
    purge: Any = False,
    keep_history: Any = True,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
) -> EntityMutationResult:
    """Generic delete: DELETE /{itemtype}/{id}."""
    itemtype_str = normalize_itemtype(itemtype)
    item_id_int = ensure_positive_int(item_id, "id")
    purge_flag = bool(prepare_bool_flag(purge))
    keep_history_flag = bool(prepare_bool_flag(keep_history))

    with open_handler() as handler:
        switch_active_profile(handler, profile_id)
        switch_active_entity(handler, entity_id)
        response = handler.delete_items(
            itemtype_str,
            [item_id_int],
            purge=purge_flag,
            log=keep_history_flag,
        )

    return EntityMutationResult(
        action="item_delete",
        entity_id_field="id",
        entity_id=item_id_int,
        description=f"Deleted {itemtype_str} {item_id_int}",
        payload={
            "itemtype": itemtype_str,
            "id": item_id_int,
            "purge": purge_flag,
            "keep_history": keep_history_flag,
        },
        response=response,
    )
