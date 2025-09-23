"""Convenience helpers for GLPI change operations."""

from typing import Dict, Optional, Sequence, Union

from glpi_client import SortOrder

from .tickets import DEFAULT_FIELDS, fetch_tickets


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
    """Retrieve tickets from GLPI with a configurable presentation."""

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
