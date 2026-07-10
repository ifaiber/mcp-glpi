"""Ticket solution operations."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..shared import ensure_non_empty_text, ensure_positive_int, merge_non_null_values
from .common import TicketMutationResult, open_handler


def add_solution(
    ticket_id: Any,
    content: Any,
    *,
    solution_type_id: Any = None,
    additional_fields: Optional[Dict[str, Any]] = None,
) -> TicketMutationResult:
    ticket_id_int = ensure_positive_int(ticket_id, "ticket_id")
    solution_text = ensure_non_empty_text(content, "content")
    payload: Dict[str, Any] = {
        "itemtype": "Ticket",
        "items_id": ticket_id_int,
        "content": solution_text,
    }
    if solution_type_id is not None:
        payload["solutiontypes_id"] = ensure_positive_int(solution_type_id, "solution_type_id")

    merge_non_null_values(payload, additional_fields)

    with open_handler() as handler:
        response = handler.add_items("ITILSolution", payload)

    return TicketMutationResult(
        action="add_ticket_solution",
        ticket_id=ticket_id_int,
        description=f"Added solution to ticket {ticket_id_int}",
        payload=payload,
        response=response,
    )
