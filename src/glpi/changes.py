"""Helpers for interacting with GLPI change records."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple, Union

from glpi_client import RequestHandler, ResponseRange, SortOrder

from common.config import get_config

config = get_config()
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

_ENUM_FIELDS = {
    "status": STATUS_LABELS,
    "impact": IMPACT_LABELS,
    "priority": PRIORITY_LABELS,
    "urgency": URGENCY_LABELS,
}


def _normalize_label_key(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _normalize_enum_value(value: Any, labels: Dict[int, str], field_name: str) -> Optional[int]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        candidate = int(value)
        if candidate in labels:
            return candidate
        raise ValueError(f"Unknown {field_name}: {value}")
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return None
        if stripped.isdigit():
            candidate = int(stripped)
            if candidate in labels:
                return candidate
        normalized = _normalize_label_key(stripped)
        for code, label in labels.items():
            if normalized in {_normalize_label_key(label), str(code)}:
                return code
        raise ValueError(f"Unknown {field_name}: {value}")
    raise ValueError(f"Unsupported value for {field_name}: {value}")


def _translate_enum(value: Any, labels: Dict[int, str]) -> Any:
    try:
        return labels[int(value)]
    except (TypeError, ValueError, KeyError):
        return value


def _prepare_change(change: Dict[str, Any], fields: Sequence[str]) -> Dict[str, Any]:
    prepared: Dict[str, Any] = {}
    for field in fields:
        value = change.get(field)
        labels = _ENUM_FIELDS.get(field)
        if labels:
            value = _translate_enum(value, labels)
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


@dataclass
class ChangeCreationResult:
    payload: Dict[str, Any]
    response: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return {"payload": self.payload, "response": self.response}

    def summary(self) -> str:
        change_id: Optional[Any] = None
        name = self.payload.get("name")
        response_obj = self.response
        if isinstance(response_obj, dict):
            change_id = response_obj.get("id") or response_obj.get("ID")
            name = response_obj.get("name", name)
        elif isinstance(response_obj, list) and response_obj:
            first = response_obj[0]
            if isinstance(first, dict):
                change_id = first.get("id") or first.get("ID")
                name = first.get("name", name)
        change_id_str = str(change_id) if change_id is not None else "unknown"
        return f"Change created (id={change_id_str}): {name}"


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
    additional_fields: Optional[Dict[str, Any]] = None,
) -> ChangeCreationResult:
    """Create a change in GLPI and return the payload and response."""

    if not name or not name.strip():
        raise ValueError("name is required to create a change")

    payload: Dict[str, Any] = {
        "name": name.strip(),
        "content": content or "",
    }

    try:
        if status is not None:
            payload["status"] = _normalize_enum_value(status, STATUS_LABELS, "status")
        if impact is not None:
            payload["impact"] = _normalize_enum_value(impact, IMPACT_LABELS, "impact")
        if priority is not None:
            payload["priority"] = _normalize_enum_value(priority, PRIORITY_LABELS, "priority")
        if urgency is not None:
            payload["urgency"] = _normalize_enum_value(urgency, URGENCY_LABELS, "urgency")
    except ValueError as exc:
        logger.debug("Enum normalization failed: %s", exc)
        raise

    if category_id is not None:
        payload["itilcategories_id"] = int(category_id)
    if entity_id is not None:
        payload["entities_id"] = int(entity_id)

    if additional_fields:
        for key, value in additional_fields.items():
            if value is None:
                continue
            payload[key] = value

    with RequestHandler(config.url, config.app_token, config.user_token) as handler:
        response = handler.create_change(**payload)

    return ChangeCreationResult(payload=payload, response=response)
