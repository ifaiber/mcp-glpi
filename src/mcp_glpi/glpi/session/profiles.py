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


def _simplify_active_profile(active_profile: Dict[str, Any]) -> Dict[str, Any]:
    entities = active_profile.get("entities") or {}
    # getActiveProfile returns "entities" as a dict keyed by id, unlike
    # getMyProfiles' list-shaped "entities"; support both defensively.
    if isinstance(entities, dict):
        entities_list = list(entities.values())
    elif isinstance(entities, list):
        entities_list = entities
    else:
        entities_list = []
    return {
        "id": active_profile.get("id"),
        "name": active_profile.get("name"),
        "entities": [
            {
                "id": entity.get("id"),
                "name": entity.get("name"),
                "is_recursive": bool(entity.get("is_recursive")),
            }
            for entity in entities_list
        ],
    }


def change_active_profile_data(profile_id: Any) -> Dict[str, Any]:
    from ..shared import ensure_positive_int

    profile_id_int = ensure_positive_int(profile_id, "profile_id")

    with open_handler() as handler:
        handler.change_active_profile(profile_id_int)
        active_profile = handler.get_active_profile()

    return {
        "profile_id": profile_id_int,
        "active_profile": _simplify_active_profile(active_profile),
    }
