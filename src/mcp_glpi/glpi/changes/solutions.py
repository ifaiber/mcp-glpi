"""Change solution operations."""

from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Union

from glpi_client import SortOrder

from ..shared import (
    EntityList,
    ensure_non_empty_text,
    ensure_positive_int,
    fetch_paginated_subitems,
    merge_non_null_values,
    prepare_generic_item,
    switch_active_entity,
    switch_active_profile,
)
from .common import ChangeMutationResult, open_handler

SOLUTION_DEFAULT_FIELDS: Sequence[str] = (
    "id",
    "date_creation",
    "users_id",
    "solutiontypes_id",
    "status",
    "content",
)


def add_solution(
    change_id: Any,
    content: Any,
    *,
    solution_type_id: Any = None,
    additional_fields: Optional[Dict[str, Any]] = None,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
) -> ChangeMutationResult:
    change_id_int = ensure_positive_int(change_id, "change_id")
    solution_text = ensure_non_empty_text(content, "content")
    payload: Dict[str, Any] = {
        "itemtype": "Change",
        "items_id": change_id_int,
        "content": solution_text,
    }
    if solution_type_id is not None:
        payload["solutiontypes_id"] = ensure_positive_int(solution_type_id, "solution_type_id")

    merge_non_null_values(payload, additional_fields)

    with open_handler() as handler:
        switch_active_profile(handler, profile_id)
        switch_active_entity(handler, entity_id)
        response = handler.add_items("ITILSolution", payload)

    return ChangeMutationResult(
        action="change_solution_add",
        change_id=change_id_int,
        description=f"Added solution to change {change_id_int}",
        payload=payload,
        response=response,
    )


def list_solutions(
    change_id: Any,
    *,
    limit: Optional[int] = 20,
    offset: int = 0,
    sort_by: Optional[str] = None,
    order: Union[SortOrder, str] = SortOrder.Descending,
    output: str = "dict",
    fields: Optional[Sequence[str]] = None,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
):
    change_id_int = ensure_positive_int(change_id, "change_id")
    items, response_range = fetch_paginated_subitems(
        "Change",
        change_id_int,
        "ITILSolution",
        open_handler,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        order=order,
        entity_id=entity_id,
        profile_id=profile_id,
    )
    solution_list = EntityList(
        item_key="solutions", items=items, response_range=response_range, prepare_item=prepare_generic_item
    )
    return solution_list.respond(output, fields, default_fields=SOLUTION_DEFAULT_FIELDS)
