"""
Operaciones de búsqueda en GLPI.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple

from .items import ItemManager
from ..models import SortOrder
from ..utils import add_criteria_to_parameters

logger = logging.getLogger(__name__)


class SearchManager(ItemManager):
    """Maneja las operaciones de búsqueda en GLPI."""

    def get_search_options(
        self, item_type: str, raw: bool = False, pretty: bool = False
    ) -> Dict[str, Any]:
        """Lista las opciones de búsqueda del itemtype proporcionado."""
        def recurse_parts(
            part_name: str, part_data: Dict[str, Any], rest: List[str], end: Any, id_: int
        ):
            if part_name not in part_data:
                part_data[part_name] = {}
            if len(rest) == 0:
                part_data[part_name] = end
                end["id"] = id_
                return
            name = rest.pop(0)
            recurse_parts(name, part_data[part_name], rest, end, id_)

        request_parameters = self._get_request_parameters()
        json_data = self._get_json(
            f"listSearchOptions/{item_type}", parameters=request_parameters
        )
        if not pretty:
            return json_data
        else:
            result = {}
            for k, v in json_data.items():
                if k.isdecimal():
                    parts = v["uid"].split(".")
                    head = parts.pop(0)
                    recurse_parts(head, result, parts, v, int(k))
            return result

    def search_items(
        self,
        item_type: str,
        filters: List[Dict[str, Any]] = None,
        sort_by_id: int = None,
        order: SortOrder = None,
        range_: Tuple[int, int] = None,
        force_display: List[int] = None,
        raw_data: bool = False,
        with_indexes: bool = False,
        uid_cols: bool = False,
        give_items: bool = False,
    ) -> Dict[str, Any]:
        """Busca ítems según algunos criterios."""
        if range_ is not None:
            range_ = "-".join(str(r) for r in range_)
        criteria = filters if filters else []
        filters = None
        request_parameters = self._get_request_parameters(
            rename={
                "sort_by_id": "sort",
                "range_": "range",
                "force_display": "forcedisplay",
                "raw_data": "rawdata",
                "with_indexes": "withindexes",
                "give_items": "giveItems",
            }
        )
        add_criteria_to_parameters(criteria, request_parameters)
        json_data = self._get_json(f"search/{item_type}", parameters=request_parameters)
        if not with_indexes:
            for d in json_data.get("data", []):
                self._keys_to_int(d)
            for d in json_data.get("data_html", []):
                self._keys_to_int(d)
        return json_data

    def search_by_name(
        self, item_type: str, name: str, exact_match: bool = False
    ) -> Dict[str, Any]:
        """Buscar ítems por nombre."""
        search_value = f"^{name}$" if exact_match else name
        filters = [{
            "field": 1,  # Campo nombre típicamente tiene ID 1
            "searchtype": "equals" if exact_match else "contains",
            "value": search_value
        }]
        return self.search_items(item_type, filters=filters)