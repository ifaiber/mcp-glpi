from glpi_client import RequestHandler
from common.config import get_config

config = get_config()

def get_full_session():
    
    with RequestHandler(config.url, config.app_token, config.user_token) as handler:
        session = handler.get_full_session()
        session_data = {
            "sessionId": handler.session_token,
            "sessionInfo": {
                "username": session.get('glpiname'),
                "name": session.get('glpifirstname'),
                "lastname": session.get('glpirealname'),
                "entityDefault": session.get('glpiactive_entity_name')
            }
        }
         # Formato bonito para presentación
        formatted_output = f"""
╔══════════════════════════════════════╗
║            SESIÓN GLPI               ║
╠══════════════════════════════════════╣
║ ID de Sesión: {session_data['sessionId'][:20]}... ║
║                                      ║
║ INFORMACIÓN DEL USUARIO:             ║
║ ├─ Usuario: {session_data['sessionInfo']['username'] or 'N/A':25} ║
║ ├─ Nombre: {session_data['sessionInfo']['name'] or 'N/A':26} ║
║ ├─ Apellido: {session_data['sessionInfo']['lastname'] or 'N/A':24} ║
║ └─ Entidad: {session_data['sessionInfo']['entityDefault'] or 'N/A':25} ║
╚══════════════════════════════════════╝
"""
        return formatted_output.strip()
