from mcp_glpi.glpi import session
from mcp_glpi.glpi.session import entities as session_entities
from mcp_glpi.glpi.session import profiles as session_profiles


def test_get_full_session_formats_session_details(monkeypatch):
    class DummyHandler:
        def __init__(self, url, app_token, user_token, verify_tls):
            self.session_token = 'abcdef123456'

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get_full_session(self):
            return {
                'glpiname': 'user@example',
                'glpifirstname': 'First',
                'glpirealname': 'Last',
                'glpiactive_entity_name': 'Entity',
            }

    monkeypatch.setattr(session, 'RequestHandler', DummyHandler)

    output = session.get_full_session()
    assert 'ID de Sesi' in output
    assert 'user@example' in output
    assert 'First' in output
    assert 'Last' in output
    assert 'Entity' in output


def test_get_full_session_data_returns_structured_payload(monkeypatch):
    class DummyHandler:
        def __init__(self, url, app_token, user_token, verify_tls):
            self.session_token = 'abcdef123456'

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get_full_session(self):
            return {
                'glpiname': 'user@example',
                'glpifirstname': 'First',
                'glpirealname': 'Last',
                'glpiactive_entity_name': 'Entity',
            }

    monkeypatch.setattr(session, 'RequestHandler', DummyHandler)

    output = session.get_full_session_data()
    assert output['session_token'] == 'abcdef123456'
    assert output['user']['username'] == 'user@example'
    assert output['user']['first_name'] == 'First'
    assert output['user']['last_name'] == 'Last'
    assert output['user']['active_entity'] == 'Entity'


def test_get_my_profiles_data_returns_simplified_profiles(monkeypatch):
    class DummyHandler:
        def __init__(self, url, app_token, user_token, verify_tls):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get_my_profiles(self):
            return [
                {
                    'id': 22,
                    'name': 'Administrativo - Solicitante',
                    'entities': [
                        {'id': 2, 'name': 'Administrativo', 'is_recursive': 1},
                    ],
                }
            ]

    monkeypatch.setattr(session, 'RequestHandler', DummyHandler)

    output = session.get_my_profiles_data()
    assert output[0]['id'] == 22
    assert output[0]['entities'][0]['name'] == 'Administrativo'
    assert output[0]['entities'][0]['is_recursive'] is True


def test_get_my_entities_data_returns_simplified_entities(monkeypatch):
    class DummyHandler:
        def __init__(self, url, app_token, user_token, verify_tls):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get_my_entities(self, recursive=False):
            return [
                {'id': 2, 'name': 'Administrativo', 'completename': 'Root > Administrativo', 'is_recursive': 1},
            ]

    monkeypatch.setattr(session_entities, 'open_handler', lambda: DummyHandler('u', 'a', 'u', False))

    output = session_entities.get_my_entities_data()
    assert output[0]['id'] == 2
    assert output[0]['name'] == 'Administrativo'
    assert output[0]['is_recursive'] is True


def test_change_active_entity_data_switches_and_confirms(monkeypatch):
    captured = {}

    class DummyHandler:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def change_active_entity(self, entity_id, is_recursive=None):
            captured['entity_id'] = entity_id
            captured['is_recursive'] = is_recursive

        def get_active_entities(self):
            return {'id': captured['entity_id'], 'name': 'Administrativo'}

    monkeypatch.setattr(session_entities, 'open_handler', lambda: DummyHandler())

    output = session_entities.change_active_entity_data(entity_id='7', recursive=True)

    assert captured['entity_id'] == 7
    assert captured['is_recursive'] is True
    assert output['entity_id'] == 7
    assert output['active_entities']['id'] == 7


def test_change_active_entity_data_accepts_root_entity_zero(monkeypatch):
    # GLPI's root entity conventionally has id 0; it must not be rejected as invalid.
    captured = {}

    class DummyHandler:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def change_active_entity(self, entity_id, is_recursive=None):
            captured['entity_id'] = entity_id

        def get_active_entities(self):
            return {'id': captured['entity_id'], 'name': 'Root entity'}

    monkeypatch.setattr(session_entities, 'open_handler', lambda: DummyHandler())

    output = session_entities.change_active_entity_data(entity_id=0)

    assert captured['entity_id'] == 0
    assert output['entity_id'] == 0


def test_change_active_profile_data_switches_and_confirms(monkeypatch):
    captured = {}

    class DummyHandler:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def change_active_profile(self, profile_id):
            captured['profile_id'] = profile_id

        def get_active_profile(self):
            return {
                'id': captured['profile_id'],
                'name': 'Desarrollador',
                'entities': {'6': {'id': 6, 'name': 'Desarrollo', 'is_recursive': 0}},
            }

    monkeypatch.setattr(session_profiles, 'open_handler', lambda: DummyHandler())

    output = session_profiles.change_active_profile_data(profile_id='24')

    assert captured['profile_id'] == 24
    assert output['profile_id'] == 24
    assert output['active_profile']['id'] == 24
    assert output['active_profile']['name'] == 'Desarrollador'
    assert output['active_profile']['entities'] == [
        {'id': 6, 'name': 'Desarrollo', 'is_recursive': False}
    ]
