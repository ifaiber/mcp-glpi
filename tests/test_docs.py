import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_claude_config_json_is_valid():
    config_path = REPO_ROOT / 'examples' / 'claude_desktop_config.json'
    data = json.loads(config_path.read_text(encoding='utf-8'))
    assert 'mcpServers' in data
    server = data['mcpServers'].get('mcp-glpi')
    assert server is not None
    assert server['command']
    assert server['cwd']
    assert server['args'][0] == '-m'


def test_markdown_documents_have_headings():
    markdown_paths = list(REPO_ROOT.glob('*.md'))
    assert markdown_paths, 'No markdown files found'
    for path in markdown_paths:
        content = path.read_text(encoding='utf-8').strip()
        assert content
        assert '#' in content, f'Expected at least one heading in {path.name}'


def test_create_and_update_change_schema_expose_pr_links():
    import mcp_glpi.GLPITools as tools

    def get_tool_schema(name):
        tool = next(t for t in tools.tools if t.name == name)
        return tool.inputSchema

    create_schema = get_tool_schema('create_change')
    update_schema = get_tool_schema('update_change')

    for schema in (create_schema, update_schema):
        properties = schema['properties']
        assert 'pr_links' in properties
        assert schema.get('required') and 'pr_links' not in schema['required']
        pr_links = properties['pr_links']
        any_of_types = {option['type'] for option in pr_links['anyOf']}
        assert {'string', 'array'}.issubset(any_of_types)
        assert any_of_types.intersection({'null'})


def test_published_tools_match_handler_commands():
    import mcp_glpi.GLPITools as tools
    from mcp_glpi.GLPiHandler import COMMAND_HANDLERS
    from mcp_glpi.tool_catalog import TOOL_SPECS

    published = {tool.name for tool in tools.tools}
    catalog_names = {spec.name for spec in TOOL_SPECS}

    assert published == catalog_names
    assert published == set(COMMAND_HANDLERS)


def test_tool_catalog_handlers_exist():
    from mcp_glpi.GLPiHandler import CommandHandler
    from mcp_glpi.tool_catalog import TOOL_SPECS

    for spec in TOOL_SPECS:
        assert hasattr(CommandHandler, spec.handler_name), spec.handler_name
