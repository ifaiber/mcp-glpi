"""Change relation operations."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..shared import (
    ensure_positive_int,
    merge_non_null_values,
    prepare_bool_flag,
    switch_active_entity,
    switch_active_profile,
)
from .common import ChangeMutationResult, open_handler


def link_ticket(
    change_id: Any,
    ticket_id: Any,
    *,
    additional_fields: Optional[Dict[str, Any]] = None,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
) -> ChangeMutationResult:
    change_id_int = ensure_positive_int(change_id, "change_id")
    ticket_id_int = ensure_positive_int(ticket_id, "ticket_id")

    payload: Dict[str, Any] = {
        "changes_id": change_id_int,
        "tickets_id": ticket_id_int,
    }
    merge_non_null_values(payload, additional_fields)

    with open_handler() as handler:
        switch_active_profile(handler, profile_id)
        switch_active_entity(handler, entity_id)
        response = handler.add_items("Change_Ticket", payload)

    return ChangeMutationResult(
        action="change_ticket_link",
        change_id=change_id_int,
        description=f"Linked change {change_id_int} to ticket {ticket_id_int}",
        payload=payload,
        response=response,
    )


def unlink_ticket(
    change_id: Any,
    link_id: Any,
    *,
    purge: bool | Any = False,
    keep_history: bool | Any = True,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
) -> ChangeMutationResult:
    change_id_int = ensure_positive_int(change_id, "change_id")
    link_id_int = ensure_positive_int(link_id, "link_id")
    purge_flag = bool(prepare_bool_flag(purge))
    keep_history_flag = bool(prepare_bool_flag(keep_history))

    with open_handler() as handler:
        switch_active_profile(handler, profile_id)
        switch_active_entity(handler, entity_id)
        response = handler.delete_items(
            "Change_Ticket",
            [link_id_int],
            purge=purge_flag,
            log=keep_history_flag,
        )

    return ChangeMutationResult(
        action="change_ticket_unlink",
        change_id=change_id_int,
        description=f"Unlinked change {change_id_int} from ticket relation {link_id_int}",
        payload={"link_id": link_id_int, "purge": purge_flag, "keep_history": keep_history_flag},
        response=response,
    )
