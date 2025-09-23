import logging

import glpi.changes as changes


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    tickets_table = changes.all_tickets(limit=10, output="table")
    print(tickets_table)
