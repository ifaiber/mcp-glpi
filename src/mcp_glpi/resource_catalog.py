"""Single source of truth for MCP resource metadata."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

RESOURCES_DIR = Path(__file__).parent / "resources"


@dataclass(frozen=True)
class ResourceSpec:
    uri: str
    name: str
    description: str
    mime_type: str
    path: Path


RESOURCE_SPECS: List[ResourceSpec] = [
    ResourceSpec(
        uri="mcp-glpi://docs/glpi-items",
        name="glpi-items",
        description=(
            "Guia de las herramientas genericas de elementos GLPI: descubrir "
            "itemtype/subtype (item_type_list/item_subtype_list), listar/"
            "consultar/eliminar de forma generica (item_list/item_get/"
            "item_delete) y listar sub-elementos (item_subitem_list), con su "
            "matriz de rutas/capacidades. Cubre Ticket/Change/Document y "
            "activos/gestion (Computer, Monitor, Software, SoftwareVersion, "
            "Project, ProjectTask, KnowbaseItem, Reminder, ContractType, "
            "Manufacturer, DeviceSimcard)."
        ),
        mime_type="text/markdown",
        path=RESOURCES_DIR / "glpi-items.md",
    ),
    ResourceSpec(
        uri="mcp-glpi://docs/glpi-tools",
        name="glpi-tools",
        description=(
            "Guia de las herramientas especificas de tickets y cambios "
            "(crear/actualizar/eliminar/seguimientos/soluciones/asignaciones/"
            "relaciones) y de archivos (file_upload/file_download/file_link/"
            "file_unlink), con su matriz de rutas/capacidades."
        ),
        mime_type="text/markdown",
        path=RESOURCES_DIR / "glpi-tools.md",
    ),
    ResourceSpec(
        uri="mcp-glpi://docs/glpi-entity-profile-resolution",
        name="glpi-entity-profile-resolution",
        description=(
            "Explica que pasa cuando 'entity_id'/'profile_id' se dan como "
            "nombre en vez de id numerico: resolucion automatica via "
            "profile_list, seleccion de la primera entidad de un perfil "
            "cuando falta 'entity_id', busqueda de entidad entre perfiles "
            "cuando falta 'profile_id', y manejo de nombres ambiguos o no "
            "encontrados como error de validacion."
        ),
        mime_type="text/markdown",
        path=RESOURCES_DIR / "glpi-entity-profile-resolution.md",
    ),
]


def find_resource(uri: str) -> ResourceSpec:
    for spec in RESOURCE_SPECS:
        if spec.uri == uri:
            return spec
    raise ValueError(f"Unknown resource URI: {uri}")


def read_resource_text(uri: str) -> str:
    spec = find_resource(uri)
    return spec.path.read_text(encoding="utf-8")
