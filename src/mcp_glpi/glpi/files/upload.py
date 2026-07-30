"""Document upload operations."""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from ..shared import (
    EntityCreationResult,
    ensure_non_empty_text,
    merge_non_null_values,
    switch_active_entity,
    switch_active_profile,
)
from .common import open_handler


def upload_document(
    file_path: Any,
    *,
    name: Optional[str] = None,
    file_name: Optional[str] = None,
    additional_fields: Optional[Dict[str, Any]] = None,
    entity_id: Optional[int] = None,
    profile_id: Optional[int] = None,
) -> EntityCreationResult:
    path = ensure_non_empty_text(file_path, "file_path")
    if not os.path.isfile(path):
        raise ValueError(f"file_path '{path}' does not exist or is not a file")

    resolved_file_name = file_name or os.path.basename(path)
    extra_input: Dict[str, Any] = {}
    merge_non_null_values(extra_input, additional_fields)

    with open(path, "rb") as fh:
        with open_handler() as handler:
            switch_active_profile(handler, profile_id)
            switch_active_entity(handler, entity_id)
            response = handler.upload_document(
                file=fh,
                name=name,
                file_name=resolved_file_name,
                extra_input=extra_input or None,
            )

    return EntityCreationResult(
        entity_label="Document",
        payload={"file_path": path, "name": name, "file_name": resolved_file_name},
        response=response,
    )
