import logging
from typing import Any, Callable, Dict, Optional, Sequence

import mcp.types as types
from common.config import get_config

import glpi.changes
import glpi.session
import glpi.tickets

logger = logging.getLogger(__name__)


class CommandHandler:
    def __init__(self, command: str, arguments: Optional[Dict[str, Any]] = None):
        self.command = command
        self.arguments = arguments or {}
        self.config = get_config()

    def execute(self):
        if self.command == "echo":
            message = self.arguments.get("message", "No message provided")
            return [types.TextContent(type="text", text=f"Echo: {message}")]
        if self.command == "validate_session":
            return self.validate_session()
        if self.command == "list_tickets":
            return self._list_items(glpi.tickets.all_tickets)
        if self.command == "list_changes":
            return self._list_items(glpi.changes.all_changes)
        return [
            types.TextContent(
                type="text",
                text=f"Herramienta desconocida: {self.command}",
            )
        ]

    def validate_session(self):
        session_info = glpi.session.get_full_session()
        if session_info:
            return [types.TextContent(type="text", text=str(session_info))]
        return [types.TextContent(type="text", text="Sesion no valida")]

    def _list_items(self, fetcher: Callable[..., Any]):
        limit = self._get_int_argument("limit", 20)
        offset = self._get_int_argument("offset", 0)
        sort_by = self.arguments.get("sort_by", "date_mod")
        order = self.arguments.get("order", "DESC")
        output = self.arguments.get("output", "table")
        fields = self._normalize_fields(self.arguments.get("fields"))
        filters = self._normalize_filters(self.arguments.get("filters"))
        expand_dropdowns = self._get_bool_argument("expand_dropdowns", False)
        include_deleted = self._get_bool_argument("include_deleted", False)

        result = fetcher(
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            order=order,
            filters=filters,
            expand_dropdowns=expand_dropdowns,
            include_deleted=include_deleted,
            output=output,
            fields=fields,
        )

        text = result if isinstance(result, str) else str(result)
        return [types.TextContent(type="text", text=text)]

    def _get_int_argument(self, key: str, default: Optional[int]) -> Optional[int]:
        value = self.arguments.get(key, default)
        if value is None:
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            logger.warning(
                "Invalid value for %s: %s. Falling back to %s.",
                key,
                value,
                default,
            )
            return default

    def _get_bool_argument(self, key: str, default: bool) -> bool:
        value = self.arguments.get(key, default)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lowered = value.strip().lower()
            if lowered in {"1", "true", "yes", "y"}:
                return True
            if lowered in {"0", "false", "no", "n"}:
                return False
        if isinstance(value, (int, float)):
            return bool(value)
        if value is not default:
            logger.warning("Invalid bool for %s: %s. Using default %s.", key, value, default)
        return default

    def _normalize_fields(self, value) -> Optional[Sequence[str]]:
        if value is None:
            return None
        if isinstance(value, (list, tuple)):
            return [str(field) for field in value]
        if isinstance(value, str):
            return [value]
        logger.warning("Unsupported fields value: %s", value)
        return None

    def _normalize_filters(self, value) -> Optional[Dict[str, str]]:
        if value is None:
            return None
        if isinstance(value, dict):
            return {str(k): str(v) for k, v in value.items()}
        logger.warning("Unsupported filters value: %s", value)
        return None
