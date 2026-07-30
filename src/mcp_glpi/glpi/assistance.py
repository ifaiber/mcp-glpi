"""Operations shared by GLPI's assistance itemtypes (Ticket, Change).

Ticket and Change both expose the same actor-assignment shape for users
(``Ticket_User``/``Change_User``) and for groups (``Group_Ticket``/
``Change_Group``), keyed by ``tickets_id``/``changes_id`` respectively, so one
generic tool per actor type covers both instead of a hand-written tool per
itemtype. Follow-ups (``ITILFollowup``) are already itemtype-generic on the
GLPI side (``itemtype``/``items_id`` fields, unlike the actor tables), so
only the ``itemtype`` value itself changes between Ticket and Change.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Union

from glpi_client import RequestHandler as GLPIRequestHandler

from ..common.config import get_config
from .shared import (
    EntityMutationResult,
    compact_payload,
    ensure_non_empty_text,
    ensure_positive_int,
    fetch_paginated_subitems,
    merge_non_null_values,
    normalize_actor_entries,
    prepare_bool_flag,
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


def add_assistance_followup(
    itemtype: Any,
    item_id: Any,
    content: Any,
    *,
    is_private: bool | Any = False,
    additional_fields: Optional[Dict[str, Any]] = None,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
) -> EntityMutationResult:
    """Add a follow-up/comment to a Ticket or Change: POST /ITILFollowup."""
    itemtype_str = _resolve_assistance_itemtype(itemtype)
    item_id_int = ensure_positive_int(item_id, "id")
    comment = ensure_non_empty_text(content, "content")
    payload: Dict[str, Any] = {
        "itemtype": itemtype_str,
        "items_id": item_id_int,
        "content": comment,
    }
    private_flag = prepare_bool_flag(is_private)
    if private_flag is not None:
        payload["is_private"] = private_flag

    merge_non_null_values(payload, additional_fields)

    with open_handler() as handler:
        switch_active_profile(handler, profile_id)
        switch_active_entity(handler, entity_id)
        response = handler.add_items("ITILFollowup", payload)

    return EntityMutationResult(
        action="assistance_item_followup_add",
        entity_id_field="id",
        entity_id=item_id_int,
        description=f"Added follow-up to {itemtype_str} {item_id_int}",
        payload=payload,
        response=response,
    )


def update_assistance_followup(
    itemtype: Any,
    item_id: Any,
    followup_id: Any,
    content: Any,
    *,
    is_private: bool | Any = False,
    additional_fields: Optional[Dict[str, Any]] = None,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
) -> EntityMutationResult:
    """Update a follow-up/comment on a Ticket or Change: PATCH /ITILFollowup."""
    itemtype_str = _resolve_assistance_itemtype(itemtype)
    item_id_int = ensure_positive_int(item_id, "id")
    followup_id_int = ensure_positive_int(followup_id, "followup_id")
    comment = ensure_non_empty_text(content, "content")
    payload: Dict[str, Any] = {
        "id": followup_id_int,
        "itemtype": itemtype_str,
        "items_id": item_id_int,
        "content": comment,
    }
    private_flag = prepare_bool_flag(is_private)
    if private_flag is not None:
        payload["is_private"] = private_flag

    merge_non_null_values(payload, additional_fields)

    with open_handler() as handler:
        switch_active_profile(handler, profile_id)
        switch_active_entity(handler, entity_id)
        response = handler.update_items("ITILFollowup", [payload])

    return EntityMutationResult(
        action="assistance_item_followup_update",
        entity_id_field="id",
        entity_id=item_id_int,
        description=f"Updated follow-up {followup_id_int} on {itemtype_str} {item_id_int}",
        payload=payload,
        response=response,
    )


def add_assistance_solution(
    itemtype: Any,
    item_id: Any,
    content: Any,
    *,
    additional_fields: Optional[Dict[str, Any]] = None,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
) -> EntityMutationResult:
    """Add a solution to a Ticket or Change: POST /ITILSolution."""
    itemtype_str = _resolve_assistance_itemtype(itemtype)
    item_id_int = ensure_positive_int(item_id, "id")
    solution_text = ensure_non_empty_text(content, "content")
    payload: Dict[str, Any] = {
        "itemtype": itemtype_str,
        "items_id": item_id_int,
        "content": solution_text,
    }

    merge_non_null_values(payload, additional_fields)

    with open_handler() as handler:
        switch_active_profile(handler, profile_id)
        switch_active_entity(handler, entity_id)
        response = handler.add_items("ITILSolution", payload)

    return EntityMutationResult(
        action="assistance_item_solution_add",
        entity_id_field="id",
        entity_id=item_id_int,
        description=f"Added solution to {itemtype_str} {item_id_int}",
        payload=payload,
        response=response,
    )


def update_assistance_solution(
    itemtype: Any,
    item_id: Any,
    solution_id: Any,
    content: Any,
    *,
    additional_fields: Optional[Dict[str, Any]] = None,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
) -> EntityMutationResult:
    """Update a solution on a Ticket or Change: PATCH /ITILSolution."""
    itemtype_str = _resolve_assistance_itemtype(itemtype)
    item_id_int = ensure_positive_int(item_id, "id")
    solution_id_int = ensure_positive_int(solution_id, "solution_id")
    solution_text = ensure_non_empty_text(content, "content")
    payload: Dict[str, Any] = {
        "id": solution_id_int,
        "itemtype": itemtype_str,
        "items_id": item_id_int,
        "content": solution_text,
    }

    merge_non_null_values(payload, additional_fields)

    with open_handler() as handler:
        switch_active_profile(handler, profile_id)
        switch_active_entity(handler, entity_id)
        response = handler.update_items("ITILSolution", [payload])

    return EntityMutationResult(
        action="assistance_item_solution_update",
        entity_id_field="id",
        entity_id=item_id_int,
        description=f"Updated solution {solution_id_int} on {itemtype_str} {item_id_int}",
        payload=payload,
        response=response,
    )


def link_ticket_change(
    itemtype: Any,
    item_id: Any,
    link_id: Any,
    *,
    additional_fields: Optional[Dict[str, Any]] = None,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
) -> EntityMutationResult:
    """Link a Ticket and a Change: POST /Change_Ticket.

    ``itemtype``/``item_id`` identify one side; ``link_id`` is the id of the
    complementary side (a change id when ``itemtype`` is ``"Ticket"``, or a
    ticket id when ``itemtype`` is ``"Change"``).
    """
    itemtype_str = _resolve_assistance_itemtype(itemtype)
    item_id_int = ensure_positive_int(item_id, "id")
    other_id_int = ensure_positive_int(link_id, "link_id")
    if itemtype_str == "Ticket":
        ticket_id_int, change_id_int = item_id_int, other_id_int
    else:
        change_id_int, ticket_id_int = item_id_int, other_id_int

    payload: Dict[str, Any] = {
        "tickets_id": ticket_id_int,
        "changes_id": change_id_int,
    }
    merge_non_null_values(payload, additional_fields)

    with open_handler() as handler:
        switch_active_profile(handler, profile_id)
        switch_active_entity(handler, entity_id)
        response = handler.add_items("Change_Ticket", payload)

    return EntityMutationResult(
        action="assistance_item_ticketchange_link",
        entity_id_field="id",
        entity_id=item_id_int,
        description=f"Linked ticket {ticket_id_int} to change {change_id_int}",
        payload=payload,
        response=response,
    )


def unlink_ticket_change(
    itemtype: Any,
    item_id: Any,
    link_id: Any,
    *,
    purge: bool | Any = False,
    keep_history: bool | Any = True,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
) -> EntityMutationResult:
    """Remove a Ticket<->Change relation: DELETE /Change_Ticket/{relation_id}.

    Same shape as ``link_ticket_change``: ``itemtype``/``item_id`` identify
    one side, ``link_id`` the complementary side. Referencing the opaque
    ``Change_Ticket`` relation id directly is hard to look up in advance, so
    this resolves it internally (via the same sub-item listing that backs
    ``item_subitem_list``) before deleting.
    """
    itemtype_str = _resolve_assistance_itemtype(itemtype)
    item_id_int = ensure_positive_int(item_id, "id")
    other_id_int = ensure_positive_int(link_id, "link_id")
    if itemtype_str == "Ticket":
        ticket_id_int, change_id_int = item_id_int, other_id_int
    else:
        change_id_int, ticket_id_int = item_id_int, other_id_int

    relations, _ = fetch_paginated_subitems(
        "Change",
        change_id_int,
        "Change_Ticket",
        open_handler,
        limit=100,
        entity_id=entity_id,
        profile_id=profile_id,
    )
    relation_id = next(
        (
            int(relation["id"])
            for relation in relations
            if int(relation.get("tickets_id", -1)) == ticket_id_int
        ),
        None,
    )
    if relation_id is None:
        raise ValueError(
            f"No existe una relacion Change_Ticket entre Ticket {ticket_id_int} y Change {change_id_int}"
        )

    purge_flag = bool(prepare_bool_flag(purge))
    keep_history_flag = bool(prepare_bool_flag(keep_history))

    with open_handler() as handler:
        switch_active_profile(handler, profile_id)
        switch_active_entity(handler, entity_id)
        response = handler.delete_items(
            "Change_Ticket",
            [relation_id],
            purge=purge_flag,
            log=keep_history_flag,
        )

    return EntityMutationResult(
        action="assistance_item_ticketchange_unlink",
        entity_id_field="id",
        entity_id=relation_id,
        description=f"Unlinked ticket {ticket_id_int} from change {change_id_int} (relation {relation_id})",
        payload={
            "tickets_id": ticket_id_int,
            "changes_id": change_id_int,
            "link_id": relation_id,
            "purge": purge_flag,
            "keep_history": keep_history_flag,
        },
        response=response,
    )
