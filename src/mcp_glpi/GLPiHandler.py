import json
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
            return self._text(f"Echo: {message}")
        if self.command == "validate_session":
            return self.validate_session()
        if self.command == "list_tickets":
            return self._list_items(glpi.tickets.all_tickets)
        if self.command == "list_changes":
            return self._list_items(glpi.changes.all_changes)
        if self.command == "create_change":
            return self._create_change()
        if self.command == "create_ticket":
            return self._create_ticket()
        if self.command == "add_change_comment":
            return self._add_change_comment()
        if self.command == "add_change_solution":
            return self._add_change_solution()
        if self.command == "assign_change_users":
            return self._assign_change_users()
        if self.command == "assign_change_groups":
            return self._assign_change_groups()
        if self.command == "add_ticket_comment":
            return self._add_ticket_comment()
        if self.command == "add_ticket_solution":
            return self._add_ticket_solution()
        if self.command == "assign_ticket_users":
            return self._assign_ticket_users()
        if self.command == "assign_ticket_groups":
            return self._assign_ticket_groups()
        return self._text(f"Herramienta desconocida: {self.command}")

    def validate_session(self):
        session_info = glpi.session.get_full_session()
        if session_info:
            return self._text(str(session_info))
        return self._text("Sesion no valida")

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
        return self._text(text)

    def _create_change(self):
        name = self.arguments.get("name")
        if not name:
            return self._text("El parametro 'name' es obligatorio para create_change.")
        content = self.arguments.get("content")
        status = self.arguments.get("status")
        impact = self.arguments.get("impact")
        priority = self.arguments.get("priority")
        urgency = self.arguments.get("urgency")
        category_id = self._get_int_argument("category_id", None)
        entity_id = self._get_int_argument("entity_id", None)
        additional = self._normalize_additional(self.arguments.get("additional"))

        try:
            result = glpi.changes.create_change(
                name=name,
                content="" if content is None else str(content),
                status=status,
                impact=impact,
                priority=priority,
                urgency=urgency,
                category_id=category_id,
                entity_id=entity_id,
                additional_fields=additional,
            )
        except ValueError as exc:
            return self._text(f"Invalid argument: {exc}")
        except Exception as exc:  # pragma: no cover - depends on remote API
            logger.exception("Error creating change")
            return self._text(f"Error creating change: {exc}")

        return self._wrap_result(result)

    def _create_ticket(self):
        name = self.arguments.get("name")
        if not name:
            return self._text("El parametro 'name' es obligatorio para create_ticket.")
        content = self.arguments.get("content")
        status = self.arguments.get("status")
        impact = self.arguments.get("impact")
        priority = self.arguments.get("priority")
        urgency = self.arguments.get("urgency")
        category_id = self._get_int_argument("category_id", None)
        entity_id = self._get_int_argument("entity_id", None)
        additional = self._normalize_additional(self.arguments.get("additional"))

        try:
            result = glpi.tickets.create_ticket(
                name=name,
                content="" if content is None else str(content),
                status=status,
                impact=impact,
                priority=priority,
                urgency=urgency,
                category_id=category_id,
                entity_id=entity_id,
                additional_fields=additional,
            )
        except ValueError as exc:
            return self._text(f"Invalid argument: {exc}")
        except Exception as exc:  # pragma: no cover - depends on remote API
            logger.exception("Error creating ticket")
            return self._text(f"Error creating ticket: {exc}")

        return self._wrap_result(result)

    def _add_change_comment(self):
        additional = self._normalize_additional(self.arguments.get("additional"))
        is_private = self._get_bool_argument("is_private", False)
        try:
            result = glpi.changes.add_followup(
                change_id=self._get_from_arguments("change_id", "id"),
                content=self.arguments.get("content"),
                is_private=is_private,
                additional_fields=additional,
            )
        except ValueError as exc:
            return self._text(f"Invalid argument: {exc}")
        except Exception as exc:  # pragma: no cover - depends on remote API
            logger.exception("Error adding change comment")
            return self._text(f"Error adding change comment: {exc}")
        return self._wrap_result(result)

    def _add_change_solution(self):
        additional = self._normalize_additional(self.arguments.get("additional"))
        solution_type_id = self._get_from_arguments("solution_type_id", "solutiontypes_id")
        try:
            result = glpi.changes.add_solution(
                change_id=self._get_from_arguments("change_id", "id"),
                content=self.arguments.get("content"),
                solution_type_id=solution_type_id,
                additional_fields=additional,
            )
        except ValueError as exc:
            return self._text(f"Invalid argument: {exc}")
        except Exception as exc:  # pragma: no cover - depends on remote API
            logger.exception("Error adding change solution")
            return self._text(f"Error adding change solution: {exc}")
        return self._wrap_result(result)

    def _assign_change_users(self):
        users = self._get_collection_argument("users", ("user", "user_id", "users_id"))
        try:
            result = glpi.changes.assign_change_users(
                change_id=self._get_from_arguments("change_id", "id"),
                users=users,
            )
        except ValueError as exc:
            return self._text(f"Invalid argument: {exc}")
        except Exception as exc:  # pragma: no cover - depends on remote API
            logger.exception("Error assigning change users")
            return self._text(f"Error assigning change users: {exc}")
        return self._wrap_result(result)

    def _assign_change_groups(self):
        groups = self._get_collection_argument("groups", ("group", "group_id", "groups_id"))
        try:
            result = glpi.changes.assign_change_groups(
                change_id=self._get_from_arguments("change_id", "id"),
                groups=groups,
            )
        except ValueError as exc:
            return self._text(f"Invalid argument: {exc}")
        except Exception as exc:  # pragma: no cover - depends on remote API
            logger.exception("Error assigning change groups")
            return self._text(f"Error assigning change groups: {exc}")
        return self._wrap_result(result)

    def _add_ticket_comment(self):
        additional = self._normalize_additional(self.arguments.get("additional"))
        is_private = self._get_bool_argument("is_private", False)
        try:
            result = glpi.tickets.add_followup(
                ticket_id=self._get_from_arguments("ticket_id", "id"),
                content=self.arguments.get("content"),
                is_private=is_private,
                additional_fields=additional,
            )
        except ValueError as exc:
            return self._text(f"Invalid argument: {exc}")
        except Exception as exc:  # pragma: no cover - depends on remote API
            logger.exception("Error adding ticket comment")
            return self._text(f"Error adding ticket comment: {exc}")
        return self._wrap_result(result)

    def _add_ticket_solution(self):
        additional = self._normalize_additional(self.arguments.get("additional"))
        solution_type_id = self._get_from_arguments("solution_type_id", "solutiontypes_id")
        try:
            result = glpi.tickets.add_solution(
                ticket_id=self._get_from_arguments("ticket_id", "id"),
                content=self.arguments.get("content"),
                solution_type_id=solution_type_id,
                additional_fields=additional,
            )
        except ValueError as exc:
            return self._text(f"Invalid argument: {exc}")
        except Exception as exc:  # pragma: no cover - depends on remote API
            logger.exception("Error adding ticket solution")
            return self._text(f"Error adding ticket solution: {exc}")
        return self._wrap_result(result)

    def _assign_ticket_users(self):
        users = self._get_collection_argument("users", ("user", "user_id", "users_id"))
        try:
            result = glpi.tickets.assign_ticket_users(
                ticket_id=self._get_from_arguments("ticket_id", "id"),
                users=users,
            )
        except ValueError as exc:
            return self._text(f"Invalid argument: {exc}")
        except Exception as exc:  # pragma: no cover - depends on remote API
            logger.exception("Error assigning ticket users")
            return self._text(f"Error assigning ticket users: {exc}")
        return self._wrap_result(result)

    def _assign_ticket_groups(self):
        groups = self._get_collection_argument("groups", ("group", "group_id", "groups_id"))
        try:
            result = glpi.tickets.assign_ticket_groups(
                ticket_id=self._get_from_arguments("ticket_id", "id"),
                groups=groups,
            )
        except ValueError as exc:
            return self._text(f"Invalid argument: {exc}")
        except Exception as exc:  # pragma: no cover - depends on remote API
            logger.exception("Error assigning ticket groups")
            return self._text(f"Error assigning ticket groups: {exc}")
        return self._wrap_result(result)

    def _wrap_result(self, result: Any):
        if hasattr(result, "summary") and callable(result.summary):
            summary = result.summary()
            details_obj = None
            if hasattr(result, "as_dict") and callable(result.as_dict):
                try:
                    details_obj = result.as_dict()
                except Exception:  # pragma: no cover - defensive
                    logger.debug("Could not serialise result", exc_info=True)
            if details_obj is not None:
                try:
                    details = json.dumps(details_obj, indent=2)
                except TypeError:
                    details = str(details_obj)
                text = f"{summary}\n\n{details}"
            else:
                text = summary
        else:
            try:
                text = json.dumps(result, indent=2)
            except TypeError:
                text = str(result)
        return self._text(text)

    def _get_from_arguments(self, *keys: str):
        for key in keys:
            if key in self.arguments:
                return self.arguments[key]
        return None

    def _get_collection_argument(self, primary: str, alternatives: Sequence[str]):
        value = self.arguments.get(primary)
        if value is not None:
            return value
        for key in alternatives:
            if key in self.arguments:
                return self.arguments[key]
        return None

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

    def _normalize_additional(self, value) -> Optional[Dict[str, Any]]:
        if value is None:
            return None
        if isinstance(value, dict):
            return value
        logger.warning("Unsupported additional value: %s", value)
        return None

    def _text(self, message: str):
        return [types.TextContent(type="text", text=message)]
