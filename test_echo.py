from common.config import get_config
import logging
import glpi.changes as changes

logging.basicConfig(level=logging.DEBUG)
logging
print(changes.all_tickets())