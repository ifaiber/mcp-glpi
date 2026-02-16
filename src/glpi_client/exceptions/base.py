"""
Excepciones base para GLPI Wrapper.
"""


class GLPIError(Exception):
    """Excepción base para todas las operaciones de GLPI.
    
    Esta es la excepción padre de todas las excepciones específicas del wrapper.
    Puede capturarse para manejar cualquier error relacionado con GLPI.
    """
    pass