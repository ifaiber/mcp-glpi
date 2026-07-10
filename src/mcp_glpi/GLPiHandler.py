import html
import json
import logging
from typing import Any, Callable, Dict, Optional, Sequence

import mcp.types as types
from mcp_glpi.common.config import get_config
from mcp_glpi.glpi import changes as glpi_changes
from mcp_glpi.glpi import session as glpi_session
from mcp_glpi.glpi import tickets as glpi_tickets
from mcp_glpi.tool_catalog import TOOL_SPECS

logger = logging.getLogger(__name__)
COMMAND_HANDLERS = {spec.name: spec.handler_name for spec in TOOL_SPECS}
ID_ALIASES = {
    "change_id": ("change_id", "id", "changes_id"),
    "ticket_id": ("ticket_id", "id", "tickets_id"),
    "link_id": ("link_id", "relation_id"),
    "solution_type_id": ("solution_type_id", "solutiontypes_id"),
}
COLLECTION_ALIASES = {
    "users": ("user", "user_id", "users_id"),
    "groups": ("group", "group_id", "groups_id"),
}
MAPPING_ALIASES = {
    "fields": ("updates", "data"),
}


class CommandHandler:
    def __init__(self, command: str, arguments: Optional[Dict[str, Any]] = None):
        self.command = command
        self.arguments = arguments or {}
        self.config = get_config()

    def execute(self):
        handler_name = COMMAND_HANDLERS.get(self.command)
        if handler_name is not None:
            return getattr(self, handler_name)()
        return self._error(
            f"Herramienta desconocida: {self.command}",
            error_type="unknown_command",
        )

    def _echo(self):
        message = self.arguments.get("message", "No message provided")
        return self._success({"message": message})

    def validate_session(self):
        session_info = glpi_session.get_full_session_data()
        if session_info:
            return self._success(session_info)
        return self._error("Sesion no valida", error_type="invalid_session")

    def _my_profiles(self):
        return self._run_operation(
            "Error retrieving my profiles",
            lambda: self._success(glpi_session.get_my_profiles_data()),
        )

    def _list_tickets(self):
        return self._list_items(glpi_tickets.all_tickets)

    def _list_changes(self):
        return self._list_items(glpi_changes.all_changes)

    def _list_items(self, fetcher: Callable[..., Any]):
        limit = self._get_int_argument("limit", 20)
        offset = self._get_int_argument("offset", 0)
        sort_by = self.arguments.get("sort_by", "date_mod")
        order = self.arguments.get("order", "DESC")
        output = self.arguments.get("output", "dict")
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

        return self._success(result)

    def _create_change(self):
        name = self.arguments.get("name")
        if not name:
            return self._error(
                "El parametro 'name' es obligatorio para create_change.",
                error_type="validation_error",
            )
        content = self.arguments.get("content")
        status = self.arguments.get("status")
        impact = self.arguments.get("impact")
        priority = self.arguments.get("priority")
        urgency = self.arguments.get("urgency")
        category_id = self._get_int_argument("category_id", None)
        entity_id = self._get_int_argument("entity_id", None)
        additional = self._normalize_additional(self.arguments.get("additional"))
        additional = self._merge_pr_links(additional)

        return self._run_operation("Error creating change", lambda: self._wrap_result(
            glpi_changes.create_change(
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
        ))

    def _create_ticket(self):
        name = self.arguments.get("name")
        if not name:
            return self._error(
                "El parametro 'name' es obligatorio para create_ticket.",
                error_type="validation_error",
            )
        content = self.arguments.get("content")
        status = self.arguments.get("status")
        impact = self.arguments.get("impact")
        priority = self.arguments.get("priority")
        urgency = self.arguments.get("urgency")
        category_id = self._get_int_argument("category_id", None)
        entity_id = self._get_int_argument("entity_id", None)
        additional = self._normalize_additional(self.arguments.get("additional"))

        return self._run_operation("Error creating ticket", lambda: self._wrap_result(
            glpi_tickets.create_ticket(
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
        ))

    def _add_change_comment(self):
        additional = self._normalize_additional(self.arguments.get("additional"))
        is_private = self._get_bool_argument("is_private", False)
        return self._run_operation("Error adding change comment", lambda: self._wrap_result(
            glpi_changes.add_followup(
                change_id=self._get_argument_alias("change_id"),
                content=self.arguments.get("content"),
                is_private=is_private,
                additional_fields=additional,
            )
        ))

    def _add_change_solution(self):
        additional = self._normalize_additional(self.arguments.get("additional"))
        solution_type_id = self._get_argument_alias("solution_type_id")
        return self._run_operation("Error adding change solution", lambda: self._wrap_result(
            glpi_changes.add_solution(
                change_id=self._get_argument_alias("change_id"),
                content=self.arguments.get("content"),
                solution_type_id=solution_type_id,
                additional_fields=additional,
            )
        ))

    def _assign_change_users(self):
        users = self._get_collection_alias("users")
        return self._run_operation("Error assigning change users", lambda: self._wrap_result(
            glpi_changes.assign_change_users(
                change_id=self._get_argument_alias("change_id"),
                users=users,
            )
        ))

    def _assign_change_groups(self):
        groups = self._get_collection_alias("groups")
        return self._run_operation("Error assigning change groups", lambda: self._wrap_result(
            glpi_changes.assign_change_groups(
                change_id=self._get_argument_alias("change_id"),
                groups=groups,
            )
        ))

    def _add_ticket_comment(self):
        additional = self._normalize_additional(self.arguments.get("additional"))
        is_private = self._get_bool_argument("is_private", False)
        return self._run_operation("Error adding ticket comment", lambda: self._wrap_result(
            glpi_tickets.add_followup(
                ticket_id=self._get_argument_alias("ticket_id"),
                content=self.arguments.get("content"),
                is_private=is_private,
                additional_fields=additional,
            )
        ))

    def _add_ticket_solution(self):
        additional = self._normalize_additional(self.arguments.get("additional"))
        solution_type_id = self._get_argument_alias("solution_type_id")
        return self._run_operation("Error adding ticket solution", lambda: self._wrap_result(
            glpi_tickets.add_solution(
                ticket_id=self._get_argument_alias("ticket_id"),
                content=self.arguments.get("content"),
                solution_type_id=solution_type_id,
                additional_fields=additional,
            )
        ))

    def _assign_ticket_users(self):
        users = self._get_collection_alias("users")
        return self._run_operation("Error assigning ticket users", lambda: self._wrap_result(
            glpi_tickets.assign_ticket_users(
                ticket_id=self._get_argument_alias("ticket_id"),
                users=users,
            )
        ))

    def _assign_ticket_groups(self):
        groups = self._get_collection_alias("groups")
        return self._run_operation("Error assigning ticket groups", lambda: self._wrap_result(
            glpi_tickets.assign_ticket_groups(
                ticket_id=self._get_argument_alias("ticket_id"),
                groups=groups,
            )
        ))

    def _link_change_to_ticket(self):
        change_id = self._get_argument_alias("change_id")
        ticket_id = self._get_from_arguments("ticket_id", "ticket", "tickets_id")
        if change_id is None or ticket_id is None:
            return self._error(
                "Los parametros 'change_id' y 'ticket_id' son obligatorios.",
                error_type="validation_error",
            )
        additional = self._normalize_additional(self.arguments.get("additional"))
        return self._run_operation("Error linking change to ticket", lambda: self._wrap_result(
            glpi_changes.link_ticket(
                change_id=change_id,
                ticket_id=ticket_id,
                additional_fields=additional,
            )
        ))

    def _link_ticket_to_change(self):
        ticket_id = self._get_argument_alias("ticket_id")
        change_id = self._get_from_arguments("change_id", "change", "changes_id")
        if ticket_id is None or change_id is None:
            return self._error(
                "Los parametros 'ticket_id' y 'change_id' son obligatorios.",
                error_type="validation_error",
            )
        additional = self._normalize_additional(self.arguments.get("additional"))
        return self._run_operation("Error linking ticket to change", lambda: self._wrap_result(
            glpi_tickets.link_change(
                ticket_id=ticket_id,
                change_id=change_id,
                additional_fields=additional,
            )
        ))

    def _unlink_change_ticket(self):
        change_id = self._get_argument_alias("change_id")
        link_id = self._get_argument_alias("link_id")
        if change_id is None or link_id is None:
            return self._error(
                "Los parametros 'change_id' y 'link_id' son obligatorios.",
                error_type="validation_error",
            )
        purge = self.arguments.get("purge", False)
        keep_history = self.arguments.get("keep_history", True)
        return self._run_operation("Error unlinking change ticket", lambda: self._wrap_result(
            glpi_changes.unlink_ticket(
                change_id=change_id,
                link_id=link_id,
                purge=purge,
                keep_history=keep_history,
            )
        ))

    def _unlink_ticket_change(self):
        ticket_id = self._get_argument_alias("ticket_id")
        link_id = self._get_argument_alias("link_id")
        if ticket_id is None or link_id is None:
            return self._error(
                "Los parametros 'ticket_id' y 'link_id' son obligatorios.",
                error_type="validation_error",
            )
        purge = self.arguments.get("purge", False)
        keep_history = self.arguments.get("keep_history", True)
        return self._run_operation("Error unlinking ticket change", lambda: self._wrap_result(
            glpi_tickets.unlink_change(
                ticket_id=ticket_id,
                link_id=link_id,
                purge=purge,
                keep_history=keep_history,
            )
        ))

    def _update_change(self):
        change_id = self._get_argument_alias("change_id")
        fields = self._get_mapping_alias("fields")
        if change_id is None:
            return self._error(
                "El parametro 'change_id' es obligatorio para update_change.",
                error_type="validation_error",
            )
        if fields is None:
            return self._error(
                "El parametro 'fields' es obligatorio y debe ser un objeto JSON.",
                error_type="validation_error",
            )
        fields = self._merge_pr_links(fields, target_key="controlistcontent")
        return self._run_operation(
            "Error updating change",
            lambda: self._wrap_result(glpi_changes.update_change(change_id=change_id, fields=fields)),
        )

    def _update_ticket(self):
        ticket_id = self._get_argument_alias("ticket_id")
        fields = self._get_mapping_alias("fields")
        if ticket_id is None:
            return self._error(
                "El parametro 'ticket_id' es obligatorio para update_ticket.",
                error_type="validation_error",
            )
        if fields is None:
            return self._error(
                "El parametro 'fields' es obligatorio y debe ser un objeto JSON.",
                error_type="validation_error",
            )
        return self._run_operation(
            "Error updating ticket",
            lambda: self._wrap_result(glpi_tickets.update_ticket(ticket_id=ticket_id, fields=fields)),
        )

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
                payload = details_obj
            else:
                payload = result
            return self._success(payload, summary=summary)
        else:
            return self._success(result)

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

    def _get_argument_alias(self, canonical_key: str):
        return self._get_from_arguments(*ID_ALIASES[canonical_key])

    def _get_collection_argument(self, primary: str, alternatives: Sequence[str]):
        value = self.arguments.get(primary)
        if value is not None:
            return value
        for key in alternatives:
            if key in self.arguments:
                return self.arguments[key]
        return None

    def _get_collection_alias(self, canonical_key: str):
        return self._get_collection_argument(canonical_key, COLLECTION_ALIASES[canonical_key])

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

    def _get_mapping_alias(self, canonical_key: str):
        return self._get_mapping_argument(canonical_key, MAPPING_ALIASES[canonical_key])

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

    def _success(self, data: Any, summary: Optional[str] = None):
        payload: Dict[str, Any] = {
            "ok": True,
            "command": self.command,
            "data": data,
        }
        if summary is not None:
            payload["summary"] = summary
        return self._json_response(payload)

    def _error(self, message: str, error_type: str = "error", details: Any = None):
        payload: Dict[str, Any] = {
            "ok": False,
            "command": self.command,
            "error": {
                "type": error_type,
                "message": message,
            },
        }
        if details is not None:
            payload["error"]["details"] = details
        return self._json_response(payload)

    def _json_response(self, payload: Dict[str, Any]):
        return [
            types.TextContent(
                type="text",
                text=json.dumps(payload, ensure_ascii=False, default=str),
            )
        ]

    def _run_operation(self, runtime_message: str, operation: Callable[[], Any]):
        try:
            return operation()
        except ValueError as exc:
            return self._error(f"Invalid argument: {exc}", error_type="validation_error")
        except Exception as exc:  # pragma: no cover - depends on remote API
            logger.exception(runtime_message)
            return self._error(f"{runtime_message}: {exc}", error_type="runtime_error")
