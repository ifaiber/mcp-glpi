"""File (Document) facade exports."""

from .common import FileMutationResult, GLPIRequestHandler, RequestHandler
from .download import download_document
from .links import link_item, unlink_item
from .upload import upload_document

__all__ = [
    "FileMutationResult",
    "GLPIRequestHandler",
    "RequestHandler",
    "download_document",
    "link_item",
    "unlink_item",
    "upload_document",
]
