"""Ticket update operations."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..shared import (
    ensure_positive_int,
    normalize_update_fields,
    switch_active_entity,
    switch_active_profile,
)
from .common import ENUM_FIELDS, TicketMutationResult, open_handler


def update_ticket(
    ticket_id: Any,
    fields: Dict[str, Any],
    *,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
) -> TicketMutationResult:
    ticket_id_int = ensure_positive_int(ticket_id, "ticket_id")
    sanitized = normalize_update_fields(fields, ENUM_FIELDS)
    payload = {"id": ticket_id_int, **sanitized}

    with open_handler() as handler:
        switch_active_profile(handler, profile_id)
        switch_active_entity(handler, entity_id)
        response = handler.update_items("Ticket", [payload])

    return TicketMutationResult(
        action="ticket_update",
        ticket_id=ticket_id_int,
        description=f"Updated ticket {ticket_id_int}",
        payload=payload,
        response=response,
    )
