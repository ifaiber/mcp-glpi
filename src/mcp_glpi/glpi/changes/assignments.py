"""Change actor assignment operations."""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Union

from ..shared import (
    compact_payload,
    ensure_positive_int,
    normalize_actor_entries,
    switch_active_entity,
    switch_active_profile,
)
from .common import ChangeMutationResult, open_handler


def assign_change_users(
    change_id: Any,
    users: Union[Dict[str, Any], Sequence[Any], Any],
    *,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
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
        switch_active_profile(handler, profile_id)
        switch_active_entity(handler, entity_id)
        response = handler.add_items("Change_User", payload_to_send)

    return ChangeMutationResult(
        action="change_user_assign",
        change_id=change_id_int,
        description=f"Assigned {len(normalized)} user(s) to change {change_id_int}",
        payload=payload_to_send,
        response=response,
    )


def assign_change_groups(
    change_id: Any,
    groups: Union[Dict[str, Any], Sequence[Any], Any],
    *,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
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
        switch_active_profile(handler, profile_id)
        switch_active_entity(handler, entity_id)
        response = handler.add_items("Change_Group", payload_to_send)

    return ChangeMutationResult(
        action="change_group_assign",
        change_id=change_id_int,
        description=f"Assigned {len(normalized)} group(s) to change {change_id_int}",
        payload=payload_to_send,
        response=response,
    )
