"""Document link operations (Document_Item)."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..generic import ensure_supported_itemtype
from ..shared import (
    ensure_positive_int,
    merge_non_null_values,
    prepare_bool_flag,
    switch_active_entity,
    switch_active_profile,
)
from .common import FileMutationResult, open_handler


def link_item(
    document_id: Any,
    item_type: Any,
    item_id: Any,
    *,
    additional_fields: Optional[Dict[str, Any]] = None,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
) -> FileMutationResult:
    document_id_int = ensure_positive_int(document_id, "document_id")
    item_type_str = ensure_supported_itemtype(item_type)
    item_id_int = ensure_positive_int(item_id, "item_id")

    payload: Dict[str, Any] = {
        "documents_id": document_id_int,
        "itemtype": item_type_str,
        "items_id": item_id_int,
    }
    merge_non_null_values(payload, additional_fields)

    with open_handler() as handler:
        switch_active_profile(handler, profile_id)
        switch_active_entity(handler, entity_id)
        response = handler.add_items("Document_Item", payload)

    return FileMutationResult(
        action="file_link",
        document_id=document_id_int,
        description=f"Linked document {document_id_int} to {item_type_str} {item_id_int}",
        payload=payload,
        response=response,
    )


def unlink_item(
    document_id: Any,
    link_id: Any,
    *,
    purge: bool | Any = False,
    keep_history: bool | Any = True,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
) -> FileMutationResult:
    document_id_int = ensure_positive_int(document_id, "document_id")
    link_id_int = ensure_positive_int(link_id, "link_id")
    purge_flag = bool(prepare_bool_flag(purge))
    keep_history_flag = bool(prepare_bool_flag(keep_history))

    with open_handler() as handler:
        switch_active_profile(handler, profile_id)
        switch_active_entity(handler, entity_id)
        response = handler.delete_items(
            "Document_Item",
            [link_id_int],
            purge=purge_flag,
            log=keep_history_flag,
        )

    return FileMutationResult(
        action="file_unlink",
        document_id=document_id_int,
        description=f"Unlinked document {document_id_int} from relation {link_id_int}",
        payload={"link_id": link_id_int, "purge": purge_flag, "keep_history": keep_history_flag},
        response=response,
    )
