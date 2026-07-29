"""Shared helpers for GLPI entity modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple, Union

from glpi_client import GLPIError, ResponseRange, SortOrder


def normalize_label_key(value: str) -> str:
    return "".join(ch for ch in value.lower() if ch.isalnum())


def ensure_int(value: Any, field_name: str) -> int:
    if value is None:
        raise ValueError(f"{field_name} is required")
    try:
        return int(value)
    except (TypeError, ValueError) as err:
        raise ValueError(f"{field_name} must be an integer") from err


def ensure_positive_int(value: Any, field_name: str) -> int:
    int_value = ensure_int(value, field_name)
    if int_value <= 0:
        raise ValueError(f"{field_name} must be greater than zero")
    return int_value


def ensure_non_negative_int(value: Any, field_name: str) -> int:
    """Like ``ensure_positive_int`` but allows zero.

    GLPI's root entity conventionally has id ``0``, so entity ids must
    accept zero as a valid value; unlike ticket/change/category ids, which
    are never zero in practice.
    """
    int_value = ensure_int(value, field_name)
    if int_value < 0:
        raise ValueError(f"{field_name} must be zero or greater")
    return int_value


def ensure_non_empty_text(value: Any, field_name: str) -> str:
    if value is None:
        raise ValueError(f"{field_name} is required")
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field_name} cannot be empty")
    return text


def ensure_optional_dict(value: Any, field_name: str) -> Optional[Dict[str, Any]]:
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    raise ValueError(f"{field_name} must be an object if provided")


def prepare_bool_flag(value: Any) -> Any:
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


def normalize_enum_value(
    value: Any,
    labels: Dict[int, str],
    field_name: str,
) -> Optional[int]:
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
        normalized = normalize_label_key(stripped)
        for code, label in labels.items():
            if normalized in {normalize_label_key(label), str(code)}:
                return code
        raise ValueError(f"Unknown {field_name}: {value}")
    raise ValueError(f"Unsupported value for {field_name}: {value}")


def translate_enum(value: Any, labels: Dict[int, str]) -> Any:
    try:
        return labels[int(value)]
    except (TypeError, ValueError, KeyError):
        return value


def switch_active_entity(handler: Any, entity_id: Any) -> Optional[int]:
    """Switch the active GLPI entity for the current session, if requested.

    ``entity_id`` is optional everywhere it is accepted: when it is ``None``
    (the default), this is a no-op and the operation proceeds in whatever
    entity GLPI assigned to the session by default. When provided, it must
    resolve to a positive int and is applied via ``changeActiveEntities``
    before the caller's real operation runs, since each ``open_handler()``
    call opens and closes its own GLPI session.
    """
    if entity_id is None:
        return None
    if isinstance(entity_id, str) and not entity_id.strip():
        return None
    entity_id_int = ensure_non_negative_int(entity_id, "entity_id")
    handler.change_active_entity(entity_id_int)
    return entity_id_int


def switch_active_profile(handler: Any, profile_id: Any) -> Optional[int]:
    """Switch the active GLPI profile for the current session, if requested.

    Same optional/no-op semantics as ``switch_active_entity``. Unlike
    entities (whose root has id 0), GLPI profile ids are always positive, so
    ``ensure_positive_int`` is used here.

    Callers that also switch entity via ``switch_active_entity`` should call
    this one FIRST: the active profile determines the user's rights
    (create/read/update bitmask), while the active entity only scopes which
    records are visible/targeted. Which entities are considered "reachable"
    for some GLPI checks can depend on the active profile, so switching
    profile before entity is the safer order.
    """
    if profile_id is None:
        return None
    if isinstance(profile_id, str) and not profile_id.strip():
        return None
    profile_id_int = ensure_positive_int(profile_id, "profile_id")
    handler.change_active_profile(profile_id_int)
    return profile_id_int


def safe_response_range(handler: Any) -> Optional[ResponseRange]:
    """Read ``handler.response_range`` without raising.

    GLPI's sub-item collection endpoints (``/Ticket/{id}/ITILFollowup``,
    ``/Ticket/{id}/ITILSolution``) do not always answer with
    ``Content-Range``/``Accept-Range`` headers (observed empty on requests
    with few results), and the ``response_range`` property raises
    ``GLPIError`` rather than returning ``None`` in that case.
    """
    try:
        return handler.response_range
    except GLPIError:
        return None


def fetch_paginated_items(
    itemtype: str,
    open_handler_fn: Callable[[], Any],
    *,
    limit: Optional[int] = 20,
    offset: int = 0,
    sort_by: Optional[str] = None,
    order: Union[SortOrder, str] = SortOrder.Descending,
    filters: Optional[Dict[str, str]] = None,
    expand_dropdowns: bool = False,
    include_deleted: bool = False,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
) -> Tuple[List[Dict[str, Any]], Optional[ResponseRange]]:
    """Shared ``GET /{itemtype}`` pagination: range math, session lifecycle,
    entity/profile switching. Used by every top-level listing (tickets,
    changes, and the generic itemtype access), which then wrap the returned
    items in their own ``EntityList`` (with domain-specific ``prepare_item``
    and ``item_key``) and call ``.respond(...)`` on it.
    """
    order_enum = SortOrder(order) if isinstance(order, str) else order
    range_tuple = (offset, offset + limit - 1) if limit is not None and limit > 0 else None

    with open_handler_fn() as handler:
        switch_active_profile(handler, profile_id)
        switch_active_entity(handler, entity_id)
        items = handler.get_many_items(
            itemtype,
            expand_dropdowns=expand_dropdowns,
            range_=range_tuple,
            sort_by=sort_by,
            order=order_enum,
            filter_by=filters,
            is_deleted=include_deleted,
        )
        response_range = safe_response_range(handler)

    return items, response_range


def fetch_paginated_subitems(
    itemtype: str,
    item_id: int,
    subtype: str,
    open_handler_fn: Callable[[], Any],
    *,
    limit: Optional[int] = 20,
    offset: int = 0,
    sort_by: Optional[str] = None,
    order: Union[SortOrder, str] = SortOrder.Descending,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
) -> Tuple[List[Dict[str, Any]], Optional[ResponseRange]]:
    """Shared ``GET /{itemtype}/{id}/{subtype}`` pagination: range math,
    session lifecycle, entity/profile switching. Used by every sub-item
    listing (ticket/change follow-ups and solutions, and the generic
    itemtype/subtype access).
    """
    order_enum = SortOrder(order) if isinstance(order, str) else order
    range_tuple = (offset, offset + limit - 1) if limit is not None and limit > 0 else None

    with open_handler_fn() as handler:
        switch_active_profile(handler, profile_id)
        switch_active_entity(handler, entity_id)
        items = handler.get_sub_items(
            itemtype, item_id, subtype,
            range_=range_tuple, sort_by=sort_by, order=order_enum,
        )
        response_range = safe_response_range(handler)

    return items, response_range


def prepare_generic_item(item: Dict[str, Any], fields: Sequence[str]) -> Dict[str, Any]:
    """Project ``fields`` out of ``item`` as-is, with no enum translation.

    Used for sub-items (follow-ups, solutions) that don't have the
    status/priority/impact label mappings tickets and changes have.
    """
    return {field: item.get(field) for field in fields}


def range_to_dict(range_: Optional[ResponseRange]) -> Optional[Dict[str, int]]:
    if range_ is None:
        return None
    return {
        "start": range_.start,
        "end": range_.end,
        "count": range_.count,
        "max": range_.max,
    }


def merge_non_null_values(
    payload: Dict[str, Any],
    additional_fields: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    extras = ensure_optional_dict(additional_fields, "additional_fields")
    if extras:
        for key, value in extras.items():
            if value is None:
                continue
            payload[key] = value
    return payload


def normalize_update_fields(
    fields: Dict[str, Any],
    enum_fields: Dict[str, Dict[int, str]],
) -> Dict[str, Any]:
    if not isinstance(fields, dict) or not fields:
        raise ValueError("fields must be a non-empty object")

    sanitized: Dict[str, Any] = {k: v for k, v in fields.items() if v is not None}
    if not sanitized:
        raise ValueError("fields cannot be empty after removing null values")

    for enum_field, labels in enum_fields.items():
        if enum_field in sanitized:
            sanitized[enum_field] = normalize_enum_value(
                sanitized[enum_field], labels, enum_field
            )

    if "itilcategories_id" in sanitized:
        sanitized["itilcategories_id"] = ensure_positive_int(
            sanitized["itilcategories_id"], "itilcategories_id"
        )
    if "entities_id" in sanitized:
        sanitized["entities_id"] = ensure_non_negative_int(
            sanitized["entities_id"], "entities_id"
        )
    return sanitized


def normalize_actor_entries(
    item_id: int,
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
            actor_id = ensure_positive_int(entry, f"{entry_name[:-1]}_id")
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
            actor_id = ensure_positive_int(actor_id_value, actor_id_key)
            current = working
            current[actor_id_key] = actor_id
        else:
            raise ValueError(
                f"Unsupported value for {entry_name[:-1]} #{index}: {entry}"
            )

        current[item_id_field] = item_id
        if "type" in current and current["type"] is not None:
            current["type"] = ensure_int(current["type"], "type")
        for flag_key in ("use_notification", "is_dynamic", "is_manager"):
            if flag_key in current:
                current[flag_key] = prepare_bool_flag(current[flag_key])
        normalized.append(current)
    return normalized


def compact_payload(entries: List[Dict[str, Any]]) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
    if len(entries) == 1:
        return entries[0]
    return entries


@dataclass
class EntityList:
    item_key: str
    items: List[Dict[str, Any]]
    response_range: Optional[ResponseRange]
    prepare_item: Callable[[Dict[str, Any], Sequence[str]], Dict[str, Any]]

    def as_dict(self, fields: Sequence[str]) -> Dict[str, Any]:
        return {
            self.item_key: [self.prepare_item(item, fields) for item in self.items],
            "range": range_to_dict(self.response_range),
        }

    def to_table(self, fields: Sequence[str]) -> str:
        if not self.items:
            return f"No {self.item_key} found."
        prepared = [self.prepare_item(item, fields) for item in self.items]
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

    def respond(
        self,
        output: str,
        fields: Optional[Sequence[str]],
        default_fields: Optional[Sequence[str]] = None,
    ) -> Any:
        """Shared ``output``/``fields`` dispatch for every listing tool.

        ``fields`` (explicit request) wins over ``default_fields`` (the
        domain's own defaults, e.g. tickets/changes always have some; the
        generic itemtype access has none). With neither, ``dict``/``raw``
        return the items exactly as GLPI sent them (no projection), and
        ``table`` has no columns to fall back to, so it's a validation error.
        """
        effective_fields = fields or default_fields
        if output == "raw":
            return self.items
        if output == "table":
            if not effective_fields:
                raise ValueError("'fields' is required when output='table'")
            return self.to_table(effective_fields)
        if not effective_fields:
            return {self.item_key: self.items, "range": range_to_dict(self.response_range)}
        return self.as_dict(effective_fields)


@dataclass
class EntityCreationResult:
    entity_label: str
    payload: Dict[str, Any]
    response: Dict[str, Any]

    def as_dict(self) -> Dict[str, Any]:
        return {"payload": self.payload, "response": self.response}

    def summary(self) -> str:
        entity_id: Optional[Any] = None
        name = self.payload.get("name")
        response_obj = self.response
        if isinstance(response_obj, dict):
            entity_id = response_obj.get("id") or response_obj.get("ID")
            name = response_obj.get("name", name)
        elif isinstance(response_obj, list) and response_obj:
            first = response_obj[0]
            if isinstance(first, dict):
                entity_id = first.get("id") or first.get("ID")
                name = first.get("name", name)
        entity_id_str = str(entity_id) if entity_id is not None else "unknown"
        return f"{self.entity_label} created (id={entity_id_str}): {name}"


@dataclass
class EntityMutationResult:
    action: str
    entity_id_field: str
    entity_id: int
    description: str
    payload: Any
    response: Any

    def as_dict(self) -> Dict[str, Any]:
        return {
            "action": self.action,
            self.entity_id_field: self.entity_id,
            "description": self.description,
            "payload": self.payload,
            "response": self.response,
        }

    def summary(self) -> str:
        return self.description
