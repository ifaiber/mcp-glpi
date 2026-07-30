"""Actor assignment shared by GLPI's assistance itemtypes (Ticket, Change).

Ticket and Change both expose the same actor-assignment shape for users
(``Ticket_User``/``Change_User``) and for groups (``Group_Ticket``/
``Change_Group``), keyed by ``tickets_id``/``changes_id`` respectively, so one
generic tool per actor type covers both instead of a hand-written tool per
itemtype.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Union

from glpi_client import RequestHandler as GLPIRequestHandler

from ..common.config import get_config
from .shared import (
    EntityMutationResult,
    compact_payload,
    ensure_positive_int,
    normalize_actor_entries,
    switch_active_entity,
    switch_active_profile,
)

RequestHandler = GLPIRequestHandler


def open_handler():
    config = get_config()
    return RequestHandler(config.url, config.app_token, config.user_token, False)


ASSISTANCE_ITEMTYPES: Dict[str, Dict[str, str]] = {
    "Ticket": {
        "id_field": "tickets_id",
        "user_subtype": "Ticket_User",
        "group_subtype": "Group_Ticket",
    },
    "Change": {
        "id_field": "changes_id",
        "user_subtype": "Change_User",
        "group_subtype": "Change_Group",
    },
}


def _resolve_assistance_itemtype(itemtype: Any) -> str:
    itemtype_str = str(itemtype).strip() if itemtype is not None else ""
    if itemtype_str not in ASSISTANCE_ITEMTYPES:
        raise ValueError(
            f"itemtype debe ser uno de {sorted(ASSISTANCE_ITEMTYPES)}, no {itemtype_str!r}"
        )
    return itemtype_str


def assign_assistance_users(
    itemtype: Any,
    item_id: Any,
    users: Union[Dict[str, Any], Sequence[Any], Any],
    *,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
) -> EntityMutationResult:
    """Assign users to a Ticket or Change: POST /Ticket_User or POST /Change_User."""
    itemtype_str = _resolve_assistance_itemtype(itemtype)
    item_id_int = ensure_positive_int(item_id, "id")
    meta = ASSISTANCE_ITEMTYPES[itemtype_str]

    normalized = normalize_actor_entries(
        item_id_int,
        users,
        actor_id_key="users_id",
        item_id_field=meta["id_field"],
        entry_name="users",
    )
    payload_to_send = compact_payload(normalized)

    with open_handler() as handler:
        switch_active_profile(handler, profile_id)
        switch_active_entity(handler, entity_id)
        response = handler.add_items(meta["user_subtype"], payload_to_send)

    return EntityMutationResult(
        action="assistance_item_user_add",
        entity_id_field="id",
        entity_id=item_id_int,
        description=f"Assigned {len(normalized)} user(s) to {itemtype_str} {item_id_int}",
        payload=payload_to_send,
        response=response,
    )


def assign_assistance_groups(
    itemtype: Any,
    item_id: Any,
    groups: Union[Dict[str, Any], Sequence[Any], Any],
    *,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
) -> EntityMutationResult:
    """Assign groups to a Ticket or Change: POST /Group_Ticket or POST /Change_Group."""
    itemtype_str = _resolve_assistance_itemtype(itemtype)
    item_id_int = ensure_positive_int(item_id, "id")
    meta = ASSISTANCE_ITEMTYPES[itemtype_str]

    normalized = normalize_actor_entries(
        item_id_int,
        groups,
        actor_id_key="groups_id",
        item_id_field=meta["id_field"],
        entry_name="groups",
    )
    payload_to_send = compact_payload(normalized)

    with open_handler() as handler:
        switch_active_profile(handler, profile_id)
        switch_active_entity(handler, entity_id)
        response = handler.add_items(meta["group_subtype"], payload_to_send)

    return EntityMutationResult(
        action="assistance_item_group_add",
        entity_id_field="id",
        entity_id=item_id_int,
        description=f"Assigned {len(normalized)} group(s) to {itemtype_str} {item_id_int}",
        payload=payload_to_send,
        response=response,
    )
