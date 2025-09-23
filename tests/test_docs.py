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
