import html
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
        if self.command == "link_change_to_ticket":
            return self._link_change_to_ticket()
        if self.command == "link_ticket_to_change":
            return self._link_ticket_to_change()
        if self.command == "unlink_change_ticket":
            return self._unlink_change_ticket()
        if self.command == "unlink_ticket_change":
            return self._unlink_ticket_change()
        if self.command == "update_change":
            return self._update_change()
        if self.command == "update_ticket":
            return self._update_ticket()
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
        additional = self._merge_pr_links(additional)

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

    def _link_change_to_ticket(self):
        change_id = self._get_from_arguments("change_id", "id", "changes_id")
        ticket_id = self._get_from_arguments("ticket_id", "ticket", "tickets_id")
        if change_id is None or ticket_id is None:
            return self._text("Los parametros 'change_id' y 'ticket_id' son obligatorios.")
        additional = self._normalize_additional(self.arguments.get("additional"))
        try:
            result = glpi.changes.link_ticket(
                change_id=change_id,
                ticket_id=ticket_id,
                additional_fields=additional,
            )
        except ValueError as exc:
            return self._text(f"Invalid argument: {exc}")
        except Exception as exc:  # pragma: no cover - depends on remote API
            logger.exception("Error linking change to ticket")
            return self._text(f"Error linking change to ticket: {exc}")
        return self._wrap_result(result)

    def _link_ticket_to_change(self):
        ticket_id = self._get_from_arguments("ticket_id", "id", "tickets_id")
        change_id = self._get_from_arguments("change_id", "change", "changes_id")
        if ticket_id is None or change_id is None:
            return self._text("Los parametros 'ticket_id' y 'change_id' son obligatorios.")
        additional = self._normalize_additional(self.arguments.get("additional"))
        try:
            result = glpi.tickets.link_change(
                ticket_id=ticket_id,
                change_id=change_id,
                additional_fields=additional,
            )
        except ValueError as exc:
            return self._text(f"Invalid argument: {exc}")
        except Exception as exc:  # pragma: no cover - depends on remote API
            logger.exception("Error linking ticket to change")
            return self._text(f"Error linking ticket to change: {exc}")
        return self._wrap_result(result)

    def _unlink_change_ticket(self):
        change_id = self._get_from_arguments("change_id", "id", "changes_id")
        link_id = self._get_from_arguments("link_id", "relation_id")
        if change_id is None or link_id is None:
            return self._text("Los parametros 'change_id' y 'link_id' son obligatorios.")
        purge = self.arguments.get("purge", False)
        keep_history = self.arguments.get("keep_history", True)
        try:
            result = glpi.changes.unlink_ticket(
                change_id=change_id,
                link_id=link_id,
                purge=purge,
                keep_history=keep_history,
            )
        except ValueError as exc:
            return self._text(f"Invalid argument: {exc}")
        except Exception as exc:  # pragma: no cover - depends on remote API
            logger.exception("Error unlinking change ticket")
            return self._text(f"Error unlinking change ticket: {exc}")
        return self._wrap_result(result)

    def _unlink_ticket_change(self):
        ticket_id = self._get_from_arguments("ticket_id", "id", "tickets_id")
        link_id = self._get_from_arguments("link_id", "relation_id")
        if ticket_id is None or link_id is None:
            return self._text("Los parametros 'ticket_id' y 'link_id' son obligatorios.")
        purge = self.arguments.get("purge", False)
        keep_history = self.arguments.get("keep_history", True)
        try:
            result = glpi.tickets.unlink_change(
                ticket_id=ticket_id,
                link_id=link_id,
                purge=purge,
                keep_history=keep_history,
            )
        except ValueError as exc:
            return self._text(f"Invalid argument: {exc}")
        except Exception as exc:  # pragma: no cover - depends on remote API
            logger.exception("Error unlinking ticket change")
            return self._text(f"Error unlinking ticket change: {exc}")
        return self._wrap_result(result)

    def _update_change(self):
        change_id = self._get_from_arguments("change_id", "id", "changes_id")
        fields = self._get_mapping_argument("fields", ("updates", "data"))
        if change_id is None:
            return self._text("El parametro 'change_id' es obligatorio para update_change.")
        if fields is None:
            return self._text("El parametro 'fields' es obligatorio y debe ser un objeto JSON.")
        fields = self._merge_pr_links(fields, target_key="controlistcontent")
        try:
            result = glpi.changes.update_change(change_id=change_id, fields=fields)
        except ValueError as exc:
            return self._text(f"Invalid argument: {exc}")
        except Exception as exc:  # pragma: no cover - depends on remote API
            logger.exception("Error updating change")
            return self._text(f"Error updating change: {exc}")
        return self._wrap_result(result)

    def _update_ticket(self):
        ticket_id = self._get_from_arguments("ticket_id", "id", "tickets_id")
        fields = self._get_mapping_argument("fields", ("updates", "data"))
        if ticket_id is None:
            return self._text("El parametro 'ticket_id' es obligatorio para update_ticket.")
        if fields is None:
            return self._text("El parametro 'fields' es obligatorio y debe ser un objeto JSON.")
        try:
            result = glpi.tickets.update_ticket(ticket_id=ticket_id, fields=fields)
        except ValueError as exc:
            return self._text(f"Invalid argument: {exc}")
        except Exception as exc:  # pragma: no cover - depends on remote API
            logger.exception("Error updating ticket")
            return self._text(f"Error updating ticket: {exc}")
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

    def _merge_pr_links(self, mapping: Optional[Dict[str, Any]], target_key: str = "controlistcontent"):
        formatted = self._format_pr_links(self.arguments.get("pr_links"))
        if not formatted:
            return mapping
        merged = dict(mapping or {})
        existing = merged.get(target_key)
        if existing:
            merged[target_key] = f"{existing}{formatted}"
        else:
            merged[target_key] = formatted
        return merged

    def _format_pr_links(self, links):
        if links is None:
            return None
        if isinstance(links, str):
            values = [links]
        elif isinstance(links, (list, tuple, set)):
            values = list(links)
        else:
            logger.warning("Unsupported pr_links value: %s", links)
            return None
        cleaned = []
        for value in values:
            if value is None:
                continue
            text_value = str(value).strip()
            if not text_value:
                continue
            cleaned.append(html.escape(text_value, quote=True))
        if not cleaned:
            return None
        return ''.join(f"<p>{item}</p>" for item in cleaned)

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

    def _get_mapping_argument(self, primary: str, alternatives: Sequence[str] = ()): 
        keys = (primary, *alternatives)
        for key in keys:
            if key not in self.arguments:
                continue
            value = self.arguments[key]
            if isinstance(value, dict):
                return value
            if isinstance(value, str):
                try:
                    parsed = json.loads(value)
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON provided for %s: %s", key, value)
                    return None
                if isinstance(parsed, dict):
                    return parsed
                logger.warning("JSON for %s must decode to an object", key)
                return None
            logger.warning("Unsupported mapping value for %s: %s", key, value)
            return None
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
