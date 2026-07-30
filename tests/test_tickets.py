from types import SimpleNamespace

import pytest

from mcp_glpi.glpi import tickets


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
        def __init__(self, url, app_token, user_token, verify_tls):
            captured['auth'] = (url, app_token, user_token, verify_tls)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def change_active_entity(self, entity_id):
            captured['switched_to'] = entity_id

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


def test_create_ticket_switches_active_entity_when_entity_id_given(monkeypatch):
    captured = {}

    class DummyHandler:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def change_active_entity(self, entity_id):
            captured['switched_to'] = entity_id

        def create_ticket(self, **payload):
            captured['payload'] = payload
            return {'id': 1, 'name': payload['name']}

    monkeypatch.setattr(tickets, 'RequestHandler', DummyHandler)

    tickets.create_ticket(name='Demo', entity_id=9)

    assert captured['switched_to'] == 9
    assert captured['payload']['entities_id'] == 9


def test_create_ticket_does_not_switch_entity_by_default(monkeypatch):
    captured = {'switch_called': False}

    class DummyHandler:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def change_active_entity(self, entity_id):
            captured['switch_called'] = True

        def create_ticket(self, **payload):
            return {'id': 1, 'name': payload['name']}

    monkeypatch.setattr(tickets, 'RequestHandler', DummyHandler)

    tickets.create_ticket(name='Demo')

    assert captured['switch_called'] is False


def test_update_ticket_switches_active_entity_when_entity_id_given(monkeypatch):
    captured = {}

    class DummyHandler:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def change_active_entity(self, entity_id):
            captured['switched_to'] = entity_id

        def update_items(self, table, payloads):
            return {'updated': payloads}

    monkeypatch.setattr(tickets, 'RequestHandler', DummyHandler)

    tickets.update_ticket(ticket_id=10, fields={'status': 'Closed'}, entity_id=4)

    assert captured['switched_to'] == 4


def test_create_ticket_switches_to_root_entity_when_entity_id_is_zero(monkeypatch):
    # GLPI's root entity conventionally has id 0; it must not be rejected as invalid.
    captured = {}

    class DummyHandler:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def change_active_entity(self, entity_id):
            captured['switched_to'] = entity_id

        def create_ticket(self, **payload):
            captured['payload'] = payload
            return {'id': 1, 'name': payload['name']}

    monkeypatch.setattr(tickets, 'RequestHandler', DummyHandler)

    tickets.create_ticket(name='Demo', entity_id=0)

    assert captured['switched_to'] == 0
    assert captured['payload']['entities_id'] == 0


def test_create_ticket_switches_profile_before_entity(monkeypatch):
    calls = []

    class DummyHandler:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def change_active_profile(self, profile_id):
            calls.append(('profile', profile_id))

        def change_active_entity(self, entity_id):
            calls.append(('entity', entity_id))

        def create_ticket(self, **payload):
            return {'id': 1, 'name': payload['name']}

    monkeypatch.setattr(tickets, 'RequestHandler', DummyHandler)

    tickets.create_ticket(name='Demo', entity_id=11, profile_id=24)

    # The active profile determines rights; the active entity only scopes
    # visible records. Profile must be switched first so the entity switch
    # (and the operation that follows) runs under the intended permissions.
    assert calls == [('profile', 24), ('entity', 11)]


def test_create_ticket_does_not_switch_profile_by_default(monkeypatch):
    captured = {'switch_called': False}

    class DummyHandler:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def change_active_profile(self, profile_id):
            captured['switch_called'] = True

        def create_ticket(self, **payload):
            return {'id': 1, 'name': payload['name']}

    monkeypatch.setattr(tickets, 'RequestHandler', DummyHandler)

    tickets.create_ticket(name='Demo')

    assert captured['switch_called'] is False


def test_save_ticket_creates_when_no_id_given(monkeypatch):
    captured = {}

    class DummyHandler:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def create_ticket(self, **payload):
            captured['payload'] = payload
            return {'id': 99, 'name': payload['name']}

    monkeypatch.setattr(tickets, 'RequestHandler', DummyHandler)

    result = tickets.save_ticket(name='Demo', content='desc', status='Solved')

    assert captured['payload']['name'] == 'Demo'
    assert captured['payload']['content'] == 'desc'
    assert captured['payload']['status'] == 5
    assert result.summary().startswith('Ticket created')


def test_save_ticket_requires_name_when_no_id():
    with pytest.raises(ValueError, match='name is required'):
        tickets.save_ticket(content='desc')


def test_save_ticket_updates_when_id_given(monkeypatch):
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

    result = tickets.save_ticket(id=10, status='Assigned', category_id='7')

    assert captured['table'] == 'Ticket'
    payload = captured['payloads'][0]
    assert payload['id'] == 10
    assert payload['status'] == 2
    assert payload['itilcategories_id'] == 7
    assert 'name' not in payload
    assert result.summary() == 'Updated ticket 10'


def test_save_ticket_update_does_not_require_name(monkeypatch):
    class DummyHandler:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def update_items(self, table, payloads):
            return {'updated': payloads}

    monkeypatch.setattr(tickets, 'RequestHandler', DummyHandler)

    # Should not raise even though 'name' is absent -- only required on create.
    tickets.save_ticket(id=10, content='nuevo contenido')


def test_save_ticket_update_merges_additional_fields(monkeypatch):
    captured = {}

    class DummyHandler:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def update_items(self, table, payloads):
            captured['payloads'] = payloads
            return {'updated': payloads}

    monkeypatch.setattr(tickets, 'RequestHandler', DummyHandler)

    tickets.save_ticket(id=10, additional_fields={'requesttypes_id': 3})

    payload = captured['payloads'][0]
    assert payload['id'] == 10
    assert payload['requesttypes_id'] == 3


def test_save_ticket_update_requires_at_least_one_field(monkeypatch):
    class DummyHandler:
        def __init__(self, *args, **kwargs):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def update_items(self, table, payloads):
            return {'updated': payloads}

    monkeypatch.setattr(tickets, 'RequestHandler', DummyHandler)

    with pytest.raises(ValueError):
        tickets.save_ticket(id=10)


