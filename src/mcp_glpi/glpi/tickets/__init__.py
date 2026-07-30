"""Ticket facade exports."""

from .common import (
    DEFAULT_FIELDS,
    GLPIRequestHandler,
    IMPACT_LABELS,
    PRIORITY_LABELS,
    RequestHandler,
    STATUS_LABELS,
    URGENCY_LABELS,
    TicketCreationResult,
    TicketList,
    TicketMutationResult,
    _normalize_enum_value,
)
from .create import create_ticket
from .read import all_tickets, fetch_tickets, list_tickets_as_table
from .save import save_ticket
from .update import update_ticket

__all__ = [
    "DEFAULT_FIELDS",
    "IMPACT_LABELS",
    "PRIORITY_LABELS",
    "RequestHandler",
    "STATUS_LABELS",
    "URGENCY_LABELS",
    "TicketCreationResult",
    "TicketList",
    "TicketMutationResult",
    "_normalize_enum_value",
    "all_tickets",
    "create_ticket",
    "fetch_tickets",
    "list_tickets_as_table",
    "save_ticket",
    "update_ticket",
]
