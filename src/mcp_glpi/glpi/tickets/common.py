"""Shared ticket-specific helpers and exported result types."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Sequence

from glpi_client import RequestHandler as GLPIRequestHandler

from ...common.config import get_config
from ..shared import EntityCreationResult, EntityList, EntityMutationResult, normalize_enum_value, translate_enum

logger = logging.getLogger(__name__)

STATUS_LABELS = {
    1: "New",
    2: "Assigned",
    3: "Planned",
    4: "Pending",
    5: "Solved",
    6: "Closed",
}

PRIORITY_LABELS = {
    1: "Very high",
    2: "High",
    3: "Medium",
    4: "Low",
    5: "Very low",
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

DEFAULT_FIELDS: Sequence[str] = (
    "id",
    "name",
    "status",
    "priority",
    "impact",
    "urgency",
    "date",
    "date_mod",
    "closedate",
)

ENUM_FIELDS = {
    "status": STATUS_LABELS,
    "priority": PRIORITY_LABELS,
    "impact": IMPACT_LABELS,
    "urgency": URGENCY_LABELS,
}


def open_handler():
    from . import RequestHandler

    config = get_config()
    return RequestHandler(config.url, config.app_token, config.user_token, False)


def prepare_ticket(ticket: Dict[str, Any], fields: Sequence[str]) -> Dict[str, Any]:
    prepared: Dict[str, Any] = {}
    for field in fields:
        value = ticket.get(field)
        labels = ENUM_FIELDS.get(field)
        if labels:
            value = _translate_enum(value, labels)
        prepared[field] = value
    return prepared


def _normalize_enum_value(value: Any, labels: Dict[int, str], field_name: str) -> Optional[int]:
    return normalize_enum_value(value, labels, field_name)


def _translate_enum(value: Any, labels: Dict[int, str]) -> Any:
    return translate_enum(value, labels)


class TicketList(EntityList):
    def __init__(self, items, response_range):
        super().__init__(
            item_key="tickets",
            items=items,
            response_range=response_range,
            prepare_item=prepare_ticket,
        )

    def as_dict(self, fields: Sequence[str] = DEFAULT_FIELDS) -> Dict[str, Any]:
        return super().as_dict(fields)

    def to_table(self, fields: Sequence[str] = DEFAULT_FIELDS) -> str:
        return super().to_table(fields)


class TicketCreationResult(EntityCreationResult):
    def __init__(self, payload: Dict[str, Any], response: Dict[str, Any]):
        super().__init__(entity_label="Ticket", payload=payload, response=response)


class TicketMutationResult(EntityMutationResult):
    def __init__(
        self,
        action: str,
        ticket_id: int,
        description: str,
        payload: Any,
        response: Any,
    ):
        super().__init__(
            action=action,
            entity_id_field="ticket_id",
            entity_id=ticket_id,
            description=description,
            payload=payload,
            response=response,
        )


RequestHandler = GLPIRequestHandler
