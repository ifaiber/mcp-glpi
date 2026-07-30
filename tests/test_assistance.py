import pytest

from mcp_glpi.glpi import assistance


class _DummyHandlerBase:
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def test_assign_assistance_users_rejects_unsupported_itemtype():
    with pytest.raises(ValueError, match="itemtype"):
        assistance.assign_assistance_users("Computer", 1, {"users_id": 2})


def test_assign_assistance_users_rejects_blank_itemtype():
    with pytest.raises(ValueError, match="itemtype"):
        assistance.assign_assistance_users("", 1, {"users_id": 2})


def test_assign_assistance_users_uses_tickets_id_and_ticket_user(monkeypatch):
    captured = {}

    class DummyHandler(_DummyHandlerBase):
        def add_items(self, item_type, payload):
            captured["item_type"] = item_type
            captured["payload"] = payload
            return {"id": 1}

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    result = assistance.assign_assistance_users("Ticket", 10, {"users_id": 5})

    assert captured["item_type"] == "Ticket_User"
    assert captured["payload"] == {"users_id": 5, "tickets_id": 10}
    assert result.action == "assistance_item_user_add"
    assert result.entity_id_field == "id"
    assert result.entity_id == 10


def test_assign_assistance_users_uses_changes_id_and_change_user(monkeypatch):
    captured = {}

    class DummyHandler(_DummyHandlerBase):
        def add_items(self, item_type, payload):
            captured["item_type"] = item_type
            captured["payload"] = payload
            return {"id": 1}

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    # Matches the GLPI payload shape the user pointed at: changes_id/users_id/type/use_notification.
    result = assistance.assign_assistance_users(
        "Change", 2620, [{"users_id": 18, "type": 1, "use_notification": 0}]
    )

    assert captured["item_type"] == "Change_User"
    assert captured["payload"] == {
        "users_id": 18, "type": 1, "use_notification": False, "changes_id": 2620
    }
    assert result.entity_id == 2620


def test_assign_assistance_users_switches_profile_before_entity(monkeypatch):
    calls = []

    class DummyHandler(_DummyHandlerBase):
        def change_active_profile(self, profile_id):
            calls.append(("profile", profile_id))

        def change_active_entity(self, entity_id):
            calls.append(("entity", entity_id))

        def add_items(self, item_type, payload):
            return {"id": 1}

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    assistance.assign_assistance_users("Ticket", 10, {"users_id": 5}, entity_id=11, profile_id=24)

    assert calls == [("profile", 24), ("entity", 11)]


def test_assign_assistance_groups_rejects_unsupported_itemtype():
    with pytest.raises(ValueError, match="itemtype"):
        assistance.assign_assistance_groups("Computer", 1, {"groups_id": 2})


def test_assign_assistance_groups_uses_tickets_id_and_group_ticket(monkeypatch):
    captured = {}

    class DummyHandler(_DummyHandlerBase):
        def add_items(self, item_type, payload):
            captured["item_type"] = item_type
            captured["payload"] = payload
            return {"id": 1}

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    # Matches the GLPI payload shape the user pointed at: tickets_id/groups_id/type/use_notification.
    result = assistance.assign_assistance_groups(
        "Ticket", 2079, [{"groups_id": 5, "type": 1, "use_notification": 0}]
    )

    assert captured["item_type"] == "Group_Ticket"
    assert captured["payload"] == {
        "groups_id": 5, "type": 1, "use_notification": False, "tickets_id": 2079
    }
    assert result.action == "assistance_item_group_add"
    assert result.entity_id_field == "id"
    assert result.entity_id == 2079


def test_assign_assistance_groups_uses_changes_id_and_change_group(monkeypatch):
    captured = {}

    class DummyHandler(_DummyHandlerBase):
        def add_items(self, item_type, payload):
            captured["item_type"] = item_type
            captured["payload"] = payload
            return {"id": 1}

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    result = assistance.assign_assistance_groups("Change", 20, {"groups_id": 7})

    assert captured["item_type"] == "Change_Group"
    assert captured["payload"] == {"groups_id": 7, "changes_id": 20}
    assert result.entity_id == 20


def test_assign_assistance_groups_switches_profile_before_entity(monkeypatch):
    calls = []

    class DummyHandler(_DummyHandlerBase):
        def change_active_profile(self, profile_id):
            calls.append(("profile", profile_id))

        def change_active_entity(self, entity_id):
            calls.append(("entity", entity_id))

        def add_items(self, item_type, payload):
            return {"id": 1}

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    assistance.assign_assistance_groups("Ticket", 10, {"groups_id": 5}, entity_id=11, profile_id=24)

    assert calls == [("profile", 24), ("entity", 11)]
