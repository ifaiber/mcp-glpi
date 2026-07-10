"""Ticket read/list operations."""

from __future__ import annotations

from typing import Dict, Optional, Sequence, Tuple, Union

from glpi_client import ResponseRange, SortOrder

from .common import DEFAULT_FIELDS, TicketList, open_handler


def fetch_tickets(
    limit: Optional[int] = 20,
    offset: int = 0,
    sort_by: str = "date_mod",
    order: Union[SortOrder, str] = SortOrder.Descending,
    filters: Optional[Dict[str, str]] = None,
    expand_dropdowns: bool = False,
    include_deleted: bool = False,
) -> TicketList:
    order_enum = SortOrder(order) if isinstance(order, str) else order
    range_tuple: Optional[Tuple[int, int]] = None
    if limit is not None and limit > 0:
        range_tuple = (offset, offset + limit - 1)
    filters_to_use = filters or None
    with open_handler() as handler:
        items = handler.get_many_items(
            "Ticket",
            expand_dropdowns=expand_dropdowns,
            sort_by=sort_by,
            order=order_enum,
            range_=range_tuple,
            filter_by=filters_to_use,
            is_deleted=include_deleted,
        )
        response_range: Optional[ResponseRange] = getattr(handler, "response_range", None)
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
) -> str:
    ticket_list = fetch_tickets(
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        order=order,
        filters=filters,
        expand_dropdowns=expand_dropdowns,
        include_deleted=include_deleted,
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
):
    ticket_list = fetch_tickets(
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        order=order,
        filters=filters,
        expand_dropdowns=expand_dropdowns,
        include_deleted=include_deleted,
    )

    selected_fields = fields or DEFAULT_FIELDS
    if output == "table":
        return ticket_list.to_table(selected_fields)
    if output == "raw":
        return ticket_list.items
    return ticket_list.as_dict(selected_fields)
