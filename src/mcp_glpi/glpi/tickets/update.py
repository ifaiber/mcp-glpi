"""Ticket update operations."""

from __future__ import annotations

from typing import Any, Dict

from ..shared import ensure_positive_int, normalize_update_fields
from .common import ENUM_FIELDS, TicketMutationResult, open_handler


def update_ticket(
    ticket_id: Any,
    fields: Dict[str, Any],
) -> TicketMutationResult:
    ticket_id_int = ensure_positive_int(ticket_id, "ticket_id")
    sanitized = normalize_update_fields(fields, ENUM_FIELDS)
    payload = {"id": ticket_id_int, **sanitized}

    with open_handler() as handler:
        response = handler.update_items("Ticket", [payload])

    return TicketMutationResult(
        action="update_ticket",
        ticket_id=ticket_id_int,
        description=f"Updated ticket {ticket_id_int}",
        payload=payload,
        response=response,
    )
