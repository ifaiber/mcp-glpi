"""Ticket facade exports."""

from .assignments import assign_ticket_groups, assign_ticket_users
from .comments import add_followup
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
from .delete import delete_ticket
from .links import link_change, unlink_change
from .read import all_tickets, fetch_tickets, list_tickets_as_table
from .solutions import add_solution
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
    "add_followup",
    "add_solution",
    "all_tickets",
    "assign_ticket_groups",
    "assign_ticket_users",
    "create_ticket",
    "delete_ticket",
    "fetch_tickets",
    "link_change",
    "list_tickets_as_table",
    "unlink_change",
    "update_ticket",
]
