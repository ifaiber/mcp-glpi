"""Shared helpers for GLPI entity modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Sequence, Tuple, Union

from glpi_client import ResponseRange


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
        sanitized["entities_id"] = ensure_positive_int(
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
