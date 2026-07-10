"""Shared change-specific helpers and exported result types."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Sequence

from glpi_client import RequestHandler as GLPIRequestHandler

from ...common.config import get_config
from ..shared import EntityCreationResult, EntityList, EntityMutationResult, normalize_enum_value, translate_enum

logger = logging.getLogger(__name__)

STATUS_LABELS = {
    1: "New",
    2: "Assessment",
    3: "Approval",
    4: "Planning",
    5: "Implementation",
    6: "Review",
    7: "Closed",
}

IMPACT_LABELS = {
    1: "High",
    2: "Medium",
    3: "Low",
}

URGENCY_LABELS = {
    1: "High",
    2: "Medium",
    3: "Low",
}

PRIORITY_LABELS = {
    1: "Very high",
    2: "High",
    3: "Medium",
    4: "Low",
    5: "Very low",
}

DEFAULT_FIELDS: Sequence[str] = (
    "id",
    "name",
    "status",
    "impact",
    "priority",
    "urgency",
    "date_mod",
)

ENUM_FIELDS = {
    "status": STATUS_LABELS,
    "impact": IMPACT_LABELS,
    "priority": PRIORITY_LABELS,
    "urgency": URGENCY_LABELS,
}


def open_handler():
    from . import RequestHandler

    config = get_config()
    return RequestHandler(config.url, config.app_token, config.user_token, False)


def prepare_change(change: Dict[str, Any], fields: Sequence[str]) -> Dict[str, Any]:
    prepared: Dict[str, Any] = {}
    for field in fields:
        value = change.get(field)
        labels = ENUM_FIELDS.get(field)
        if labels:
            value = _translate_enum(value, labels)
        prepared[field] = value
    return prepared


def _normalize_enum_value(value: Any, labels: Dict[int, str], field_name: str) -> Optional[int]:
    return normalize_enum_value(value, labels, field_name)


def _translate_enum(value: Any, labels: Dict[int, str]) -> Any:
    return translate_enum(value, labels)


class ChangeList(EntityList):
    def __init__(self, items, response_range):
        super().__init__(
            item_key="changes",
            items=items,
            response_range=response_range,
            prepare_item=prepare_change,
        )

    def as_dict(self, fields: Sequence[str] = DEFAULT_FIELDS) -> Dict[str, Any]:
        return super().as_dict(fields)

    def to_table(self, fields: Sequence[str] = DEFAULT_FIELDS) -> str:
        return super().to_table(fields)


class ChangeCreationResult(EntityCreationResult):
    def __init__(self, payload: Dict[str, Any], response: Dict[str, Any]):
        super().__init__(entity_label="Change", payload=payload, response=response)


class ChangeMutationResult(EntityMutationResult):
    def __init__(
        self,
        action: str,
        change_id: int,
        description: str,
        payload: Any,
        response: Any,
    ):
        super().__init__(
            action=action,
            entity_id_field="change_id",
            entity_id=change_id,
            description=description,
            payload=payload,
            response=response,
        )


RequestHandler = GLPIRequestHandler
