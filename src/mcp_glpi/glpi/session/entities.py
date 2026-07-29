"""Session active-entity operations."""

from typing import Any, Dict, List, Optional

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


def change_active_entity_data(
    entity_id: Any,
    recursive: Optional[bool] = None,
) -> Dict[str, Any]:
    from ..shared import ensure_non_negative_int

    entity_id_int = ensure_non_negative_int(entity_id, "entity_id")

    with open_handler() as handler:
        handler.change_active_entity(entity_id_int, is_recursive=recursive)
        active_entities = handler.get_active_entities()

    return {
        "entity_id": entity_id_int,
        "recursive": recursive,
        "active_entities": active_entities,
    }
