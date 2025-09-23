import glpi.session as session


def test_get_full_session_formats_session_details(monkeypatch):
    class DummyHandler:
        def __init__(self, url, app_token, user_token):
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
