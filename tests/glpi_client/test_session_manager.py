from glpi_client.core.session import SessionManager
from glpi_client.exceptions import GLPIError, GLPIRequestError

import pytest


class DummyRequest:
    headers = {}
    body = None
    method = 'POST'


class DummyResponse:
    def __init__(self, status_code, json_body):
        self.status_code = status_code
        self._json_body = json_body
        self.text = str(json_body)
        self.url = 'http://glpi.example/apirest.php/changeActiveEntities'
        self.request = DummyRequest()

    def json(self):
        return self._json_body


def _manager_with_response(monkeypatch, response):
    manager = SessionManager.__new__(SessionManager)
    captured = {}

    def fake_do_method(method, api_method_url, data=None, **kwargs):
        captured['method'] = method
        captured['api_method_url'] = api_method_url
        captured['data'] = data
        return response

    monkeypatch.setattr(manager, '_do_method', fake_do_method)
    return manager, captured


def test_change_active_entity_succeeds_on_true_body(monkeypatch):
    manager, captured = _manager_with_response(monkeypatch, DummyResponse(200, True))

    manager.change_active_entity(6)

    assert captured['api_method_url'] == 'changeActiveEntities'
    assert captured['data'] == {'entities_id': 6}


def test_change_active_entity_raises_when_glpi_rejects_with_false_body(monkeypatch):
    # GLPI answers HTTP 200 with a bare `false` when the entity is not
    # accessible for this user/token; that must not be treated as success.
    manager, _ = _manager_with_response(monkeypatch, DummyResponse(200, False))

    with pytest.raises(GLPIError, match='rejected changing to entity 6'):
        manager.change_active_entity(6)


def test_change_active_entity_forwards_is_recursive(monkeypatch):
    manager, captured = _manager_with_response(monkeypatch, DummyResponse(200, True))

    manager.change_active_entity(6, is_recursive=True)

    assert captured['data'] == {'entities_id': 6, 'is_recursive': True}


def test_change_active_entity_raises_glpi_error_on_400(monkeypatch):
    manager, _ = _manager_with_response(
        monkeypatch, DummyResponse(400, ['ERROR', 'Entity does not exist'])
    )

    with pytest.raises(GLPIError, match='Entity does not exist'):
        manager.change_active_entity(999)


def test_change_active_entity_raises_request_error_on_other_4xx(monkeypatch):
    manager, _ = _manager_with_response(monkeypatch, DummyResponse(401, {'error': 'unauthorized'}))

    with pytest.raises(GLPIRequestError):
        manager.change_active_entity(6)


def test_change_active_profile_succeeds_on_true_body(monkeypatch):
    manager, captured = _manager_with_response(monkeypatch, DummyResponse(200, True))

    manager.change_active_profile(6)

    assert captured['api_method_url'] == 'changeActiveProfile'
    assert captured['data'] == {'profiles_id': 6}


def test_change_active_profile_raises_when_glpi_rejects_with_false_body(monkeypatch):
    # Same silent-rejection pattern as changeActiveEntities: GLPI can answer
    # 200 with a bare `false` when the profile isn't one of the user's own.
    manager, _ = _manager_with_response(monkeypatch, DummyResponse(200, False))

    with pytest.raises(GLPIError, match='rejected changing to profile 6'):
        manager.change_active_profile(6)


def test_change_active_profile_raises_glpi_error_on_404(monkeypatch):
    manager, _ = _manager_with_response(monkeypatch, DummyResponse(404, ['ERROR_ITEM_NOT_FOUND', 'Item Not Found']))

    with pytest.raises(GLPIError, match='Profile not found'):
        manager.change_active_profile(999999)


def test_change_active_profile_raises_request_error_on_other_4xx(monkeypatch):
    manager, _ = _manager_with_response(monkeypatch, DummyResponse(401, {'error': 'unauthorized'}))

    with pytest.raises(GLPIRequestError):
        manager.change_active_profile(6)
