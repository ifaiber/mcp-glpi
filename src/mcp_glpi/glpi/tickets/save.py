"""Ticket create-or-update: a single entry point selecting behavior by ``id``."""

from __future__ import annotations

from typing import Any, Dict, Optional, Union

from ..shared import ensure_positive_int, merge_non_null_values
from .common import TicketCreationResult, TicketMutationResult
from .create import create_ticket
from .update import update_ticket


def save_ticket(
    *,
    id: Any = None,
    name: Any = None,
    content: Any = None,
    status: Any = None,
    impact: Any = None,
    priority: Any = None,
    urgency: Any = None,
    category_id: Any = None,
    additional_fields: Optional[Dict[str, Any]] = None,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
) -> Union[TicketCreationResult, TicketMutationResult]:
    """Create a ticket when ``id`` is omitted, update it otherwise.

    Without ``id``: same as ``create_ticket`` (``name`` is required).
    With ``id``: builds a ``fields`` dict from whichever named parameters
    were actually given (plus ``additional_fields``) and calls
    ``update_ticket`` -- so the same friendly parameter names work for both
    creating and updating instead of requiring raw GLPI field names on update.
    """
    if id is None:
        if not name or not str(name).strip():
            raise ValueError("name is required to create a ticket")
        return create_ticket(
            name=name,
            content="" if content is None else str(content),
            status=status,
            impact=impact,
            priority=priority,
            urgency=urgency,
            category_id=category_id,
            entity_id=entity_id,
            profile_id=profile_id,
            additional_fields=additional_fields,
        )

    ticket_id_int = ensure_positive_int(id, "id")
    fields: Dict[str, Any] = {}
    if name is not None:
        fields["name"] = name
    if content is not None:
        fields["content"] = content
    if status is not None:
        fields["status"] = status
    if impact is not None:
        fields["impact"] = impact
    if priority is not None:
        fields["priority"] = priority
    if urgency is not None:
        fields["urgency"] = urgency
    if category_id is not None:
        fields["itilcategories_id"] = category_id
    merge_non_null_values(fields, additional_fields)

    return update_ticket(
        ticket_id=ticket_id_int,
        fields=fields,
        entity_id=entity_id,
        profile_id=profile_id,
    )
