"""Ticket delete operations."""

from __future__ import annotations

from typing import Any

from ..shared import ensure_positive_int, prepare_bool_flag
from .common import TicketMutationResult, open_handler


def delete_ticket(
    ticket_id: Any,
    *,
    purge: bool | Any = False,
    keep_history: bool | Any = True,
) -> TicketMutationResult:
    ticket_id_int = ensure_positive_int(ticket_id, "ticket_id")
    purge_flag = bool(prepare_bool_flag(purge))
    keep_history_flag = bool(prepare_bool_flag(keep_history))

    with open_handler() as handler:
        response = handler.delete_items(
            "Ticket",
            [ticket_id_int],
            purge=purge_flag,
            log=keep_history_flag,
        )

    return TicketMutationResult(
        action="delete_ticket",
        ticket_id=ticket_id_int,
        description=f"Deleted ticket {ticket_id_int}",
        payload={"ticket_id": ticket_id_int, "purge": purge_flag, "keep_history": keep_history_flag},
        response=response,
    )
