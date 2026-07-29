"""Ticket read/list operations."""

from __future__ import annotations

from typing import Dict, Optional, Sequence, Union

from glpi_client import SortOrder

from ..shared import fetch_paginated_items
from .common import DEFAULT_FIELDS, TicketList, open_handler


def fetch_tickets(
    limit: Optional[int] = 20,
    offset: int = 0,
    sort_by: str = "date_mod",
    order: Union[SortOrder, str] = SortOrder.Descending,
    filters: Optional[Dict[str, str]] = None,
    expand_dropdowns: bool = False,
    include_deleted: bool = False,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
) -> TicketList:
    items, response_range = fetch_paginated_items(
        "Ticket",
        open_handler,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        order=order,
        filters=filters or None,
        expand_dropdowns=expand_dropdowns,
        include_deleted=include_deleted,
        entity_id=entity_id,
        profile_id=profile_id,
    )
    return TicketList(items=items, response_range=response_range)


def list_tickets_as_table(
    limit: Optional[int] = 20,
    offset: int = 0,
    sort_by: str = "date_mod",
    order: Union[SortOrder, str] = SortOrder.Descending,
    filters: Optional[Dict[str, str]] = None,
    expand_dropdowns: bool = False,
    include_deleted: bool = False,
    fields: Sequence[str] = DEFAULT_FIELDS,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
) -> str:
    ticket_list = fetch_tickets(
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        order=order,
        filters=filters,
        expand_dropdowns=expand_dropdowns,
        include_deleted=include_deleted,
        entity_id=entity_id,
        profile_id=profile_id,
    )
    return ticket_list.to_table(fields)


def all_tickets(
    limit: Optional[int] = 20,
    offset: int = 0,
    sort_by: str = "date_mod",
    order: Union[SortOrder, str] = SortOrder.Descending,
    filters: Optional[Dict[str, str]] = None,
    expand_dropdowns: bool = False,
    include_deleted: bool = False,
    output: str = "dict",
    fields: Optional[Sequence[str]] = None,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
):
    ticket_list = fetch_tickets(
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        order=order,
        filters=filters,
        expand_dropdowns=expand_dropdowns,
        include_deleted=include_deleted,
        entity_id=entity_id,
        profile_id=profile_id,
    )

    return ticket_list.respond(output, fields, default_fields=DEFAULT_FIELDS)
