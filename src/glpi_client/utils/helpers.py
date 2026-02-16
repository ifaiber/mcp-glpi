"""
Funciones auxiliares para GLPI Wrapper.
"""

from typing import Any, List, Tuple, Dict, Union


def add_criteria_to_parameters(
    criteria: Union[Dict[str, Any], List[Any]], 
    parameters: List[Tuple[str, Any]], 
    father: str = "criteria"
) -> None:
    """Agrega criterios de búsqueda a los parámetros del request.
    
    Esta función recursiva convierte estructuras anidadas de criterios
    en parámetros planos que pueden ser enviados en el query string.
    
    Parameters
    ----------
    criteria : Union[Dict[str, Any], List[Any]]
        Los criterios a convertir
    parameters : List[Tuple[str, Any]]
        Lista de parámetros donde agregar los criterios convertidos
    father : str, default "criteria"
        Prefijo para los parámetros generados
        
    Raises
    ------
    NotImplementedError
        Si el tipo de criteria no es soportado
    """
    if isinstance(criteria, dict):
        for key, value in criteria.items():
            path = f"{father}[{key}]"
            if isinstance(value, list):
                add_criteria_to_parameters(value, parameters, path)
            else:
                parameters.append((path, value))
    elif isinstance(criteria, list):
        for i in range(len(criteria)):
            add_criteria_to_parameters(criteria[i], parameters, f"{father}[{i}]")
    else:
        raise NotImplementedError(
            f"add_criteria_to_parameters cannot handle objects of type {type(criteria)}"
        )