"""Shared file-specific helpers and exported result types."""

from __future__ import annotations

import logging

from glpi_client import RequestHandler as GLPIRequestHandler

from ...common.config import get_config
from ..shared import EntityMutationResult

logger = logging.getLogger(__name__)


def open_handler():
    from . import RequestHandler

    config = get_config()
    return RequestHandler(config.url, config.app_token, config.user_token, False)


class FileMutationResult(EntityMutationResult):
    def __init__(
        self,
        action: str,
        document_id: int,
        description: str,
        payload,
        response,
    ):
        super().__init__(
            action=action,
            entity_id_field="document_id",
            entity_id=document_id,
            description=description,
            payload=payload,
            response=response,
        )


RequestHandler = GLPIRequestHandler
