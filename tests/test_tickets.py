from types import SimpleNamespace

import pytest

import glpi.tickets as tickets


def test_normalize_enum_value_accepts_label():
    value = tickets._normalize_enum_value('Closed', tickets.STATUS_LABELS, 'status')
    assert value == 6


def test_normalize_enum_value_rejects_unknown_label():
    with pytest.raises(ValueError):
        tickets._normalize_enum_value('not-a-status', tickets.STATUS_LABELS, 'status')


def test_ticket_list_to_table_translates_labels():
    ticket_list = tickets.TicketList(
        items=[
            {
                'id': 1,
                'name': 'Demo',
                'status': 5,
                'priority': 2,
                'impact': 1,
                'urgency': 3,
                'date': '2024-01-01',
                'date_mod': '2024-01-02',
                'closedate': '2024-01-03',
            }
        ],
        response_range=SimpleNamespace(start=0, end=0, count=1, max=1),
    )
    table = ticket_list.to_table()
    assert 'Solved' in table
    assert 'High' in table


def test_create_ticket_builds_expected_payload(monkeypatch):
    captured = {}

    class DummyHandler:
        def __init__(self, url, app_token, user_token):
            captured['auth'] = (url, app_token, user_token)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def create_ticket(self, **payload):
            captured['payload'] = payload
            return {'id': 99, 'name': payload['name']}

    monkeypatch.setattr(tickets, 'RequestHandler', DummyHandler)

    result = tickets.create_ticket(
        name=' Demo ',
        content='desc',
        status='Solved',
        impact='High',
        priority='Very low',
        urgency='low',
        category_id='7',
        entity_id=3,
        additional_fields={'custom': 'value', 'skip': None},
    )

    payload = captured['payload']
    assert payload['name'] == 'Demo'
    assert payload['status'] == 5
    assert payload['impact'] == 1
    assert payload['priority'] == 5
    assert payload['urgency'] == 3
    assert payload['itilcategories_id'] == 7
    assert payload['entities_id'] == 3
    assert payload['custom'] == 'value'
    assert 'skip' not in payload
    assert result.summary().startswith('Ticket created')


def test_create_ticket_invalid_enum_is_propagated(monkeypatch):
    class DummyHandler:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def create_ticket(self, **payload):
            return payload

    monkeypatch.setattr(tickets, 'RequestHandler', DummyHandler)

    with pytest.raises(ValueError):
        tickets.create_ticket(name='Demo', status='invalid')


def test_update_ticket_sanitises_fields(monkeypatch):
    captured = {}

    class DummyHandler:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def update_items(self, table, payloads):
            captured['table'] = table
            captured['payloads'] = payloads
            return {'updated': payloads}

    monkeypatch.setattr(tickets, 'RequestHandler', DummyHandler)

    result = tickets.update_ticket(
        ticket_id='10',
        fields={
            'status': 'Assigned',
            'entities_id': '4',
            'priority': '2',
            'custom': 'value',
            'ignored': None,
        },
    )

    payload = captured['payloads'][0]
    assert payload['id'] == 10
    assert payload['status'] == 2
    assert payload['entities_id'] == 4
    assert payload['priority'] == 2
    assert payload['custom'] == 'value'
    assert 'ignored' not in payload
    assert result.summary() == 'Updated ticket 10'


def test_update_ticket_requires_fields(monkeypatch):
    with pytest.raises(ValueError):
        tickets.update_ticket(ticket_id=1, fields={})

    with pytest.raises(ValueError):
        tickets.update_ticket(ticket_id=1, fields={'custom': None})


def test_delete_ticket_converts_flags(monkeypatch):
    captured = {}

    class DummyHandler:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def delete_items(self, table, ids, *, purge, log):
            captured['table'] = table
            captured['ids'] = ids
            captured['purge'] = purge
            captured['log'] = log
            return {'deleted': ids}

    monkeypatch.setattr(tickets, 'RequestHandler', DummyHandler)

    result = tickets.delete_ticket('15', purge='1', keep_history='0')

    assert captured['table'] == 'Ticket'
    assert captured['ids'] == [15]
    assert captured['purge'] is True
    assert captured['log'] is False
    assert result.summary() == 'Deleted ticket 15'
