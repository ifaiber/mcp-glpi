"""Session profile operations."""

from typing import Any, Dict, List

from .common import open_handler


def _simplify_profiles(profiles: List[Dict[str, Any]]) -> Dict[str, Any]:
    simplified_profiles = []
    for profile in profiles:
        entities = profile.get("entities") or []
        simplified_profiles.append(
            {
                "id": profile.get("id"),
                "name": profile.get("name"),
                "entities": [
                    {
                        "id": entity.get("id"),
                        "name": entity.get("name"),
                        "is_recursive": bool(entity.get("is_recursive")),
                    }
                    for entity in entities
                ],
            }
        )
    return simplified_profiles


def get_my_profiles_data() -> List[Dict[str, Any]]:
    with open_handler() as handler:
        profiles = handler.get_my_profiles()

    return _simplify_profiles(profiles)
