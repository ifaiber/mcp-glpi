from glpi_client import RequestHandler
from common.config import get_config

config = get_config()


def all_tickets():
    with RequestHandler(config.url, config.app_token, config.user_token) as handler:
        return handler.get_all_tickets()