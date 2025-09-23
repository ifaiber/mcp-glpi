"""Helpers for interacting with GLPI change records."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from glpi_client import RequestHandler, ResponseRange, SortOrder

from common.config import get_config

config = get_config()

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


def _translate(value: Any, mapping: Dict[int, str]) -> Any:
    try:
        return mapping[int(value)]
    except (TypeError, ValueError, KeyError):
        return value


def _prepare_change(change: Dict[str, Any], fields: Sequence[str]) -> Dict[str, Any]:
    prepared: Dict[str, Any] = {}
    for field in fields:
        value = change.get(field)
        if field == "status":
            value = _translate(value, STATUS_LABELS)
        elif field == "impact":
            value = _translate(value, IMPACT_LABELS)
        elif field == "urgency":
            value = _translate(value, URGENCY_LABELS)
        elif field == "priority":
            value = _translate(value, PRIORITY_LABELS)
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
class ChangeList:
    items: List[Dict[str, Any]]
    response_range: Optional[ResponseRange]

    def as_dict(self, fields: Sequence[str] = DEFAULT_FIELDS) -> Dict[str, Any]:
        return {
            "changes": [_prepare_change(item, fields) for item in self.items],
            "range": _range_to_dict(self.response_range),
        }

    def to_table(self, fields: Sequence[str] = DEFAULT_FIELDS) -> str:
        if not self.items:
            return "No changes found."
        prepared = [_prepare_change(item, fields) for item in self.items]
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


def fetch_changes(
    limit: Optional[int] = 20,
    offset: int = 0,
    sort_by: str = "date_mod",
    order: Union[SortOrder, str] = SortOrder.Descending,
    filters: Optional[Dict[str, str]] = None,
    expand_dropdowns: bool = False,
    include_deleted: bool = False,
) -> ChangeList:
    order_enum = SortOrder(order) if isinstance(order, str) else order
    range_tuple: Optional[Tuple[int, int]] = None
    if limit is not None and limit > 0:
        range_tuple = (offset, offset + limit - 1)
    filters_to_use = filters or None
    with RequestHandler(config.url, config.app_token, config.user_token) as handler:
        items = handler.get_many_items(
            "Change",
            expand_dropdowns=expand_dropdowns,
            sort_by=sort_by,
            order=order_enum,
            range_=range_tuple,
            filter_by=filters_to_use,
            is_deleted=include_deleted,
        )
        response_range = getattr(handler, "response_range", None)
    return ChangeList(items=items, response_range=response_range)


def list_changes_as_table(
    limit: Optional[int] = 20,
    offset: int = 0,
    sort_by: str = "date_mod",
    order: Union[SortOrder, str] = SortOrder.Descending,
    filters: Optional[Dict[str, str]] = None,
    expand_dropdowns: bool = False,
    include_deleted: bool = False,
    fields: Sequence[str] = DEFAULT_FIELDS,
) -> str:
    change_list = fetch_changes(
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        order=order,
        filters=filters,
        expand_dropdowns=expand_dropdowns,
        include_deleted=include_deleted,
    )
    return change_list.to_table(fields)


def all_changes(
    limit: Optional[int] = 20,
    offset: int = 0,
    sort_by: str = "date_mod",
    order: Union[SortOrder, str] = SortOrder.Descending,
    filters: Optional[Dict[str, str]] = None,
    expand_dropdowns: bool = False,
    include_deleted: bool = False,
    output: str = "dict",
    fields: Optional[Sequence[str]] = None,
):
    """Retrieve changes from GLPI with a configurable presentation."""

    change_list = fetch_changes(
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        order=order,
        filters=filters,
        expand_dropdowns=expand_dropdowns,
        include_deleted=include_deleted,
    )

    selected_fields = fields or DEFAULT_FIELDS

    if output == "table":
        return change_list.to_table(selected_fields)
    if output == "raw":
        return change_list.items

    return change_list.as_dict(selected_fields)
