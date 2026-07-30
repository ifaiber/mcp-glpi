"""Document download operations."""

from __future__ import annotations

import os
from typing import Any, Optional

from ..shared import ensure_non_empty_text, ensure_positive_int, switch_active_entity, switch_active_profile
from .common import FileMutationResult, open_handler


def download_document(
    document_id: Any,
    destination_path: Any,
    *,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
) -> FileMutationResult:
    document_id_int = ensure_positive_int(document_id, "document_id")
    path = ensure_non_empty_text(destination_path, "destination_path")

    with open_handler() as handler:
        switch_active_profile(handler, profile_id)
        switch_active_entity(handler, entity_id)
        if os.path.isdir(path):
            document = handler.get_item("Document", document_id_int)
            filename = document.get("filename") or f"document-{document_id_int}"
            path = os.path.join(path, filename)
        content = handler.download_document(document_id_int)

    parent_dir = os.path.dirname(path)
    if parent_dir:
        os.makedirs(parent_dir, exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(content)

    return FileMutationResult(
        action="file_download",
        document_id=document_id_int,
        description=f"Downloaded document {document_id_int} to {path} ({len(content)} bytes)",
        payload={"destination_path": path},
        response={"bytes_written": len(content)},
    )
