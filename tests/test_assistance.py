import pytest
from glpi_client import GLPIError

from mcp_glpi.glpi import assistance


class _DummyHandlerBase:
    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    @property
    def response_range(self):
        # GLPI's sub-item endpoints don't always send Content-Range headers.
        raise GLPIError("The previous request did not return a range")


def test_assign_assistance_user_rejects_unsupported_itemtype():
    with pytest.raises(ValueError, match="itemtype"):
        assistance.assign_assistance_user("Computer", 1, {"users_id": 2})


def test_assign_assistance_user_rejects_blank_itemtype():
    with pytest.raises(ValueError, match="itemtype"):
        assistance.assign_assistance_user("", 1, {"users_id": 2})


def test_assign_assistance_user_rejects_list(monkeypatch):
    class DummyHandler(_DummyHandlerBase):
        def add_items(self, item_type, payload):
            return {"id": 1}

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    with pytest.raises(ValueError, match="lista"):
        assistance.assign_assistance_user(
            "Ticket", 2079, [{"users_id": 5}, {"users_id": 6}]
        )


def test_assign_assistance_user_uses_tickets_id_and_ticket_user(monkeypatch):
    captured = {}

    class DummyHandler(_DummyHandlerBase):
        def add_items(self, item_type, payload):
            captured["item_type"] = item_type
            captured["payload"] = payload
            return {"id": 1}

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    result = assistance.assign_assistance_user("Ticket", 10, {"users_id": 5})

    assert captured["item_type"] == "Ticket_User"
    assert captured["payload"] == {"users_id": 5, "tickets_id": 10}
    assert result.action == "item_user_add"
    assert result.entity_id_field == "id"
    assert result.entity_id == 10


def test_assign_assistance_user_uses_changes_id_and_change_user(monkeypatch):
    captured = {}

    class DummyHandler(_DummyHandlerBase):
        def add_items(self, item_type, payload):
            captured["item_type"] = item_type
            captured["payload"] = payload
            return {"id": 1}

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    # Matches the GLPI payload shape the user pointed at: changes_id/users_id/type/use_notification.
    result = assistance.assign_assistance_user(
        "Change", 2620, {"users_id": 18, "type": 1, "use_notification": 0}
    )

    assert captured["item_type"] == "Change_User"
    assert captured["payload"] == {
        "users_id": 18, "type": 1, "use_notification": False, "changes_id": 2620
    }
    assert result.entity_id == 2620


def test_assign_assistance_user_switches_profile_before_entity(monkeypatch):
    calls = []

    class DummyHandler(_DummyHandlerBase):
        def change_active_profile(self, profile_id):
            calls.append(("profile", profile_id))

        def change_active_entity(self, entity_id):
            calls.append(("entity", entity_id))

        def add_items(self, item_type, payload):
            return {"id": 1}

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    assistance.assign_assistance_user("Ticket", 10, {"users_id": 5}, entity_id=11, profile_id=24)

    assert calls == [("profile", 24), ("entity", 11)]


def test_assign_assistance_group_rejects_unsupported_itemtype():
    with pytest.raises(ValueError, match="itemtype"):
        assistance.assign_assistance_group("Computer", 1, {"groups_id": 2})


def test_assign_assistance_group_rejects_list(monkeypatch):
    class DummyHandler(_DummyHandlerBase):
        def add_items(self, item_type, payload):
            return {"id": 1}

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    with pytest.raises(ValueError, match="lista"):
        assistance.assign_assistance_group(
            "Ticket", 2079, [{"groups_id": 5}, {"groups_id": 6}]
        )


def test_assign_assistance_group_uses_tickets_id_and_group_ticket(monkeypatch):
    captured = {}

    class DummyHandler(_DummyHandlerBase):
        def add_items(self, item_type, payload):
            captured["item_type"] = item_type
            captured["payload"] = payload
            return {"id": 1}

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    # Matches the GLPI payload shape the user pointed at: tickets_id/groups_id/type/use_notification.
    result = assistance.assign_assistance_group(
        "Ticket", 2079, {"groups_id": 5, "type": 1, "use_notification": 0}
    )

    assert captured["item_type"] == "Group_Ticket"
    assert captured["payload"] == {
        "groups_id": 5, "type": 1, "use_notification": False, "tickets_id": 2079
    }
    assert result.action == "item_group_add"
    assert result.entity_id_field == "id"
    assert result.entity_id == 2079


def test_assign_assistance_group_uses_changes_id_and_change_group(monkeypatch):
    captured = {}

    class DummyHandler(_DummyHandlerBase):
        def add_items(self, item_type, payload):
            captured["item_type"] = item_type
            captured["payload"] = payload
            return {"id": 1}

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    result = assistance.assign_assistance_group("Change", 20, {"groups_id": 7})

    assert captured["item_type"] == "Change_Group"
    assert captured["payload"] == {"groups_id": 7, "changes_id": 20}
    assert result.entity_id == 20


def test_assign_assistance_group_switches_profile_before_entity(monkeypatch):
    calls = []

    class DummyHandler(_DummyHandlerBase):
        def change_active_profile(self, profile_id):
            calls.append(("profile", profile_id))

        def change_active_entity(self, entity_id):
            calls.append(("entity", entity_id))

        def add_items(self, item_type, payload):
            return {"id": 1}

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    assistance.assign_assistance_group("Ticket", 10, {"groups_id": 5}, entity_id=11, profile_id=24)

    assert calls == [("profile", 24), ("entity", 11)]


def test_add_assistance_followup_rejects_unsupported_itemtype():
    with pytest.raises(ValueError, match="itemtype"):
        assistance.add_assistance_followup("Computer", 1, "hola")


def test_add_assistance_followup_uses_generic_itemtype_items_id_shape(monkeypatch):
    captured = {}

    class DummyHandler(_DummyHandlerBase):
        def add_items(self, item_type, payload):
            captured["item_type"] = item_type
            captured["payload"] = payload
            return {"id": 1}

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    # Matches the GLPI payload shape the user pointed at: itemtype/items_id/content/is_private.
    result = assistance.add_assistance_followup(
        "Change", 2620, "pruebas de ticketssss", is_private=0
    )

    assert captured["item_type"] == "ITILFollowup"
    assert captured["payload"] == {
        "itemtype": "Change",
        "items_id": 2620,
        "content": "pruebas de ticketssss",
        "is_private": False,
    }
    assert result.action == "assistance_item_followup_add"
    assert result.entity_id_field == "id"
    assert result.entity_id == 2620


def test_add_assistance_followup_uses_ticket_itemtype(monkeypatch):
    captured = {}

    class DummyHandler(_DummyHandlerBase):
        def add_items(self, item_type, payload):
            captured["item_type"] = item_type
            captured["payload"] = payload
            return {"id": 1}

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    assistance.add_assistance_followup("Ticket", 10, "hola")

    assert captured["item_type"] == "ITILFollowup"
    assert captured["payload"]["itemtype"] == "Ticket"
    assert captured["payload"]["items_id"] == 10


def test_add_assistance_followup_switches_profile_before_entity(monkeypatch):
    calls = []

    class DummyHandler(_DummyHandlerBase):
        def change_active_profile(self, profile_id):
            calls.append(("profile", profile_id))

        def change_active_entity(self, entity_id):
            calls.append(("entity", entity_id))

        def add_items(self, item_type, payload):
            return {"id": 1}

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    assistance.add_assistance_followup("Ticket", 10, "hola", entity_id=11, profile_id=24)

    assert calls == [("profile", 24), ("entity", 11)]


def test_update_assistance_followup_rejects_unsupported_itemtype():
    with pytest.raises(ValueError, match="itemtype"):
        assistance.update_assistance_followup("Computer", 1, 99, "hola")


def test_update_assistance_followup_uses_update_items_with_id(monkeypatch):
    captured = {}

    class DummyHandler(_DummyHandlerBase):
        def update_items(self, item_type, payload_list):
            captured["item_type"] = item_type
            captured["payload_list"] = payload_list
            return [{"id": 20016}]

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    # Matches the user's literal example payload.
    result = assistance.update_assistance_followup(
        "Change", 2620, 20016, "xxxxx de ticketssss", is_private=0
    )

    assert captured["item_type"] == "ITILFollowup"
    assert captured["payload_list"] == [
        {
            "id": 20016,
            "itemtype": "Change",
            "items_id": 2620,
            "content": "xxxxx de ticketssss",
            "is_private": False,
        }
    ]
    assert result.action == "assistance_item_followup_update"
    assert result.entity_id_field == "id"
    assert result.entity_id == 2620


def test_update_assistance_followup_switches_profile_before_entity(monkeypatch):
    calls = []

    class DummyHandler(_DummyHandlerBase):
        def change_active_profile(self, profile_id):
            calls.append(("profile", profile_id))

        def change_active_entity(self, entity_id):
            calls.append(("entity", entity_id))

        def update_items(self, item_type, payload_list):
            return [{"id": 1}]

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    assistance.update_assistance_followup(
        "Ticket", 10, 99, "hola", entity_id=11, profile_id=24
    )

    assert calls == [("profile", 24), ("entity", 11)]


def test_save_assistance_followup_without_followup_id_creates(monkeypatch):
    captured = {}

    class DummyHandler(_DummyHandlerBase):
        def add_items(self, item_type, payload):
            captured["item_type"] = item_type
            captured["payload"] = payload
            return {"id": 1}

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    result = assistance.save_assistance_followup("Change", 2620, "hola")

    assert captured["item_type"] == "ITILFollowup"
    assert captured["payload"] == {
        "itemtype": "Change",
        "items_id": 2620,
        "content": "hola",
        "is_private": 0,
    }
    assert result.action == "assistance_item_followup_add"


def test_save_assistance_followup_with_followup_id_updates(monkeypatch):
    captured = {}

    class DummyHandler(_DummyHandlerBase):
        def update_items(self, item_type, payload_list):
            captured["item_type"] = item_type
            captured["payload_list"] = payload_list
            return [{"id": 1}]

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    result = assistance.save_assistance_followup(
        "Change", 2620, "hola actualizada", followup_id=99
    )

    assert captured["item_type"] == "ITILFollowup"
    assert captured["payload_list"] == [
        {
            "id": 99,
            "itemtype": "Change",
            "items_id": 2620,
            "content": "hola actualizada",
            "is_private": 0,
        }
    ]
    assert result.action == "assistance_item_followup_update"


def test_add_assistance_solution_rejects_unsupported_itemtype():
    with pytest.raises(ValueError, match="itemtype"):
        assistance.add_assistance_solution("Computer", 1, "sol")


def test_add_assistance_solution_uses_generic_itemtype_items_id_shape(monkeypatch):
    captured = {}

    class DummyHandler(_DummyHandlerBase):
        def add_items(self, item_type, payload):
            captured["item_type"] = item_type
            captured["payload"] = payload
            return {"id": 1}

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    result = assistance.add_assistance_solution("Change", 2620, "sol")

    assert captured["item_type"] == "ITILSolution"
    assert captured["payload"] == {
        "itemtype": "Change",
        "items_id": 2620,
        "content": "sol",
    }
    assert result.action == "assistance_item_solution_add"
    assert result.entity_id_field == "id"
    assert result.entity_id == 2620


def test_add_assistance_solution_switches_profile_before_entity(monkeypatch):
    calls = []

    class DummyHandler(_DummyHandlerBase):
        def change_active_profile(self, profile_id):
            calls.append(("profile", profile_id))

        def change_active_entity(self, entity_id):
            calls.append(("entity", entity_id))

        def add_items(self, item_type, payload):
            return {"id": 1}

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    assistance.add_assistance_solution("Ticket", 10, "sol", entity_id=11, profile_id=24)

    assert calls == [("profile", 24), ("entity", 11)]


def test_update_assistance_solution_rejects_unsupported_itemtype():
    with pytest.raises(ValueError, match="itemtype"):
        assistance.update_assistance_solution("Computer", 1, 99, "sol")


def test_update_assistance_solution_uses_update_items_with_id(monkeypatch):
    captured = {}

    class DummyHandler(_DummyHandlerBase):
        def update_items(self, item_type, payload_list):
            captured["item_type"] = item_type
            captured["payload_list"] = payload_list
            return [{"id": 1}]

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    result = assistance.update_assistance_solution(
        "Change", 2620, 555, "sol actualizada"
    )

    assert captured["item_type"] == "ITILSolution"
    assert captured["payload_list"] == [
        {
            "id": 555,
            "itemtype": "Change",
            "items_id": 2620,
            "content": "sol actualizada",
        }
    ]
    assert result.action == "assistance_item_solution_update"
    assert result.entity_id == 2620


def test_update_assistance_solution_switches_profile_before_entity(monkeypatch):
    calls = []

    class DummyHandler(_DummyHandlerBase):
        def change_active_profile(self, profile_id):
            calls.append(("profile", profile_id))

        def change_active_entity(self, entity_id):
            calls.append(("entity", entity_id))

        def update_items(self, item_type, payload_list):
            return [{"id": 1}]

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    assistance.update_assistance_solution(
        "Ticket", 10, 99, "sol", entity_id=11, profile_id=24
    )

    assert calls == [("profile", 24), ("entity", 11)]


def test_add_item_solution_without_solution_id_creates(monkeypatch):
    captured = {}

    class DummyHandler(_DummyHandlerBase):
        def add_items(self, item_type, payload):
            captured["item_type"] = item_type
            captured["payload"] = payload
            return {"id": 1}

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    result = assistance.add_item_solution("Change", 2620, "sol")

    assert captured["item_type"] == "ITILSolution"
    assert captured["payload"] == {
        "itemtype": "Change",
        "items_id": 2620,
        "content": "sol",
    }
    assert result.action == "assistance_item_solution_add"


def test_add_item_solution_with_solution_id_updates(monkeypatch):
    captured = {}

    class DummyHandler(_DummyHandlerBase):
        def update_items(self, item_type, payload_list):
            captured["item_type"] = item_type
            captured["payload_list"] = payload_list
            return [{"id": 1}]

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    result = assistance.add_item_solution(
        "Change", 2620, "sol actualizada", solution_id=555
    )

    assert captured["item_type"] == "ITILSolution"
    assert captured["payload_list"] == [
        {
            "id": 555,
            "itemtype": "Change",
            "items_id": 2620,
            "content": "sol actualizada",
        }
    ]
    assert result.action == "assistance_item_solution_update"


def test_link_ticket_change_from_ticket_side(monkeypatch):
    captured = {}

    class DummyHandler(_DummyHandlerBase):
        def add_items(self, item_type, payload):
            captured["item_type"] = item_type
            captured["payload"] = payload
            return {"id": 9}

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    result = assistance.link_ticket_change("Ticket", 47, 2620)

    assert captured["item_type"] == "Change_Ticket"
    assert captured["payload"] == {"tickets_id": 47, "changes_id": 2620}
    assert result.action == "item_ticketchange_link"
    assert result.entity_id == 47


def test_link_ticket_change_from_change_side(monkeypatch):
    captured = {}

    class DummyHandler(_DummyHandlerBase):
        def add_items(self, item_type, payload):
            captured["item_type"] = item_type
            captured["payload"] = payload
            return {"id": 9}

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    result = assistance.link_ticket_change("Change", 2620, 47)

    assert captured["item_type"] == "Change_Ticket"
    assert captured["payload"] == {"tickets_id": 47, "changes_id": 2620}
    assert result.entity_id == 2620


def test_link_ticket_change_switches_profile_before_entity(monkeypatch):
    calls = []

    class DummyHandler(_DummyHandlerBase):
        def change_active_profile(self, profile_id):
            calls.append(("profile", profile_id))

        def change_active_entity(self, entity_id):
            calls.append(("entity", entity_id))

        def add_items(self, item_type, payload):
            return {"id": 9}

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    assistance.link_ticket_change("Ticket", 47, 2620, entity_id=11, profile_id=24)

    assert calls == [("profile", 24), ("entity", 11)]


def test_unlink_ticket_change_resolves_relation_id_then_deletes(monkeypatch):
    captured = {}

    class DummyHandler(_DummyHandlerBase):
        def get_sub_items(self, item_type, item_id, sub_item_type, **kwargs):
            captured["get_sub_items_args"] = (item_type, item_id, sub_item_type)
            return [
                {"id": 1565, "changes_id": 2623, "tickets_id": 7431},
                {"id": 9001, "changes_id": 2623, "tickets_id": 47},
            ]

        def delete_items(self, item_type, ids, *, purge, log):
            captured["item_type"] = item_type
            captured["ids"] = ids
            captured["purge"] = purge
            captured["log"] = log
            return [{"9001": True}]

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    result = assistance.unlink_ticket_change("Ticket", 47, 2623)

    assert captured["get_sub_items_args"] == ("Change", 2623, "Change_Ticket")
    assert captured["item_type"] == "Change_Ticket"
    assert captured["ids"] == [9001]
    assert captured["purge"] is False
    assert captured["log"] is True
    assert result.action == "item_ticketchange_unlink"
    assert result.entity_id == 9001


def test_unlink_ticket_change_from_change_side(monkeypatch):
    captured = {}

    class DummyHandler(_DummyHandlerBase):
        def get_sub_items(self, item_type, item_id, sub_item_type, **kwargs):
            return [{"id": 9001, "changes_id": 2623, "tickets_id": 47}]

        def delete_items(self, item_type, ids, *, purge, log):
            captured["ids"] = ids
            return [{"9001": True}]

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    assistance.unlink_ticket_change("Change", 2623, 47)

    assert captured["ids"] == [9001]


def test_unlink_ticket_change_raises_when_relation_not_found(monkeypatch):
    class DummyHandler(_DummyHandlerBase):
        def get_sub_items(self, item_type, item_id, sub_item_type, **kwargs):
            return []

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    with pytest.raises(ValueError, match="No existe una relacion"):
        assistance.unlink_ticket_change("Ticket", 47, 2623)


def test_unlink_ticket_change_converts_flags(monkeypatch):
    captured = {}

    class DummyHandler(_DummyHandlerBase):
        def get_sub_items(self, item_type, item_id, sub_item_type, **kwargs):
            return [{"id": 9001, "changes_id": 2623, "tickets_id": 47}]

        def delete_items(self, item_type, ids, *, purge, log):
            captured["purge"] = purge
            captured["log"] = log
            return [{"9001": True}]

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    assistance.unlink_ticket_change("Ticket", 47, 2623, purge="1", keep_history="0")

    assert captured["purge"] is True
    assert captured["log"] is False


def test_unlink_ticket_change_switches_profile_before_entity(monkeypatch):
    calls = []

    class DummyHandler(_DummyHandlerBase):
        def change_active_profile(self, profile_id):
            calls.append(("profile", profile_id))

        def change_active_entity(self, entity_id):
            calls.append(("entity", entity_id))

        def get_sub_items(self, item_type, item_id, sub_item_type, **kwargs):
            return [{"id": 9001, "changes_id": 2623, "tickets_id": 47}]

        def delete_items(self, item_type, ids, *, purge, log):
            return [{"9001": True}]

    monkeypatch.setattr(assistance, "RequestHandler", DummyHandler)

    assistance.unlink_ticket_change("Ticket", 47, 2623, entity_id=11, profile_id=24)

    # Two separate sessions: one to resolve the relation id (fetch_paginated_subitems),
    # one to delete it -- each switches profile before entity.
    assert calls == [("profile", 24), ("entity", 11), ("profile", 24), ("entity", 11)]
