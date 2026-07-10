"""Change creation operations."""

from __future__ import annotations

from typing import Dict, Optional, Union

from ..shared import merge_non_null_values, normalize_enum_value
from .common import (
    IMPACT_LABELS,
    PRIORITY_LABELS,
    STATUS_LABELS,
    URGENCY_LABELS,
    ChangeCreationResult,
    logger,
    open_handler,
)


def create_change(
    name: str,
    content: str = "",
    *,
    status: Optional[Union[int, str]] = None,
    impact: Optional[Union[int, str]] = None,
    priority: Optional[Union[int, str]] = None,
    urgency: Optional[Union[int, str]] = None,
    category_id: Optional[int] = None,
    entity_id: Optional[int] = None,
    additional_fields: Optional[Dict[str, object]] = None,
) -> ChangeCreationResult:
    if not name or not name.strip():
        raise ValueError("name is required to create a change")

    payload: Dict[str, object] = {
        "name": name.strip(),
        "content": content or "",
    }

    try:
        if status is not None:
            payload["status"] = normalize_enum_value(status, STATUS_LABELS, "status")
        if impact is not None:
            payload["impact"] = normalize_enum_value(impact, IMPACT_LABELS, "impact")
        if priority is not None:
            payload["priority"] = normalize_enum_value(priority, PRIORITY_LABELS, "priority")
        if urgency is not None:
            payload["urgency"] = normalize_enum_value(urgency, URGENCY_LABELS, "urgency")
    except ValueError as exc:
        logger.debug("Enum normalization failed: %s", exc)
        raise

    if category_id is not None:
        payload["itilcategories_id"] = int(category_id)
    if entity_id is not None:
        payload["entities_id"] = int(entity_id)

    merge_non_null_values(payload, additional_fields)

    with open_handler() as handler:
        response = handler.create_change(**payload)

    return ChangeCreationResult(payload=payload, response=response)
