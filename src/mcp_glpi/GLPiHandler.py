import html
import json
import logging
from typing import Any, Callable, Dict, List, Optional, Sequence

import mcp.types as types
from mcp_glpi.common.config import get_config
from mcp_glpi.glpi import assistance as glpi_assistance
from mcp_glpi.glpi import changes as glpi_changes
from mcp_glpi.glpi import files as glpi_files
from mcp_glpi.glpi import generic as glpi_generic
from mcp_glpi.glpi import session as glpi_session
from mcp_glpi.glpi import tickets as glpi_tickets
from mcp_glpi.tool_catalog import TOOL_SPECS

logger = logging.getLogger(__name__)
COMMAND_HANDLERS = {spec.name: spec.handler_name for spec in TOOL_SPECS}
ID_ALIASES = {
    "change_id": ("change_id", "id", "changes_id"),
    "ticket_id": ("ticket_id", "id", "tickets_id"),
    "document_id": ("document_id", "id", "documents_id"),
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
        self._resolved_entity_id: Optional[int] = None
        self._resolved_profile_id: Optional[int] = None
        self._resolution_notes: List[str] = []

    def execute(self):
        handler_name = COMMAND_HANDLERS.get(self.command)
        if handler_name is None:
            return self._error(
                f"Herramienta desconocida: {self.command}",
                error_type="unknown_command",
            )
        try:
            self._resolve_entity_and_profile()
        except ValueError as exc:
            return self._error(f"Invalid argument: {exc}", error_type="validation_error")
        except Exception as exc:  # pragma: no cover - depends on remote API
            logger.exception("Error resolving entity_id/profile_id")
            return self._error(
                f"Error resolving entity_id/profile_id: {exc}", error_type="runtime_error"
            )
        return getattr(self, handler_name)()

    def _session_validate(self):
        session_info = glpi_session.get_full_session_data()
        if session_info:
            return self._success(session_info)
        return self._error("Sesion no valida", error_type="invalid_session")

    def _entityprofile_list(self):
        return self._run_operation(
            "Error retrieving my profiles",
            lambda: self._success(glpi_session.get_my_profiles_data()),
        )

    def _ticket_list(self):
        return self._list_items(glpi_tickets.all_tickets)

    def _change_list(self):
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
        entity_id = self._get_entity_id()
        profile_id = self._get_profile_id()

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
            entity_id=entity_id,
            profile_id=profile_id,
        )

        return self._success(result)

    def _change_add(self):
        name = self.arguments.get("name")
        if not name:
            return self._error(
                "El parametro 'name' es obligatorio para change_add.",
                error_type="validation_error",
            )
        content = self.arguments.get("content")
        status = self.arguments.get("status")
        impact = self.arguments.get("impact")
        priority = self.arguments.get("priority")
        urgency = self.arguments.get("urgency")
        category_id = self._get_int_argument("category_id", None)
        entity_id = self._get_entity_id()
        profile_id = self._get_profile_id()
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
                profile_id=profile_id,
                additional_fields=additional,
            )
        ))

    def _ticket_add(self):
        name = self.arguments.get("name")
        if not name:
            return self._error(
                "El parametro 'name' es obligatorio para ticket_add.",
                error_type="validation_error",
            )
        content = self.arguments.get("content")
        status = self.arguments.get("status")
        impact = self.arguments.get("impact")
        priority = self.arguments.get("priority")
        urgency = self.arguments.get("urgency")
        category_id = self._get_int_argument("category_id", None)
        entity_id = self._get_entity_id()
        profile_id = self._get_profile_id()
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
                profile_id=profile_id,
                additional_fields=additional,
            )
        ))

    def _change_follow_add(self):
        additional = self._normalize_additional(self.arguments.get("additional"))
        is_private = self._get_bool_argument("is_private", False)
        return self._run_operation("Error adding change comment", lambda: self._wrap_result(
            glpi_changes.add_followup(
                change_id=self._get_argument_alias("change_id"),
                content=self.arguments.get("content"),
                is_private=is_private,
                additional_fields=additional,
                entity_id=self._get_entity_id(),
                profile_id=self._get_profile_id(),
            )
        ))

    def _change_solution_add(self):
        additional = self._normalize_additional(self.arguments.get("additional"))
        solution_type_id = self._get_argument_alias("solution_type_id")
        return self._run_operation("Error adding change solution", lambda: self._wrap_result(
            glpi_changes.add_solution(
                change_id=self._get_argument_alias("change_id"),
                content=self.arguments.get("content"),
                solution_type_id=solution_type_id,
                additional_fields=additional,
                entity_id=self._get_entity_id(),
                profile_id=self._get_profile_id(),
            )
        ))

    def _assistance_item_user_add(self):
        itemtype = self.arguments.get("itemtype")
        item_id = self.arguments.get("id")
        users = self._get_collection_alias("users")
        if not itemtype or item_id is None:
            return self._error(
                "Los parametros 'itemtype' e 'id' son obligatorios para assistance_item_user_add.",
                error_type="validation_error",
            )
        return self._run_operation("Error assigning assistance item users", lambda: self._wrap_result(
            glpi_assistance.assign_assistance_users(
                itemtype=itemtype,
                item_id=item_id,
                users=users,
                entity_id=self._get_entity_id(),
                profile_id=self._get_profile_id(),
            )
        ))

    def _assistance_item_group_add(self):
        itemtype = self.arguments.get("itemtype")
        item_id = self.arguments.get("id")
        groups = self._get_collection_alias("groups")
        if not itemtype or item_id is None:
            return self._error(
                "Los parametros 'itemtype' e 'id' son obligatorios para assistance_item_group_add.",
                error_type="validation_error",
            )
        return self._run_operation("Error assigning assistance item groups", lambda: self._wrap_result(
            glpi_assistance.assign_assistance_groups(
                itemtype=itemtype,
                item_id=item_id,
                groups=groups,
                entity_id=self._get_entity_id(),
                profile_id=self._get_profile_id(),
            )
        ))

    def _ticket_follow_add(self):
        additional = self._normalize_additional(self.arguments.get("additional"))
        is_private = self._get_bool_argument("is_private", False)
        return self._run_operation("Error adding ticket comment", lambda: self._wrap_result(
            glpi_tickets.add_followup(
                ticket_id=self._get_argument_alias("ticket_id"),
                content=self.arguments.get("content"),
                is_private=is_private,
                additional_fields=additional,
                entity_id=self._get_entity_id(),
                profile_id=self._get_profile_id(),
            )
        ))

    def _ticket_solution_add(self):
        additional = self._normalize_additional(self.arguments.get("additional"))
        solution_type_id = self._get_argument_alias("solution_type_id")
        return self._run_operation("Error adding ticket solution", lambda: self._wrap_result(
            glpi_tickets.add_solution(
                ticket_id=self._get_argument_alias("ticket_id"),
                content=self.arguments.get("content"),
                solution_type_id=solution_type_id,
                additional_fields=additional,
                entity_id=self._get_entity_id(),
                profile_id=self._get_profile_id(),
            )
        ))

    def _change_ticket_link(self):
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
                entity_id=self._get_entity_id(),
                profile_id=self._get_profile_id(),
            )
        ))

    def _ticket_change_link(self):
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
                entity_id=self._get_entity_id(),
                profile_id=self._get_profile_id(),
            )
        ))

    def _change_ticket_unlink(self):
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
                entity_id=self._get_entity_id(),
                profile_id=self._get_profile_id(),
            )
        ))

    def _ticket_change_unlink(self):
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
                entity_id=self._get_entity_id(),
                profile_id=self._get_profile_id(),
            )
        ))

    def _change_update(self):
        change_id = self._get_argument_alias("change_id")
        fields = self._get_mapping_alias("fields")
        if change_id is None:
            return self._error(
                "El parametro 'change_id' es obligatorio para change_update.",
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
            lambda: self._wrap_result(
                glpi_changes.update_change(
                    change_id=change_id,
                    fields=fields,
                    entity_id=self._get_entity_id(),
                    profile_id=self._get_profile_id(),
                )
            ),
        )

    def _ticket_update(self):
        ticket_id = self._get_argument_alias("ticket_id")
        fields = self._get_mapping_alias("fields")
        if ticket_id is None:
            return self._error(
                "El parametro 'ticket_id' es obligatorio para ticket_update.",
                error_type="validation_error",
            )
        if fields is None:
            return self._error(
                "El parametro 'fields' es obligatorio y debe ser un objeto JSON.",
                error_type="validation_error",
            )
        return self._run_operation(
            "Error updating ticket",
            lambda: self._wrap_result(
                glpi_tickets.update_ticket(
                    ticket_id=ticket_id,
                    fields=fields,
                    entity_id=self._get_entity_id(),
                    profile_id=self._get_profile_id(),
                )
            ),
        )

    def _ticket_delete(self):
        ticket_id = self._get_argument_alias("ticket_id")
        if ticket_id is None:
            return self._error(
                "El parametro 'ticket_id' es obligatorio para ticket_delete.",
                error_type="validation_error",
            )
        purge = self.arguments.get("purge", False)
        keep_history = self.arguments.get("keep_history", True)
        return self._run_operation("Error deleting ticket", lambda: self._wrap_result(
            glpi_tickets.delete_ticket(
                ticket_id=ticket_id,
                purge=purge,
                keep_history=keep_history,
                entity_id=self._get_entity_id(),
                profile_id=self._get_profile_id(),
            )
        ))

    def _change_delete(self):
        change_id = self._get_argument_alias("change_id")
        if change_id is None:
            return self._error(
                "El parametro 'change_id' es obligatorio para change_delete.",
                error_type="validation_error",
            )
        purge = self.arguments.get("purge", False)
        keep_history = self.arguments.get("keep_history", True)
        return self._run_operation("Error deleting change", lambda: self._wrap_result(
            glpi_changes.delete_change(
                change_id=change_id,
                purge=purge,
                keep_history=keep_history,
                entity_id=self._get_entity_id(),
                profile_id=self._get_profile_id(),
            )
        ))

    def _item_type_list(self):
        return self._run_operation(
            "Error listing itemtypes",
            lambda: self._success(glpi_generic.list_itemtypes()),
        )

    def _item_subtype_list(self):
        itemtype = self.arguments.get("itemtype")
        return self._run_operation(
            "Error listing subtypes",
            lambda: self._success(glpi_generic.list_subtypes(itemtype)),
        )

    def _item_list(self):
        itemtype = self.arguments.get("itemtype")
        if not itemtype:
            return self._error(
                "El parametro 'itemtype' es obligatorio para item_list.",
                error_type="validation_error",
            )
        limit = self._get_int_argument("limit", 20)
        offset = self._get_int_argument("offset", 0)
        sort_by = self.arguments.get("sort_by", "date_mod")
        order = self.arguments.get("order", "DESC")
        output = self.arguments.get("output", "dict")
        fields = self._normalize_fields(self.arguments.get("fields"))
        filters = self._normalize_filters(self.arguments.get("filters"))
        expand_dropdowns = self._get_bool_argument("expand_dropdowns", False)
        include_deleted = self._get_bool_argument("include_deleted", False)

        return self._run_operation("Error listing items", lambda: self._success(
            glpi_generic.list_items(
                itemtype,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                order=order,
                output=output,
                fields=fields,
                filters=filters,
                expand_dropdowns=expand_dropdowns,
                include_deleted=include_deleted,
                entity_id=self._get_entity_id(),
                profile_id=self._get_profile_id(),
            )
        ))

    def _item_get(self):
        itemtype = self.arguments.get("itemtype")
        item_id = self.arguments.get("id")
        if not itemtype or item_id is None:
            return self._error(
                "Los parametros 'itemtype' e 'id' son obligatorios para item_get.",
                error_type="validation_error",
            )
        fields = self._normalize_fields(self.arguments.get("fields"))
        expand_dropdowns = self._get_bool_argument("expand_dropdowns", False)

        return self._run_operation("Error getting item", lambda: self._success(
            glpi_generic.get_item(
                itemtype,
                item_id,
                fields=fields,
                expand_dropdowns=expand_dropdowns,
                entity_id=self._get_entity_id(),
                profile_id=self._get_profile_id(),
            )
        ))

    def _item_subitem_list(self):
        itemtype = self.arguments.get("itemtype")
        item_id = self.arguments.get("id")
        subtype = self.arguments.get("subtype")
        if not itemtype or item_id is None or not subtype:
            return self._error(
                "Los parametros 'itemtype', 'id' y 'subtype' son obligatorios para item_subitem_list.",
                error_type="validation_error",
            )
        limit = self._get_int_argument("limit", 20)
        offset = self._get_int_argument("offset", 0)
        sort_by = self.arguments.get("sort_by")
        order = self.arguments.get("order", "DESC")
        output = self.arguments.get("output", "dict")
        fields = self._normalize_fields(self.arguments.get("fields"))

        return self._run_operation("Error listing sub-items", lambda: self._success(
            glpi_generic.list_subitems(
                itemtype,
                item_id,
                subtype,
                limit=limit,
                offset=offset,
                sort_by=sort_by,
                order=order,
                output=output,
                fields=fields,
                entity_id=self._get_entity_id(),
                profile_id=self._get_profile_id(),
            )
        ))

    def _item_delete(self):
        itemtype = self.arguments.get("itemtype")
        item_id = self.arguments.get("id")
        if not itemtype or item_id is None:
            return self._error(
                "Los parametros 'itemtype' e 'id' son obligatorios para item_delete.",
                error_type="validation_error",
            )
        purge = self.arguments.get("purge", False)
        keep_history = self.arguments.get("keep_history", True)

        return self._run_operation("Error deleting item", lambda: self._wrap_result(
            glpi_generic.delete_item(
                itemtype,
                item_id,
                purge=purge,
                keep_history=keep_history,
                entity_id=self._get_entity_id(),
                profile_id=self._get_profile_id(),
            )
        ))

    def _file_upload(self):
        file_path = self.arguments.get("file_path")
        if not file_path:
            return self._error(
                "El parametro 'file_path' es obligatorio para file_upload.",
                error_type="validation_error",
            )
        name = self.arguments.get("name")
        file_name = self.arguments.get("file_name")
        additional = self._normalize_additional(self.arguments.get("additional"))

        return self._run_operation("Error uploading document", lambda: self._wrap_result(
            glpi_files.upload_document(
                file_path,
                name=name,
                file_name=file_name,
                additional_fields=additional,
                entity_id=self._get_entity_id(),
                profile_id=self._get_profile_id(),
            )
        ))

    def _file_download(self):
        document_id = self._get_argument_alias("document_id")
        destination_path = self.arguments.get("destination_path")
        if document_id is None or not destination_path:
            return self._error(
                "Los parametros 'document_id' y 'destination_path' son obligatorios para file_download.",
                error_type="validation_error",
            )

        return self._run_operation("Error downloading document", lambda: self._wrap_result(
            glpi_files.download_document(
                document_id,
                destination_path,
                entity_id=self._get_entity_id(),
                profile_id=self._get_profile_id(),
            )
        ))

    def _file_link(self):
        document_id = self._get_argument_alias("document_id")
        item_type = self.arguments.get("item_type")
        item_id = self.arguments.get("item_id")
        if document_id is None or not item_type or item_id is None:
            return self._error(
                "Los parametros 'document_id', 'item_type' e 'item_id' son obligatorios para file_link.",
                error_type="validation_error",
            )
        additional = self._normalize_additional(self.arguments.get("additional"))

        return self._run_operation("Error linking document", lambda: self._wrap_result(
            glpi_files.link_item(
                document_id=document_id,
                item_type=item_type,
                item_id=item_id,
                additional_fields=additional,
                entity_id=self._get_entity_id(),
                profile_id=self._get_profile_id(),
            )
        ))

    def _file_unlink(self):
        document_id = self._get_argument_alias("document_id")
        link_id = self._get_argument_alias("link_id")
        if document_id is None or link_id is None:
            return self._error(
                "Los parametros 'document_id' y 'link_id' son obligatorios para file_unlink.",
                error_type="validation_error",
            )
        purge = self.arguments.get("purge", False)
        keep_history = self.arguments.get("keep_history", True)

        return self._run_operation("Error unlinking document", lambda: self._wrap_result(
            glpi_files.unlink_item(
                document_id=document_id,
                link_id=link_id,
                purge=purge,
                keep_history=keep_history,
                entity_id=self._get_entity_id(),
                profile_id=self._get_profile_id(),
            )
        ))

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

    def _get_entity_id(self) -> Optional[int]:
        return self._resolved_entity_id

    def _get_profile_id(self) -> Optional[int]:
        return self._resolved_profile_id

    @staticmethod
    def _is_blank(value: Any) -> bool:
        return value is None or (isinstance(value, str) and not value.strip())

    @staticmethod
    def _looks_numeric(value: Any) -> bool:
        try:
            int(value)
            return True
        except (TypeError, ValueError):
            return False

    def _resolve_entity_and_profile(self) -> None:
        """Resolve entity_id/profile_id for the current command.

        Both are normally numeric ids. If either is given as a non-numeric,
        non-blank string, it is treated as a *name* to look up via
        ``get_my_profiles_data()`` (the same data ``entityprofile_list`` exposes):

        - Profile name only (no entity given): switch to that profile, then
          fall back to the first entity in its entity list (since none was
          requested), and record which one was auto-selected.
        - Entity name only (no profile given): search every profile's
          entities for a matching name and resolve both the profile and the
          entity from whichever match is found.
        - Ambiguous name (matches more than one profile/entity) or a name
          that matches nothing raises ValueError, which the caller reports
          as a validation error instead of guessing.

        Numeric ids and blank/omitted values behave exactly as before.
        """
        raw_entity = self._get_from_arguments("entity_id", "entities_id")
        raw_profile = self._get_from_arguments("profile_id", "profiles_id")

        entity_blank = self._is_blank(raw_entity)
        profile_blank = self._is_blank(raw_profile)
        entity_is_name = not entity_blank and not self._looks_numeric(raw_entity)
        profile_is_name = not profile_blank and not self._looks_numeric(raw_profile)

        if not entity_is_name and not profile_is_name:
            self._resolved_entity_id = None if entity_blank else int(raw_entity)
            self._resolved_profile_id = None if profile_blank else int(raw_profile)
            return

        profiles = glpi_session.get_my_profiles_data()

        resolved_profile: Optional[Dict[str, Any]] = None
        resolved_entity_id = None if (entity_blank or entity_is_name) else int(raw_entity)
        resolved_profile_id = None if (profile_blank or profile_is_name) else int(raw_profile)

        if profile_is_name:
            needle = str(raw_profile).strip().lower()
            matches = [p for p in profiles if str(p.get("name", "")).strip().lower() == needle]
            if not matches:
                raise ValueError(
                    f"No se encontro el perfil '{raw_profile}'. Use 'entityprofile_list' para ver "
                    "los perfiles disponibles."
                )
            if len(matches) > 1:
                ids = [p.get("id") for p in matches]
                raise ValueError(
                    f"El nombre de perfil '{raw_profile}' es ambiguo: coincide con {len(matches)} "
                    f"perfiles (ids {ids}). Use el id numerico del perfil para desambiguar."
                )
            resolved_profile = matches[0]
            resolved_profile_id = resolved_profile.get("id")
            self._resolution_notes.append(
                f"profile_id: nombre de perfil '{raw_profile}' resuelto a id {resolved_profile_id}."
            )

            if entity_blank:
                entities = resolved_profile.get("entities") or []
                if not entities:
                    raise ValueError(
                        f"El perfil '{resolved_profile.get('name')}' (id {resolved_profile_id}) no "
                        "tiene entidades asociadas."
                    )
                chosen = entities[0]
                resolved_entity_id = chosen.get("id")
                self._resolution_notes.append(
                    "entity_id: no se indico; se selecciono automaticamente la primera entidad del "
                    f"perfil '{resolved_profile.get('name')}': '{chosen.get('name')}' "
                    f"(id {resolved_entity_id})."
                )

        if entity_is_name:
            needle = str(raw_entity).strip().lower()
            if resolved_profile is not None:
                search_scope = [resolved_profile]
            elif resolved_profile_id is not None:
                search_scope = [p for p in profiles if p.get("id") == resolved_profile_id]
            else:
                search_scope = profiles

            candidates = []
            for profile in search_scope:
                for entity in profile.get("entities") or []:
                    if str(entity.get("name", "")).strip().lower() == needle:
                        candidates.append((profile, entity))

            if not candidates:
                scope_msg = (
                    f" dentro del perfil '{resolved_profile.get('name')}'" if resolved_profile else ""
                )
                raise ValueError(
                    f"No se encontro la entidad '{raw_entity}'{scope_msg}. Use 'entityprofile_list' "
                    "para ver las disponibles."
                )
            if len(candidates) > 1:
                options = "; ".join(
                    f"perfil '{p.get('name')}' (id {p.get('id')}) -> entidad id {e.get('id')}"
                    for p, e in candidates
                )
                raise ValueError(
                    f"El nombre de entidad '{raw_entity}' es ambiguo: coincide con {len(candidates)} "
                    f"perfil(es)/entidad(es) ({options}). Indique 'profile_id' o el id numerico de la "
                    "entidad para desambiguar."
                )
            matched_profile, matched_entity = candidates[0]
            resolved_entity_id = matched_entity.get("id")
            if resolved_profile_id is None:
                resolved_profile_id = matched_profile.get("id")
                self._resolution_notes.append(
                    f"entity_id: nombre de entidad '{raw_entity}' resuelto al perfil "
                    f"'{matched_profile.get('name')}' (id {resolved_profile_id}) y entidad id "
                    f"{resolved_entity_id}."
                )
            else:
                self._resolution_notes.append(
                    f"entity_id: nombre de entidad '{raw_entity}' resuelto a id {resolved_entity_id}."
                )

        self._resolved_entity_id = resolved_entity_id
        self._resolved_profile_id = resolved_profile_id

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
        if self._resolution_notes:
            payload["resolution_notes"] = list(self._resolution_notes)
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
