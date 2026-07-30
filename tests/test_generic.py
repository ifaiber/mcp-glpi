import pytest

from mcp_glpi.glpi import generic
from glpi_client import GLPIError


class _NoRangeDummyHandler:
    """GLPI's list/sub-item endpoints don't always send Content-Range."""

    def __init__(self, *args, **kwargs):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    @property
    def response_range(self):
        raise GLPIError("The previous request did not return a range")


def test_list_itemtypes_returns_catalog():
    result = generic.list_itemtypes()
    names = {entry['itemtype'] for entry in result}
    assert names == set(generic.ITEMTYPE_CATALOG.keys())
    assert {'Ticket', 'Change', 'Document', 'Computer', 'Monitor', 'Software'} <= names
    assert all(entry['description'] for entry in result)


def test_list_subtypes_without_filter_returns_all():
    result = generic.list_subtypes()
    itemtypes = {entry['itemtype'] for entry in result}
    assert {'Ticket', 'Change', 'Computer', 'Monitor', 'Software', 'Project'} <= itemtypes


def test_list_subtypes_includes_document_item_for_ticket_and_change():
    result = generic.list_subtypes()
    subtypes_by_itemtype = {}
    for entry in result:
        subtypes_by_itemtype.setdefault(entry['itemtype'], set()).add(entry['subtype'])
    assert 'Document_Item' in subtypes_by_itemtype['Ticket']
    assert 'Document_Item' in subtypes_by_itemtype['Change']


def test_list_subtypes_document_has_none():
    # Document itself has no supported sub-items; it's a leaf itemtype in the catalog.
    result = generic.list_subtypes('Document')
    assert result == []


def test_list_subtypes_filtered_by_itemtype():
    result = generic.list_subtypes('Ticket')
    assert all(entry['itemtype'] == 'Ticket' for entry in result)
    subtypes = {entry['subtype'] for entry in result}
    assert 'Ticket_User' in subtypes
    assert 'Change_User' not in subtypes


def test_list_subtypes_returns_empty_for_itemtype_outside_catalog():
    # Not a restriction: item_subitem_list itself accepts any subtype; this
    # just means there's no curated guidance on file for 'User' yet.
    assert generic.list_subtypes('User') == []


def test_normalize_itemtype_accepts_any_nonblank_value():
    assert generic.normalize_itemtype('User') == 'User'
    assert generic.normalize_itemtype('Config') == 'Config'


def test_normalize_itemtype_rejects_blank():
    with pytest.raises(ValueError, match='itemtype is required'):
        generic.normalize_itemtype('')
    with pytest.raises(ValueError, match='itemtype is required'):
        generic.normalize_itemtype(None)


def test_normalize_subtype_accepts_any_nonblank_value():
    # Ticket_User isn't in the catalog under Change, but that's no longer
    # enforced here -- GLPI decides whether the route is valid.
    assert generic.normalize_subtype('Ticket_User') == 'Ticket_User'


def test_normalize_subtype_rejects_blank():
    with pytest.raises(ValueError, match='subtype is required'):
        generic.normalize_subtype('')


def test_list_items_lists_itemtype(monkeypatch):
    captured = {}

    class DummyHandler(_NoRangeDummyHandler):
        def get_many_items(self, itemtype, **kwargs):
            captured['itemtype'] = itemtype
            captured.update(kwargs)
            return [{'id': 1, 'name': 'Demo'}]

    monkeypatch.setattr(generic, 'RequestHandler', DummyHandler)

    result = generic.list_items('Ticket')

    assert captured['itemtype'] == 'Ticket'
    assert result == {'items': [{'id': 1, 'name': 'Demo'}], 'range': None}


def test_list_items_accepts_itemtype_outside_catalog(monkeypatch):
    captured = {}

    class DummyHandler(_NoRangeDummyHandler):
        def get_many_items(self, itemtype, **kwargs):
            captured['itemtype'] = itemtype
            return [{'id': 1}]

    monkeypatch.setattr(generic, 'RequestHandler', DummyHandler)

    result = generic.list_items('User')

    assert captured['itemtype'] == 'User'
    assert result['items'] == [{'id': 1}]


def test_list_items_table_output_requires_fields(monkeypatch):
    class DummyHandler(_NoRangeDummyHandler):
        def get_many_items(self, itemtype, **kwargs):
            return [{'id': 1}]

    monkeypatch.setattr(generic, 'RequestHandler', DummyHandler)

    with pytest.raises(ValueError, match="'fields' is required"):
        generic.list_items('Ticket', output='table')


def test_list_items_switches_entity_and_profile(monkeypatch):
    calls = []

    class DummyHandler(_NoRangeDummyHandler):
        def change_active_profile(self, profile_id):
            calls.append(('profile', profile_id))

        def change_active_entity(self, entity_id):
            calls.append(('entity', entity_id))

        def get_many_items(self, itemtype, **kwargs):
            return []

    monkeypatch.setattr(generic, 'RequestHandler', DummyHandler)

    generic.list_items('Ticket', entity_id=11, profile_id=24)

    assert calls == [('profile', 24), ('entity', 11)]


def test_get_item_fetches_single_item_when_id_given(monkeypatch):
    captured = {}

    class DummyHandler(_NoRangeDummyHandler):
        def get_item(self, itemtype, item_id, **kwargs):
            captured['itemtype'] = itemtype
            captured['item_id'] = item_id
            return {'id': item_id, 'name': 'Demo', 'extra': 'noise'}

    monkeypatch.setattr(generic, 'RequestHandler', DummyHandler)

    result = generic.get_item('Ticket', 47)

    assert captured['itemtype'] == 'Ticket'
    assert captured['item_id'] == 47
    assert result == {'id': 47, 'name': 'Demo', 'extra': 'noise'}


def test_get_item_applies_field_projection_for_single_item(monkeypatch):
    class DummyHandler(_NoRangeDummyHandler):
        def get_item(self, itemtype, item_id, **kwargs):
            return {'id': item_id, 'name': 'Demo', 'extra': 'noise'}

    monkeypatch.setattr(generic, 'RequestHandler', DummyHandler)

    result = generic.get_item('Ticket', 47, fields=['id', 'name'])

    assert result == {'id': 47, 'name': 'Demo'}


def test_get_item_accepts_itemtype_outside_catalog(monkeypatch):
    captured = {}

    class DummyHandler(_NoRangeDummyHandler):
        def get_item(self, itemtype, item_id, **kwargs):
            captured['itemtype'] = itemtype
            return {'id': item_id}

    monkeypatch.setattr(generic, 'RequestHandler', DummyHandler)

    result = generic.get_item('User', 3)

    assert captured['itemtype'] == 'User'
    assert result == {'id': 3}


def test_get_item_switches_entity_and_profile(monkeypatch):
    calls = []

    class DummyHandler(_NoRangeDummyHandler):
        def change_active_profile(self, profile_id):
            calls.append(('profile', profile_id))

        def change_active_entity(self, entity_id):
            calls.append(('entity', entity_id))

        def get_item(self, itemtype, item_id, **kwargs):
            return {'id': item_id}

    monkeypatch.setattr(generic, 'RequestHandler', DummyHandler)

    generic.get_item('Ticket', 47, entity_id=11, profile_id=24)

    assert calls == [('profile', 24), ('entity', 11)]


def test_list_subitems_forwards_call_and_switches_entity_profile(monkeypatch):
    calls = []
    captured = {}

    class DummyHandler(_NoRangeDummyHandler):
        def change_active_profile(self, profile_id):
            calls.append(('profile', profile_id))

        def change_active_entity(self, entity_id):
            calls.append(('entity', entity_id))

        def get_sub_items(self, itemtype, item_id, subtype, **kwargs):
            captured['itemtype'] = itemtype
            captured['item_id'] = item_id
            captured['subtype'] = subtype
            return [{'id': 1, 'content': 'hola'}]

    monkeypatch.setattr(generic, 'RequestHandler', DummyHandler)

    result = generic.list_subitems('Ticket', 47, 'ITILFollowup', entity_id=11, profile_id=24)

    assert calls == [('profile', 24), ('entity', 11)]
    assert captured['itemtype'] == 'Ticket'
    assert captured['item_id'] == 47
    assert captured['subtype'] == 'ITILFollowup'
    assert result == {'items': [{'id': 1, 'content': 'hola'}], 'range': None}


def test_list_subitems_accepts_combination_outside_catalog(monkeypatch):
    captured = {}

    class DummyHandler(_NoRangeDummyHandler):
        def get_sub_items(self, itemtype, item_id, subtype, **kwargs):
            captured['itemtype'] = itemtype
            captured['subtype'] = subtype
            return []

    monkeypatch.setattr(generic, 'RequestHandler', DummyHandler)

    # Ticket_User isn't catalogued under Change, but that's no longer
    # enforced here -- GLPI decides whether the route is valid.
    generic.list_subitems('Change', 1, 'Ticket_User')

    assert captured['itemtype'] == 'Change'
    assert captured['subtype'] == 'Ticket_User'


def test_list_subitems_supports_raw_output(monkeypatch):
    class DummyHandler(_NoRangeDummyHandler):
        def get_sub_items(self, itemtype, item_id, subtype, **kwargs):
            return [{'id': 9}]

    monkeypatch.setattr(generic, 'RequestHandler', DummyHandler)

    result = generic.list_subitems('Ticket', 47, 'ITILSolution', output='raw')

    assert result == [{'id': 9}]


def test_list_items_supports_document_itemtype(monkeypatch):
    class DummyHandler(_NoRangeDummyHandler):
        def get_many_items(self, itemtype, **kwargs):
            return [{'id': 1, 'name': 'file.txt', 'filename': 'file.txt'}]

    monkeypatch.setattr(generic, 'RequestHandler', DummyHandler)

    result = generic.list_items('Document')

    assert result['items'][0]['name'] == 'file.txt'


def test_get_item_supports_document_itemtype(monkeypatch):
    class DummyHandler(_NoRangeDummyHandler):
        def get_item(self, itemtype, item_id, **kwargs):
            return {'id': item_id, 'name': 'file.txt'}

    monkeypatch.setattr(generic, 'RequestHandler', DummyHandler)

    result = generic.get_item('Document', 1)

    assert result == {'id': 1, 'name': 'file.txt'}


def test_list_subitems_supports_document_item_under_ticket(monkeypatch):
    captured = {}

    class DummyHandler(_NoRangeDummyHandler):
        def get_sub_items(self, itemtype, item_id, subtype, **kwargs):
            captured['itemtype'] = itemtype
            captured['subtype'] = subtype
            return [{'id': 3, 'documents_id': 1, 'items_id': item_id}]

    monkeypatch.setattr(generic, 'RequestHandler', DummyHandler)

    result = generic.list_subitems('Ticket', 47, 'Document_Item')

    assert captured['itemtype'] == 'Ticket'
    assert captured['subtype'] == 'Document_Item'
    assert result['items'][0]['documents_id'] == 1


def test_list_items_supports_asset_itemtypes(monkeypatch):
    captured = {}

    class DummyHandler(_NoRangeDummyHandler):
        def get_many_items(self, itemtype, **kwargs):
            captured['itemtype'] = itemtype
            return [{'id': 1, 'name': 'PC-01'}]

    monkeypatch.setattr(generic, 'RequestHandler', DummyHandler)

    for itemtype in ('Computer', 'Monitor', 'Software'):
        result = generic.list_items(itemtype)
        assert captured['itemtype'] == itemtype
        assert result['items'][0]['name'] == 'PC-01'


def test_list_subitems_supports_computer_specific_subtypes(monkeypatch):
    class DummyHandler(_NoRangeDummyHandler):
        def get_sub_items(self, itemtype, item_id, subtype, **kwargs):
            return [{'id': 1}]

    monkeypatch.setattr(generic, 'RequestHandler', DummyHandler)

    for subtype in ('Item_SoftwareVersion', 'ComputerAntivirus', 'ComputerVirtualMachine', 'Ticket'):
        result = generic.list_subitems('Computer', 12, subtype)
        assert result['items'] == [{'id': 1}]


def test_list_subitems_accepts_computer_only_subtype_for_monitor(monkeypatch):
    # ComputerAntivirus isn't catalogued under Monitor; no longer enforced.
    class DummyHandler(_NoRangeDummyHandler):
        def get_sub_items(self, itemtype, item_id, subtype, **kwargs):
            return []

    monkeypatch.setattr(generic, 'RequestHandler', DummyHandler)

    generic.list_subitems('Monitor', 1, 'ComputerAntivirus')


def test_delete_item_deletes_via_delete_items(monkeypatch):
    captured = {}

    class DummyHandler(_NoRangeDummyHandler):
        def delete_items(self, itemtype, ids, *, purge, log):
            captured['itemtype'] = itemtype
            captured['ids'] = ids
            captured['purge'] = purge
            captured['log'] = log
            return {'deleted': ids}

    monkeypatch.setattr(generic, 'RequestHandler', DummyHandler)

    result = generic.delete_item('Ticket', '15', purge='1', keep_history='0')

    assert captured['itemtype'] == 'Ticket'
    assert captured['ids'] == [15]
    assert captured['purge'] is True
    assert captured['log'] is False
    assert result.summary() == 'Deleted Ticket 15'


def test_delete_item_accepts_itemtype_outside_catalog(monkeypatch):
    captured = {}

    class DummyHandler(_NoRangeDummyHandler):
        def delete_items(self, itemtype, ids, *, purge, log):
            captured['itemtype'] = itemtype
            return {'deleted': ids}

    monkeypatch.setattr(generic, 'RequestHandler', DummyHandler)

    generic.delete_item('User', 3)

    assert captured['itemtype'] == 'User'


def test_delete_item_switches_entity_and_profile(monkeypatch):
    calls = []

    class DummyHandler(_NoRangeDummyHandler):
        def change_active_profile(self, profile_id):
            calls.append(('profile', profile_id))

        def change_active_entity(self, entity_id):
            calls.append(('entity', entity_id))

        def delete_items(self, itemtype, ids, *, purge, log):
            return {'deleted': ids}

    monkeypatch.setattr(generic, 'RequestHandler', DummyHandler)

    generic.delete_item('Ticket', 15, entity_id=11, profile_id=24)

    assert calls == [('profile', 24), ('entity', 11)]
