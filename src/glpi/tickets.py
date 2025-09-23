"""Helpers for interacting with GLPI tickets."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

from glpi_client import RequestHandler, ResponseRange, SortOrder

from common.config import get_config

config = get_config()
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

_ENUM_FIELDS = {
    "status": STATUS_LABELS,
    "priority": PRIORITY_LABELS,
    "impact": IMPACT_LABELS,
    "urgency": URGENCY_LABELS,
}


def _normalize_label_key(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def _ensure_int(value: Any, field_name: str) -> int:
    if value is None:
        raise ValueError(f"{field_name} is required")
    try:
        return int(value)
    except (TypeError, ValueError) as err:
        raise ValueError(f"{field_name} must be an integer") from err


def _ensure_positive_int(value: Any, field_name: str) -> int:
    int_value = _ensure_int(value, field_name)
    if int_value <= 0:
        raise ValueError(f"{field_name} must be greater than zero")
    return int_value


def _ensure_non_empty_text(value: Any, field_name: str) -> str:
    if value is None:
        raise ValueError(f"{field_name} is required")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} cannot be empty")
    return text


def _ensure_optional_dict(value: Any, field_name: str) -> Optional[Dict[str, Any]]:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    raise ValueError(f"{field_name} must be an object if provided")


def _prepare_bool_flag(value: Any) -> Any:
    if isinstance(value, bool):
        return 1 if value else 0
    if isinstance(value, (int, float)):
        return 1 if int(value) else 0
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "y"}:
            return 1
        if lowered in {"0", "false", "no", "n"}:
            return 0
    return value


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


def _prepare_ticket(ticket: Dict[str, Any], fields: Sequence[str]) -> Dict[str, Any]:
    prepared: Dict[str, Any] = {}
    for field in fields:
        value = ticket.get(field)
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
        if self.response_range is not None:
            table_lines.append("")
            table_lines.append(f"Range: {self.response_range}")
        return "\n".join(table_lines)


@dataclass
class TicketCreationResult:
    payload: Dict[str, Any]
    response: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return {"payload": self.payload, "response": self.response}

    def summary(self) -> str:
        ticket_id: Optional[Any] = None
        name = self.payload.get("name")
        response_obj = self.response
        if isinstance(response_obj, dict):
            ticket_id = response_obj.get("id") or response_obj.get("ID")
            name = response_obj.get("name", name)
        elif isinstance(response_obj, list) and response_obj:
            first = response_obj[0]
            if isinstance(first, dict):
                ticket_id = first.get("id") or first.get("ID")
                name = first.get("name", name)
        ticket_id_str = str(ticket_id) if ticket_id is not None else "unknown"
        return f"Ticket created (id={ticket_id_str}): {name}"


@dataclass
class TicketMutationResult:
    action: str
    ticket_id: int
    description: str
    payload: Any
    response: Any

    def as_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            "ticket_id": self.ticket_id,
            "description": self.description,
            "payload": self.payload,
            "response": self.response,
        }

    def summary(self) -> str:
        return self.description


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


def all_tickets(
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
    """Retrieve tickets from GLPI with a configurable presentation."""

    ticket_list = fetch_tickets(
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
        return ticket_list.to_table(selected_fields)
    if output == "raw":
        return ticket_list.items

    return ticket_list.as_dict(selected_fields)


def _normalize_actor_entries(
    ticket_id: int,
    entries: Union[Dict[str, Any], Sequence[Any], Any],
    *,
    actor_id_key: str,
    item_id_field: str,
    entry_name: str,
) -> List[Dict[str, Any]]:
    if entries is None:
        raise ValueError(f"{entry_name} are required")
    if isinstance(entries, dict) or not isinstance(entries, Iterable):
        raw_entries: List[Any] = [entries]
    else:
        raw_entries = list(entries)
        if not raw_entries:
            raise ValueError(f"{entry_name} cannot be empty")

    normalized: List[Dict[str, Any]] = []
    actor_alt_keys = {
        actor_id_key,
        actor_id_key.rstrip("s"),
        actor_id_key.replace("_id", ""),
        actor_id_key.replace("_", ""),
    }
    for index, entry in enumerate(raw_entries, start=1):
        current: Dict[str, Any]
        if isinstance(entry, (int, float, str)) and not isinstance(entry, bool):
            actor_id = _ensure_positive_int(entry, f"{entry_name[:-1]}_id")
            current = {actor_id_key: actor_id}
        elif isinstance(entry, dict):
            working = {k: v for k, v in entry.items() if v is not None}
            actor_id_value = None
            for key in actor_alt_keys:
                if key in working:
                    actor_id_value = working.pop(key)
                    break
            if actor_id_value is None:
                raise ValueError(
                    f"{actor_id_key} is required for element #{index} in {entry_name}"
                )
            actor_id = _ensure_positive_int(actor_id_value, actor_id_key)
            current = working
            current[actor_id_key] = actor_id
        else:
            raise ValueError(
                f"Unsupported value for {entry_name[:-1]} #{index}: {entry}"
            )

        current[item_id_field] = ticket_id
        if "type" in current and current["type"] is not None:
            current["type"] = _ensure_int(current["type"], "type")
        for flag_key in ("use_notification", "is_dynamic", "is_manager"):
            if flag_key in current:
                current[flag_key] = _prepare_bool_flag(current[flag_key])
        normalized.append(current)
    return normalized


def assign_ticket_users(
    ticket_id: Any,
    users: Union[Dict[str, Any], Sequence[Any], Any],
) -> TicketMutationResult:
    ticket_id_int = _ensure_positive_int(ticket_id, "ticket_id")
    normalized = _normalize_actor_entries(
        ticket_id_int,
        users,
        actor_id_key="users_id",
        item_id_field="tickets_id",
        entry_name="users",
    )
    payload_to_send: Union[Dict[str, Any], List[Dict[str, Any]]]
    if len(normalized) == 1:
        payload_to_send = normalized[0]
    else:
        payload_to_send = normalized

    with RequestHandler(config.url, config.app_token, config.user_token) as handler:
        response = handler.add_items("Ticket_User", payload_to_send)

    description = f"Assigned {len(normalized)} user(s) to ticket {ticket_id_int}"
    return TicketMutationResult(
        action="assign_ticket_users",
        ticket_id=ticket_id_int,
        description=description,
        payload=payload_to_send,
        response=response,
    )


def assign_ticket_groups(
    ticket_id: Any,
    groups: Union[Dict[str, Any], Sequence[Any], Any],
) -> TicketMutationResult:
    ticket_id_int = _ensure_positive_int(ticket_id, "ticket_id")
    normalized = _normalize_actor_entries(
        ticket_id_int,
        groups,
        actor_id_key="groups_id",
        item_id_field="tickets_id",
        entry_name="groups",
    )
    payload_to_send: Union[Dict[str, Any], List[Dict[str, Any]]]
    if len(normalized) == 1:
        payload_to_send = normalized[0]
    else:
        payload_to_send = normalized

    with RequestHandler(config.url, config.app_token, config.user_token) as handler:
        response = handler.add_items("Group_Ticket", payload_to_send)

    description = f"Assigned {len(normalized)} group(s) to ticket {ticket_id_int}"
    return TicketMutationResult(
        action="assign_ticket_groups",
        ticket_id=ticket_id_int,
        description=description,
        payload=payload_to_send,
        response=response,
    )


def add_followup(
    ticket_id: Any,
    content: Any,
    *,
    is_private: bool | Any = False,
    additional_fields: Optional[Dict[str, Any]] = None,
) -> TicketMutationResult:
    ticket_id_int = _ensure_positive_int(ticket_id, "ticket_id")
    comment = _ensure_non_empty_text(content, "content")
    payload: Dict[str, Any] = {
        "itemtype": "Ticket",
        "items_id": ticket_id_int,
        "content": comment,
    }
    private_flag = _prepare_bool_flag(is_private)
    if private_flag is not None:
        payload["is_private"] = private_flag

    extras = _ensure_optional_dict(additional_fields, "additional_fields")
    if extras:
        payload.update({k: v for k, v in extras.items() if v is not None})

    with RequestHandler(config.url, config.app_token, config.user_token) as handler:
        response = handler.add_items("ITILFollowup", payload)

    description = f"Added follow-up to ticket {ticket_id_int}"
    return TicketMutationResult(
        action="add_ticket_comment",
        ticket_id=ticket_id_int,
        description=description,
        payload=payload,
        response=response,
    )


def add_solution(
    ticket_id: Any,
    content: Any,
    *,
    solution_type_id: Any = None,
    additional_fields: Optional[Dict[str, Any]] = None,
) -> TicketMutationResult:
    ticket_id_int = _ensure_positive_int(ticket_id, "ticket_id")
    solution_text = _ensure_non_empty_text(content, "content")
    payload: Dict[str, Any] = {
        "itemtype": "Ticket",
        "items_id": ticket_id_int,
        "content": solution_text,
    }
    if solution_type_id is not None:
        payload["solutiontypes_id"] = _ensure_positive_int(
            solution_type_id, "solution_type_id"
        )

    extras = _ensure_optional_dict(additional_fields, "additional_fields")
    if extras:
        payload.update({k: v for k, v in extras.items() if v is not None})

    with RequestHandler(config.url, config.app_token, config.user_token) as handler:
        response = handler.add_items("ITILSolution", payload)

    description = f"Added solution to ticket {ticket_id_int}"
    return TicketMutationResult(
        action="add_ticket_solution",
        ticket_id=ticket_id_int,
        description=description,
        payload=payload,
        response=response,
    )


def create_ticket(
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
) -> TicketCreationResult:
    """Create a ticket in GLPI and return the payload and response."""

    if not name or not name.strip():
        raise ValueError("name is required to create a ticket")

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

    extras = _ensure_optional_dict(additional_fields, "additional_fields")
    if extras:
        for key, value in extras.items():
            if value is None:
                continue
            payload[key] = value

    with RequestHandler(config.url, config.app_token, config.user_token) as handler:
        response = handler.create_ticket(**payload)

    return TicketCreationResult(payload=payload, response=response)
