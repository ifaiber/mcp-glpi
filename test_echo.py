import logging

import glpi.changes as changes
import glpi.tickets as tickets


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    print("Tickets:\n")
    print(tickets.all_tickets(limit=10, output="table"))
    print("\nChanges:\n")
    print(changes.all_changes(limit=10, output="table"))
