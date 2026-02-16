from glpi_client.core.client import RequestHandler
from glpi_client.core.session import SessionManager
import logging

# Configurar logging detallado
#logging.basicConfig(level=logging.DEBUG)

def main():
    print ("Inicio de session")

    with RequestHandler("http://grit.ideasfractal.com", "xxxxxx", "xxxxx") as handler:
        #valor = handler.add_items("Change", { "name": "Cambio desde API", "content": "Creado desde API", "urgency": 3, "priority": 4, "checklistcontent": "xxxx", "impactcontent": "sssp" } )

        """
        result = handler.add_items(f"Change/1411/Change_User", [
            { # Asignar como tipo follower
                "changes_id": 1411, 
                "users_id": 18,
                "type": 1
            },
            { # Asignar como tipo assigner
                "changes_id": 1411,
                "users_id": 18,
                "type": 2
            }
        ])"""

        """result = handler.add_items(f"Change/1411/Change_Group", [
            {
                "changes_id": 1411,
                "groups_id": 5,
                "type": 2
            }
        ])"""
        

        print (result)
        

if __name__ == "__main__":
    main()