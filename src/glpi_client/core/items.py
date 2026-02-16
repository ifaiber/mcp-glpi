"""
Operaciones CRUD para ítems de GLPI.
"""

import logging
from typing import Dict, Any, List, Union, Tuple, Optional

import requests
from .session import SessionManager
from ..exceptions import GLPIError
from ..models import SortOrder
from ..utils import add_criteria_to_parameters

logger = logging.getLogger(__name__)


class ItemManager(SessionManager):
    """Maneja las operaciones CRUD de ítems en GLPI."""

    def get_item(
        self,
        item_type: str,
        id_: int,
        expand_dropdowns: bool = False,
        get_hateoas: bool = True,
        get_sha1: bool = False,
        with_devices: bool = False,
        with_disks: bool = False,
        with_softwares: bool = False,
        with_connections: bool = False,
        with_networkports: bool = False,
        with_infocoms: bool = False,
        with_contracts: bool = False,
        with_documents: bool = False,
        with_tickets: bool = False,
        with_problems: bool = False,
        with_changes: bool = False,
        with_notes: bool = False,
        with_logs: bool = False,
        add_key_names: List[str] = None,
    ) -> Dict[str, Any]:
        """Retorna una instancia de item_type identificada por id."""
        if not get_hateoas:
            get_hateoas = 0
        request_parameters = self._get_request_parameters(
            rename={"add_key_names": "add_keys_names"}
        )
        try:
            return self._get_json(f"{item_type}/{id_}", parameters=request_parameters)
        except requests.HTTPError as err:
            raise GLPIError(f"{item_type} with id={id_} was not found") from err

    def get_many_items(
        self,
        item_type: str,
        expand_dropdowns: bool = False,
        get_hateoas: bool = True,
        only_id: bool = False,
        range_: Tuple[int, int] = None,
        sort_by: str = None,
        order: SortOrder = None,
        filter_by: Dict[str, str] = None,
        is_deleted: bool = False,
        add_key_names: List[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retorna un conjunto de ítems identificados por item_type."""
        if range_ is not None:
            range_ = "-".join(str(r) for r in range_)
        if is_deleted:
            is_deleted = 1
        if not get_hateoas:
            get_hateoas = 0
        request_parameters = self._get_request_parameters(
            rename={
                "range_": "range",
                "add_key_names": "add_keys_names",
                "sort_by": "sort",
            }
        )
        if filter_by:
            for name in filter_by:
                request_parameters.append((f"searchText[{name}]", filter_by[name]))
        return self._get_json(f"{item_type}/", parameters=request_parameters)

    def get_sub_items(
        self,
        item_type: str,
        item_id: int,
        sub_item_type: str,
        expand_dropdowns: bool = False,
        get_hateoas: bool = True,
        only_id: bool = False,
        range_: Tuple[int, int] = None,
        sort_by: str = None,
        order: SortOrder = None,
        add_key_names: List[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retorna sub-ítems del sub_item_type para el item_id identificado."""
        if range_ is not None:
            range_ = "-".join(str(r) for r in range_)
        if not get_hateoas:
            get_hateoas = 0
        request_parameters = self._get_request_parameters(
            rename={
                "range_": "range",
                "add_key_names": "add_keys_names",
                "sort_by": "sort",
            }
        )
        return self._get_json(
            f"{item_type}/{item_id}/{sub_item_type}", parameters=request_parameters
        )

    def add_items(
        self, item_type: str, data: Union[Dict[str, Any], List[Dict[str, Any]]]
    ) -> Union[Dict[str, Any], List[Dict[str, Any]]]:
        """Agrega uno o varios ítems."""
        response = self._do_method("post", f"{item_type}", data={"input": data})
        return response.json()

    def update_items(
        self, item_type: str, data: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Actualiza los atributos de varios ítems."""
        response = self._do_method("patch", f"{item_type}", data={"input": data})
        return response.json()

    def delete_items(
        self, item_type: str, ids: List[int], purge=False, log=True
    ) -> List[Dict[str, Any]]:
        """Elimina una lista de objetos existentes."""
        data = {"input": {"id": id_ for id_ in ids}}
        if purge:
            data["force_purge"] = True
        if not log:
            data["force_no_history"] = True
        response = self._do_method("delete", f"{item_type}", data=data)
        return response.json()

    # Métodos de conveniencia
    def create_change(self, name: str, content: str = "", **kwargs) -> Dict[str, Any]:
        """Método de conveniencia para crear un cambio."""
        change_data = {
            "name": name,
            "content": content,
            **kwargs
        }
        return self.add_items("Change", change_data)

    def create_ticket(self, name: str, content: str = "", **kwargs) -> Dict[str, Any]:
        """Método de conveniencia para crear un ticket."""
        ticket_data = {
            "name": name,
            "content": content,
            **kwargs
        }
        return self.add_items("Ticket", ticket_data)

    def get_all_changes(self, **kwargs) -> List[Dict[str, Any]]:
        """Método de conveniencia para obtener todos los cambios."""
        return self.get_many_items("Change", **kwargs)

    def get_all_tickets(self, **kwargs) -> List[Dict[str, Any]]:
        """Método de conveniencia para obtener todos los tickets."""
        return self.get_many_items("Ticket", **kwargs)