from mcp_glpi.glpi import session


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
