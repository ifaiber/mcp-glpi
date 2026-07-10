"""Change update operations."""

from __future__ import annotations

from typing import Any, Dict

from ..shared import ensure_positive_int, normalize_update_fields
from .common import ENUM_FIELDS, ChangeMutationResult, open_handler


def update_change(
    change_id: Any,
    fields: Dict[str, Any],
) -> ChangeMutationResult:
    change_id_int = ensure_positive_int(change_id, "change_id")
    sanitized = normalize_update_fields(fields, ENUM_FIELDS)
    payload = {"id": change_id_int, **sanitized}

    with open_handler() as handler:
        response = handler.update_items("Change", [payload])

    return ChangeMutationResult(
        action="update_change",
        change_id=change_id_int,
        description=f"Updated change {change_id_int}",
        payload=payload,
        response=response,
    )
