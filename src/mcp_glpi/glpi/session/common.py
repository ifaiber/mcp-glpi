"""Session shared helpers."""

from glpi_client import RequestHandler as GLPIRequestHandler

from ...common.config import get_config


def open_handler():
    from . import RequestHandler

    config = get_config()
    return RequestHandler(config.url, config.app_token, config.user_token, False)


RequestHandler = GLPIRequestHandler
