"""Ticket actor assignment operations."""

from __future__ import annotations

from typing import Any, Dict, Sequence, Union

from ..shared import compact_payload, ensure_positive_int, normalize_actor_entries
from .common import TicketMutationResult, open_handler


def assign_ticket_users(
    ticket_id: Any,
    users: Union[Dict[str, Any], Sequence[Any], Any],
) -> TicketMutationResult:
    ticket_id_int = ensure_positive_int(ticket_id, "ticket_id")
    normalized = normalize_actor_entries(
        ticket_id_int,
        users,
        actor_id_key="users_id",
        item_id_field="tickets_id",
        entry_name="users",
    )
    payload_to_send = compact_payload(normalized)

    with open_handler() as handler:
        response = handler.add_items("Ticket_User", payload_to_send)

    return TicketMutationResult(
        action="assign_ticket_users",
        ticket_id=ticket_id_int,
        description=f"Assigned {len(normalized)} user(s) to ticket {ticket_id_int}",
        payload=payload_to_send,
        response=response,
    )


def assign_ticket_groups(
    ticket_id: Any,
    groups: Union[Dict[str, Any], Sequence[Any], Any],
) -> TicketMutationResult:
    ticket_id_int = ensure_positive_int(ticket_id, "ticket_id")
    normalized = normalize_actor_entries(
        ticket_id_int,
        groups,
        actor_id_key="groups_id",
        item_id_field="tickets_id",
        entry_name="groups",
    )
    payload_to_send = compact_payload(normalized)

    with open_handler() as handler:
        response = handler.add_items("Group_Ticket", payload_to_send)

    return TicketMutationResult(
        action="assign_ticket_groups",
        ticket_id=ticket_id_int,
        description=f"Assigned {len(normalized)} group(s) to ticket {ticket_id_int}",
        payload=payload_to_send,
        response=response,
    )
