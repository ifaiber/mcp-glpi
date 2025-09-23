import pytest

from mcp_glpi.GLPiHandler import CommandHandler
import glpi.session as glpi_session
import glpi.tickets as glpi_tickets


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
