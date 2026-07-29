"""Generic, allowlisted access to GLPI itemtypes and their sub-items.

Unlike the ticket/change-specific tools, this module lets a caller reach any
*supported* GLPI itemtype (and, for sub-items, a supported itemtype/subtype
pair) through one pair of tools instead of a hand-written tool per
combination. ``ITEMTYPE_CATALOG`` is a deliberate allowlist: it only covers
itemtypes/subtypes this server already understands elsewhere (tickets,
changes, and their follow-ups/solutions/actors/links), so a caller can't
reach unrelated GLPI data (User, Config, Computer, ...) that was never meant
to be exposed here. Read-only: no create/update/delete.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence, Union

from glpi_client import RequestHandler as GLPIRequestHandler
from glpi_client import SortOrder

from ..common.config import get_config
from .shared import (
    EntityList,
    ensure_positive_int,
    fetch_paginated_items,
    fetch_paginated_subitems,
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
}


def ensure_supported_itemtype(itemtype: Any) -> str:
    itemtype_str = str(itemtype)
    if itemtype_str not in ITEMTYPE_CATALOG:
        supported = ", ".join(sorted(ITEMTYPE_CATALOG))
        raise ValueError(
            f"Unsupported itemtype '{itemtype_str}'. Supported: {supported}. "
            "Use 'item_type_list' to see supported values."
        )
    return itemtype_str


def ensure_supported_subtype(itemtype: Any, subtype: Any) -> str:
    itemtype_str = ensure_supported_itemtype(itemtype)
    subtype_str = str(subtype)
    allowed = ITEMTYPE_CATALOG[itemtype_str]["subtypes"]
    if subtype_str not in allowed:
        supported = ", ".join(sorted(allowed))
        raise ValueError(
            f"Unsupported subtype '{subtype_str}' for itemtype '{itemtype_str}'. "
            f"Supported for {itemtype_str}: {supported}. Use 'item_subtype_list' to see supported values."
        )
    return subtype_str


def list_itemtypes() -> List[Dict[str, Any]]:
    return [
        {"itemtype": name, "description": meta["description"]}
        for name, meta in ITEMTYPE_CATALOG.items()
    ]


def list_subtypes(itemtype: Optional[Any] = None) -> List[Dict[str, Any]]:
    if itemtype is not None:
        itemtype_str = ensure_supported_itemtype(itemtype)
        catalog = {itemtype_str: ITEMTYPE_CATALOG[itemtype_str]}
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
    itemtype_str = ensure_supported_itemtype(itemtype)
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
    itemtype_str = ensure_supported_itemtype(itemtype)
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
    itemtype_str = ensure_supported_itemtype(itemtype)
    subtype_str = ensure_supported_subtype(itemtype_str, subtype)
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
