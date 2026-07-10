"""Change delete operations."""

from __future__ import annotations

from typing import Any

from ..shared import ensure_positive_int, prepare_bool_flag
from .common import ChangeMutationResult, open_handler


def delete_change(
    change_id: Any,
    *,
    purge: bool | Any = False,
    keep_history: bool | Any = True,
) -> ChangeMutationResult:
    change_id_int = ensure_positive_int(change_id, "change_id")
    purge_flag = bool(prepare_bool_flag(purge))
    keep_history_flag = bool(prepare_bool_flag(keep_history))

    with open_handler() as handler:
        response = handler.delete_items(
            "Change",
            [change_id_int],
            purge=purge_flag,
            log=keep_history_flag,
        )

    return ChangeMutationResult(
        action="delete_change",
        change_id=change_id_int,
        description=f"Deleted change {change_id_int}",
        payload={"change_id": change_id_int, "purge": purge_flag, "keep_history": keep_history_flag},
        response=response,
    )
