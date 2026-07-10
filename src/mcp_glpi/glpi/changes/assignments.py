"""Change actor assignment operations."""

from __future__ import annotations

from typing import Any, Dict, Sequence, Union

from ..shared import compact_payload, ensure_positive_int, normalize_actor_entries
from .common import ChangeMutationResult, open_handler


def assign_change_users(
    change_id: Any,
    users: Union[Dict[str, Any], Sequence[Any], Any],
) -> ChangeMutationResult:
    change_id_int = ensure_positive_int(change_id, "change_id")
    normalized = normalize_actor_entries(
        change_id_int,
        users,
        actor_id_key="users_id",
        item_id_field="changes_id",
        entry_name="users",
    )
    payload_to_send = compact_payload(normalized)

    with open_handler() as handler:
        response = handler.add_items("Change_User", payload_to_send)

    return ChangeMutationResult(
        action="assign_change_users",
        change_id=change_id_int,
        description=f"Assigned {len(normalized)} user(s) to change {change_id_int}",
        payload=payload_to_send,
        response=response,
    )


def assign_change_groups(
    change_id: Any,
    groups: Union[Dict[str, Any], Sequence[Any], Any],
) -> ChangeMutationResult:
    change_id_int = ensure_positive_int(change_id, "change_id")
    normalized = normalize_actor_entries(
        change_id_int,
        groups,
        actor_id_key="groups_id",
        item_id_field="changes_id",
        entry_name="groups",
    )
    payload_to_send = compact_payload(normalized)

    with open_handler() as handler:
        response = handler.add_items("Change_Group", payload_to_send)

    return ChangeMutationResult(
        action="assign_change_groups",
        change_id=change_id_int,
        description=f"Assigned {len(normalized)} group(s) to change {change_id_int}",
        payload=payload_to_send,
        response=response,
    )
