"""Session active-entity operations."""

from typing import Any, Dict, List

from .common import open_handler


def _simplify_entities(entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "id": entity.get("id"),
            "name": entity.get("name"),
            "completename": entity.get("completename"),
            "is_recursive": bool(entity.get("is_recursive")),
        }
        for entity in entities
    ]


def get_my_entities_data(recursive: bool = False) -> List[Dict[str, Any]]:
    with open_handler() as handler:
        entities = handler.get_my_entities(recursive=recursive)

    return _simplify_entities(entities)
