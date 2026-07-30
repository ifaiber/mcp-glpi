import pytest

from mcp_glpi import resource_catalog


_ALL_URIS = (
    "mcp-glpi://docs/glpi-items",
    "mcp-glpi://docs/glpi-tools",
    "mcp-glpi://docs/glpi-entity-profile-resolution",
)


def test_resource_specs_include_all_documents():
    uris = {spec.uri for spec in resource_catalog.RESOURCE_SPECS}
    for uri in _ALL_URIS:
        assert uri in uris


def test_find_resource_returns_spec_with_existing_path():
    for uri in _ALL_URIS:
        spec = resource_catalog.find_resource(uri)
        assert spec.path.is_file()
        assert spec.mime_type == "text/markdown"


def test_glpi_items_resource_covers_generic_tools():
    text = resource_catalog.read_resource_text("mcp-glpi://docs/glpi-items")
    assert "item_list" in text
    assert "item_get" in text
    assert "item_delete" in text
    assert "item_subitem_list" in text
    assert "ticket_add" not in text


def test_glpi_tools_resource_covers_specific_tools():
    text = resource_catalog.read_resource_text("mcp-glpi://docs/glpi-tools")
    assert "ticket_add" in text
    assert "file_upload" in text
    assert "change_ticket_link" in text


def test_glpi_entity_profile_resolution_resource_covers_both_cases():
    text = resource_catalog.read_resource_text("mcp-glpi://docs/glpi-entity-profile-resolution")
    assert "resolution_notes" in text
    assert "profile_list" in text
    assert "ambigu" in text.lower()


def test_read_resource_text_rejects_unknown_uri():
    with pytest.raises(ValueError, match="Unknown resource URI"):
        resource_catalog.read_resource_text("mcp-glpi://docs/does-not-exist")


def test_server_registers_resource_handlers():
    import mcp.types as types
    from mcp_glpi.server import GLPIMCPServer

    server = GLPIMCPServer()

    assert types.ListResourcesRequest in server.app.request_handlers
    assert types.ReadResourceRequest in server.app.request_handlers
