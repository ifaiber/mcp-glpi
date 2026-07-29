"""Change update operations."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..shared import (
    ensure_positive_int,
    normalize_update_fields,
    switch_active_entity,
    switch_active_profile,
)
from .common import ENUM_FIELDS, ChangeMutationResult, open_handler


def update_change(
    change_id: Any,
    fields: Dict[str, Any],
    *,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
) -> ChangeMutationResult:
    change_id_int = ensure_positive_int(change_id, "change_id")
    sanitized = normalize_update_fields(fields, ENUM_FIELDS)
    payload = {"id": change_id_int, **sanitized}

    with open_handler() as handler:
        switch_active_profile(handler, profile_id)
        switch_active_entity(handler, entity_id)
        response = handler.update_items("Change", [payload])

    return ChangeMutationResult(
        action="change_update",
        change_id=change_id_int,
        description=f"Updated change {change_id_int}",
        payload=payload,
        response=response,
    )
