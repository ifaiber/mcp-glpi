import io
import json

from glpi_client.core.documents import DocumentManager


class _FakeResponse:
    def __init__(self, json_body=None, content=b"", status_code=200):
        self._json_body = json_body
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self):
        return self._json_body


class _FakeSession:
    def __init__(self, response):
        self._response = response
        self.calls = []

    def post(self, url, **kwargs):
        self.calls.append({"url": url, **kwargs})
        return self._response


def _manager():
    manager = DocumentManager.__new__(DocumentManager)
    manager.host_url = "http://glpi.example"
    manager.app_token = "app-token"
    manager.verify_tls = True
    manager._BaseHTTPHandler__session_token = "session-token"
    manager._BaseHTTPHandler__session = None
    return manager


def test_upload_document_sends_multipart_with_manifest():
    manager = _manager()
    response = _FakeResponse(json_body={"id": 1, "message": "Document move succeeded."})
    fake_session = _FakeSession(response)
    manager._BaseHTTPHandler__session = fake_session

    result = manager.upload_document(io.BytesIO(b"hello world"), name="Doc", file_name="hello.txt")

    assert result == {"id": 1, "message": "Document move succeeded."}
    call = fake_session.calls[0]
    assert call["url"] == "http://glpi.example/apirest.php/Document/"
    assert "Content-Type" not in call["headers"]
    assert call["headers"]["Session-Token"] == "session-token"
    manifest = json.loads(call["data"]["uploadManifest"])
    assert manifest["input"]["name"] == "Doc"
    assert manifest["input"]["_filename"] == ["hello.txt"]
    assert call["files"]["filename[0]"][0] == "hello.txt"


def test_upload_document_merges_extra_input_into_manifest():
    manager = _manager()
    response = _FakeResponse(json_body={"id": 2})
    fake_session = _FakeSession(response)
    manager._BaseHTTPHandler__session = fake_session

    manager.upload_document(
        io.BytesIO(b"data"), name="Doc", file_name="f.txt", extra_input={"entities_id": 3}
    )

    manifest = json.loads(fake_session.calls[0]["data"]["uploadManifest"])
    assert manifest["input"]["entities_id"] == 3
    assert manifest["input"]["name"] == "Doc"


def test_download_document_returns_bytes(monkeypatch):
    manager = _manager()
    captured = {}

    def fake_do_method(method, api_method_url, **kwargs):
        captured["method"] = method
        captured["api_method_url"] = api_method_url
        captured["headers"] = kwargs.get("headers")
        captured["on_error_raise"] = kwargs.get("on_error_raise")
        return _FakeResponse(content=b"file-bytes")

    monkeypatch.setattr(manager, "_do_method", fake_do_method)

    result = manager.download_document(11)

    assert result == b"file-bytes"
    assert captured["method"] == "get"
    assert captured["api_method_url"] == "Document/11"
    assert captured["headers"] == {"Accept": "application/octet-stream"}
    assert captured["on_error_raise"] is False
