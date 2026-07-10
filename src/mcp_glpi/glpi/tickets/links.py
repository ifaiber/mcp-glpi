"""Ticket relation operations."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..shared import ensure_positive_int, merge_non_null_values, prepare_bool_flag
from .common import TicketMutationResult, open_handler


def link_change(
    ticket_id: Any,
    change_id: Any,
    *,
    additional_fields: Optional[Dict[str, Any]] = None,
) -> TicketMutationResult:
    ticket_id_int = ensure_positive_int(ticket_id, "ticket_id")
    change_id_int = ensure_positive_int(change_id, "change_id")

    payload: Dict[str, Any] = {
        "tickets_id": ticket_id_int,
        "changes_id": change_id_int,
    }
    merge_non_null_values(payload, additional_fields)

    with open_handler() as handler:
        response = handler.add_items("Change_Ticket", payload)

    return TicketMutationResult(
        action="link_ticket_change",
        ticket_id=ticket_id_int,
        description=f"Linked ticket {ticket_id_int} to change {change_id_int}",
        payload=payload,
        response=response,
    )


def unlink_change(
    ticket_id: Any,
    link_id: Any,
    *,
    purge: bool | Any = False,
    keep_history: bool | Any = True,
) -> TicketMutationResult:
    ticket_id_int = ensure_positive_int(ticket_id, "ticket_id")
    link_id_int = ensure_positive_int(link_id, "link_id")
    purge_flag = bool(prepare_bool_flag(purge))
    keep_history_flag = bool(prepare_bool_flag(keep_history))

    with open_handler() as handler:
        response = handler.delete_items(
            "Change_Ticket",
            [link_id_int],
            purge=purge_flag,
            log=keep_history_flag,
        )

    return TicketMutationResult(
        action="unlink_ticket_change",
        ticket_id=ticket_id_int,
        description=f"Unlinked ticket {ticket_id_int} from change relation {link_id_int}",
        payload={"link_id": link_id_int, "purge": purge_flag, "keep_history": keep_history_flag},
        response=response,
    )
