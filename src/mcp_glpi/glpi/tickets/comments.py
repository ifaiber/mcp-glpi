"""Ticket follow-up operations."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..shared import ensure_non_empty_text, ensure_positive_int, merge_non_null_values, prepare_bool_flag
from .common import TicketMutationResult, open_handler


def add_followup(
    ticket_id: Any,
    content: Any,
    *,
    is_private: bool | Any = False,
    additional_fields: Optional[Dict[str, Any]] = None,
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
        response = handler.add_items("ITILFollowup", payload)

    return TicketMutationResult(
        action="add_ticket_comment",
        ticket_id=ticket_id_int,
        description=f"Added follow-up to ticket {ticket_id_int}",
        payload=payload,
        response=response,
    )
