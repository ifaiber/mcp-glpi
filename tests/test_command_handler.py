import pytest

from mcp_glpi.GLPiHandler import CommandHandler
import glpi.session as glpi_session
import glpi.tickets as glpi_tickets
import glpi.changes as glpi_changes


class DummyResult:
    def __init__(self, summary_text='Ticket created (id=99): Demo', payload=None):
        self._summary_text = summary_text
        self._payload = payload or {'payload': {'name': 'Demo'}}

    def summary(self):
        return self._summary_text

    def as_dict(self):
        return self._payload


def _extract_text(response):
    assert response
    content = response[0]
    assert content.type == 'text'
    return content.text


def test_echo_command_returns_expected_text():
    response = CommandHandler('echo', {'message': 'hola'}).execute()
    assert _extract_text(response) == 'Echo: hola'


def test_unknown_command_returns_friendly_message():
    response = CommandHandler('nope').execute()
    assert _extract_text(response) == 'Herramienta desconocida: nope'


def test_validate_session_uses_session_module(monkeypatch):
    monkeypatch.setattr(glpi_session, 'get_full_session', lambda: 'OK')
    response = CommandHandler('validate_session').execute()
    assert _extract_text(response) == 'OK'


def test_list_tickets_normalises_arguments(monkeypatch):
    captured = {}

    def fake_all_tickets(**kwargs):
        captured.update(kwargs)
        return [{'id': 1}]

    monkeypatch.setattr(glpi_tickets, 'all_tickets', fake_all_tickets)

    response = CommandHandler(
        'list_tickets',
        {
            'limit': '5',
            'offset': '2',
            'expand_dropdowns': 'true',
            'include_deleted': '1',
            'filters': {'status': 'open'},
        },
    ).execute()

    text = _extract_text(response)
    assert text == "[{'id': 1}]"
    assert captured['limit'] == 5
    assert captured['offset'] == 2
    assert captured['expand_dropdowns'] is True
    assert captured['include_deleted'] is True
    assert captured['filters'] == {'status': 'open'}


def test_create_ticket_wraps_result_with_summary(monkeypatch):
    captured = {}

    def fake_create_ticket(**kwargs):
        captured.update(kwargs)
        return DummyResult(payload={'payload': kwargs, 'response': {'id': 42, 'name': 'Demo'}})

    monkeypatch.setattr(glpi_tickets, 'create_ticket', fake_create_ticket)

    response = CommandHandler(
        'create_ticket',
        {
            'name': 'Demo',
            'content': 'desc',
            'additional': {'foo': 'bar'},
        },
    ).execute()

    text = _extract_text(response)
    assert 'Ticket created' in text
    assert '"foo": "bar"' in text
    assert captured['name'] == 'Demo'
    assert captured['content'] == 'desc'


def test_create_ticket_value_error_is_reported(monkeypatch):
    def failing_create_ticket(**_kwargs):
        raise ValueError('boom')

    monkeypatch.setattr(glpi_tickets, 'create_ticket', failing_create_ticket)

    response = CommandHandler('create_ticket', {'name': 'Demo'}).execute()
    assert _extract_text(response) == 'Invalid argument: boom'


def test_create_change_merges_pr_links(monkeypatch):
    captured = {}

    def fake_create_change(**kwargs):
        captured.update(kwargs)
        return DummyResult(
            summary_text='Change created (id=77): Demo',
            payload={'payload': kwargs, 'response': {'id': 77, 'name': 'Demo'}},
        )

    monkeypatch.setattr(glpi_changes, 'create_change', fake_create_change)

    response = CommandHandler(
        'create_change',
        {
            'name': 'Demo change',
            'pr_links': [
                'https://example.com/pr/1',
                '  https://example.com/pr/2  ',
                '',
            ],
            'additional': {'other': 'value'},
        },
    ).execute()

    text = _extract_text(response)
    assert 'Change created' in text
    additional_fields = captured['additional_fields']
    assert additional_fields['other'] == 'value'
    assert additional_fields['controlistcontent'] == (
        '<p>https://example.com/pr/1</p><p>https://example.com/pr/2</p>'
    )


def test_update_change_merges_pr_links(monkeypatch):
    captured = {}

    def fake_update_change(**kwargs):
        captured.update(kwargs)
        return DummyResult(summary_text='Change updated', payload={'payload': kwargs})

    monkeypatch.setattr(glpi_changes, 'update_change', fake_update_change)

    original_fields = {'status': 3, 'controlistcontent': '<p>existing</p>'}
    response = CommandHandler(
        'update_change',
        {
            'change_id': 55,
            'fields': original_fields,
            'pr_links': ['https://example.com/pr/3'],
        },
    ).execute()

    text = _extract_text(response)
    assert 'Change updated' in text
    assert captured['change_id'] == 55
    merged_fields = captured['fields']
    assert merged_fields is not original_fields
    assert merged_fields['status'] == 3
    assert merged_fields['controlistcontent'] == '<p>existing</p><p>https://example.com/pr/3</p>'
