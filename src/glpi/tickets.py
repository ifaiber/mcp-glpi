"""Helpers for interacting with GLPI tickets."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from glpi_client import RequestHandler, ResponseRange, SortOrder

from common.config import get_config

config = get_config()

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

DEFAULT_FIELDS: Sequence[str] = (
    "id",
    "name",
    "status",
    "priority",
    "date",
    "date_mod",
    "closedate",
)


def _translate_status(value: Any) -> Any:
    try:
        return STATUS_LABELS[int(value)]
    except (TypeError, ValueError, KeyError):
        return value


def _translate_priority(value: Any) -> Any:
    try:
        return PRIORITY_LABELS[int(value)]
    except (TypeError, ValueError, KeyError):
        return value


def _prepare_ticket(ticket: Dict[str, Any], fields: Sequence[str]) -> Dict[str, Any]:
    prepared: Dict[str, Any] = {}
    for field in fields:
        value = ticket.get(field)
        if field == "status":
            value = _translate_status(value)
        elif field == "priority":
            value = _translate_priority(value)
        prepared[field] = value
    return prepared


def _range_to_dict(range_: Optional[ResponseRange]) -> Optional[Dict[str, int]]:
    if range_ is None:
        return None
    return {
        "start": range_.start,
        "end": range_.end,
        "count": range_.count,
        "max": range_.max,
    }


@dataclass
class TicketList:
    items: List[Dict[str, Any]]
    response_range: Optional[ResponseRange]

    def as_dict(self, fields: Sequence[str] = DEFAULT_FIELDS) -> Dict[str, Any]:
        return {
            "tickets": [_prepare_ticket(item, fields) for item in self.items],
            "range": _range_to_dict(self.response_range),
        }

    def to_table(self, fields: Sequence[str] = DEFAULT_FIELDS) -> str:
        if not self.items:
            return "No tickets found."
        prepared = [_prepare_ticket(item, fields) for item in self.items]
        widths = {
            field: max(
                len(str(field)),
                max(len(str(row.get(field, "") or "")) for row in prepared),
            )
            for field in fields
        }
        header = " | ".join(field.upper().ljust(widths[field]) for field in fields)
        separator = "-+-".join("-" * widths[field] for field in fields)
        rows = [
            " | ".join(str(row.get(field, "") or "").ljust(widths[field]) for field in fields)
            for row in prepared
        ]
        table_lines = [header, separator, *rows]
        if self.response_range is not None:
            table_lines.append("")
            table_lines.append(f"Range: {self.response_range}")
        return "\n".join(table_lines)


def fetch_tickets(
    limit: Optional[int] = 20,
    offset: int = 0,
    sort_by: str = "date_mod",
    order: Union[SortOrder, str] = SortOrder.Descending,
    filters: Optional[Dict[str, str]] = None,
    expand_dropdowns: bool = False,
    include_deleted: bool = False,
) -> TicketList:
    order_enum = SortOrder(order) if isinstance(order, str) else order
    range_tuple: Optional[Tuple[int, int]] = None
    if limit is not None and limit > 0:
        range_tuple = (offset, offset + limit - 1)
    filters_to_use = filters or None
    with RequestHandler(config.url, config.app_token, config.user_token) as handler:
        items = handler.get_many_items(
            "Ticket",
            expand_dropdowns=expand_dropdowns,
            sort_by=sort_by,
            order=order_enum,
            range_=range_tuple,
            filter_by=filters_to_use,
            is_deleted=include_deleted,
        )
        response_range = getattr(handler, "response_range", None)
    return TicketList(items=items, response_range=response_range)


def list_tickets_as_table(
    limit: Optional[int] = 20,
    offset: int = 0,
    sort_by: str = "date_mod",
    order: Union[SortOrder, str] = SortOrder.Descending,
    filters: Optional[Dict[str, str]] = None,
    expand_dropdowns: bool = False,
    include_deleted: bool = False,
    fields: Sequence[str] = DEFAULT_FIELDS,
) -> str:
    ticket_list = fetch_tickets(
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        order=order,
        filters=filters,
        expand_dropdowns=expand_dropdowns,
        include_deleted=include_deleted,
    )
    return ticket_list.to_table(fields)
