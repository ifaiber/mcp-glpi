"""Ticket follow-up operations."""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Union

from glpi_client import SortOrder

from ..shared import (
    EntityList,
    ensure_non_empty_text,
    ensure_positive_int,
    fetch_paginated_subitems,
    merge_non_null_values,
    prepare_bool_flag,
    prepare_generic_item,
    switch_active_entity,
    switch_active_profile,
)
from .common import TicketMutationResult, open_handler

FOLLOWUP_DEFAULT_FIELDS: Sequence[str] = ("id", "date", "users_id", "content", "is_private")


def add_followup(
    ticket_id: Any,
    content: Any,
    *,
    is_private: bool | Any = False,
    additional_fields: Optional[Dict[str, Any]] = None,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
) -> TicketMutationResult:
    ticket_id_int = ensure_positive_int(ticket_id, "ticket_id")
    comment = ensure_non_empty_text(content, "content")
    payload: Dict[str, Any] = {
        "itemtype": "Ticket",
        "items_id": ticket_id_int,
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

    return TicketMutationResult(
        action="ticket_follow_add",
        ticket_id=ticket_id_int,
        description=f"Added follow-up to ticket {ticket_id_int}",
        payload=payload,
        response=response,
    )


def list_followups(
    ticket_id: Any,
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
    ticket_id_int = ensure_positive_int(ticket_id, "ticket_id")
    items, response_range = fetch_paginated_subitems(
        "Ticket",
        ticket_id_int,
        "ITILFollowup",
        open_handler,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        order=order,
        entity_id=entity_id,
        profile_id=profile_id,
    )
    followup_list = EntityList(
        item_key="followups", items=items, response_range=response_range, prepare_item=prepare_generic_item
    )
    return followup_list.respond(output, fields, default_fields=FOLLOWUP_DEFAULT_FIELDS)
