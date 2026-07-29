import pytest

from mcp_glpi.glpi import files


class _DummyHandlerBase:
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_upload_document_rejects_missing_file(tmp_path):
    missing = tmp_path / "does-not-exist.txt"

    with pytest.raises(ValueError, match="does not exist"):
        files.upload_document(str(missing))


def test_upload_document_reads_file_and_merges_additional_fields(monkeypatch, tmp_path):
    source = tmp_path / "hello.txt"
    source.write_bytes(b"hello world")
    captured = {}

    class DummyHandler(_DummyHandlerBase):
        def upload_document(self, file, name=None, file_name=None, extra_input=None):
            captured["content"] = file.read()
            captured["name"] = name
            captured["file_name"] = file_name
            captured["extra_input"] = extra_input
            return {"id": 5, "message": "Document move succeeded."}

    monkeypatch.setattr(files, "RequestHandler", DummyHandler)

    result = files.upload_document(
        str(source), name="Doc", additional_fields={"entities_id": 3, "skip": None}
    )

    assert captured["content"] == b"hello world"
    assert captured["name"] == "Doc"
    assert captured["file_name"] == "hello.txt"
    assert captured["extra_input"] == {"entities_id": 3}
    assert result.summary() == "Document created (id=5): Doc"


def test_upload_document_defaults_file_name_to_basename(monkeypatch, tmp_path):
    source = tmp_path / "report.pdf"
    source.write_bytes(b"data")
    captured = {}

    class DummyHandler(_DummyHandlerBase):
        def upload_document(self, file, name=None, file_name=None, extra_input=None):
            captured["file_name"] = file_name
            return {"id": 1}

    monkeypatch.setattr(files, "RequestHandler", DummyHandler)

    files.upload_document(str(source))

    assert captured["file_name"] == "report.pdf"


def test_upload_document_switches_profile_before_entity(monkeypatch, tmp_path):
    source = tmp_path / "f.txt"
    source.write_bytes(b"x")
    calls = []

    class DummyHandler(_DummyHandlerBase):
        def change_active_profile(self, profile_id):
            calls.append(("profile", profile_id))

        def change_active_entity(self, entity_id):
            calls.append(("entity", entity_id))

        def upload_document(self, file, name=None, file_name=None, extra_input=None):
            return {"id": 1}

    monkeypatch.setattr(files, "RequestHandler", DummyHandler)

    files.upload_document(str(source), entity_id=11, profile_id=24)

    assert calls == [("profile", 24), ("entity", 11)]


def test_download_document_writes_bytes_to_destination(monkeypatch, tmp_path):
    destination = tmp_path / "nested" / "out.bin"

    class DummyHandler(_DummyHandlerBase):
        def download_document(self, document_id):
            return b"downloaded-bytes"

    monkeypatch.setattr(files, "RequestHandler", DummyHandler)

    result = files.download_document(7, str(destination))

    assert destination.read_bytes() == b"downloaded-bytes"
    assert result.as_dict()["response"] == {"bytes_written": len(b"downloaded-bytes")}


def test_download_document_resolves_filename_when_destination_is_a_directory(monkeypatch, tmp_path):
    class DummyHandler(_DummyHandlerBase):
        def get_item(self, itemtype, item_id, **kwargs):
            assert itemtype == "Document"
            return {"id": item_id, "filename": "report.pdf"}

        def download_document(self, document_id):
            return b"pdf-bytes"

    monkeypatch.setattr(files, "RequestHandler", DummyHandler)

    result = files.download_document(7, str(tmp_path))

    written = tmp_path / "report.pdf"
    assert written.read_bytes() == b"pdf-bytes"
    assert result.as_dict()["payload"]["destination_path"] == str(written)


def test_download_document_switches_entity_and_profile(monkeypatch, tmp_path):
    destination = tmp_path / "out.bin"
    calls = []

    class DummyHandler(_DummyHandlerBase):
        def change_active_profile(self, profile_id):
            calls.append(("profile", profile_id))

        def change_active_entity(self, entity_id):
            calls.append(("entity", entity_id))

        def download_document(self, document_id):
            return b"x"

    monkeypatch.setattr(files, "RequestHandler", DummyHandler)

    files.download_document(7, str(destination), entity_id=11, profile_id=24)

    assert calls == [("profile", 24), ("entity", 11)]


def test_link_item_rejects_unsupported_item_type():
    with pytest.raises(ValueError, match="Unsupported itemtype"):
        files.link_item(document_id=1, item_type="User", item_id=2)


def test_link_item_builds_document_item_payload(monkeypatch):
    captured = {}

    class DummyHandler(_DummyHandlerBase):
        def add_items(self, item_type, payload):
            captured["item_type"] = item_type
            captured["payload"] = payload
            return {"id": 9}

    monkeypatch.setattr(files, "RequestHandler", DummyHandler)

    result = files.link_item(document_id=1, item_type="Ticket", item_id=47)

    assert captured["item_type"] == "Document_Item"
    assert captured["payload"] == {"documents_id": 1, "itemtype": "Ticket", "items_id": 47}
    assert result.summary() == "Linked document 1 to Ticket 47"


def test_unlink_item_converts_flags(monkeypatch):
    captured = {}

    class DummyHandler(_DummyHandlerBase):
        def delete_items(self, table, ids, *, purge, log):
            captured["table"] = table
            captured["ids"] = ids
            captured["purge"] = purge
            captured["log"] = log
            return {"deleted": ids}

    monkeypatch.setattr(files, "RequestHandler", DummyHandler)

    result = files.unlink_item(document_id=1, link_id="9", purge="1", keep_history="0")

    assert captured["table"] == "Document_Item"
    assert captured["ids"] == [9]
    assert captured["purge"] is True
    assert captured["log"] is False
    assert result.summary() == "Unlinked document 1 from relation 9"
