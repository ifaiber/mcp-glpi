"""Change solution operations."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..shared import ensure_non_empty_text, ensure_positive_int, merge_non_null_values
from .common import ChangeMutationResult, open_handler


def add_solution(
    change_id: Any,
    content: Any,
    *,
    solution_type_id: Any = None,
    additional_fields: Optional[Dict[str, Any]] = None,
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
        response = handler.add_items("ITILSolution", payload)

    return ChangeMutationResult(
        action="add_change_solution",
        change_id=change_id_int,
        description=f"Added solution to change {change_id_int}",
        payload=payload,
        response=response,
    )
