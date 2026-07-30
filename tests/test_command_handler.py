import json

import pytest

from mcp_glpi.GLPiHandler import CommandHandler
from mcp_glpi.glpi import session as glpi_session
from mcp_glpi.glpi import tickets as glpi_tickets
from mcp_glpi.glpi import changes as glpi_changes
from mcp_glpi.glpi import generic as glpi_generic
from mcp_glpi.glpi import files as glpi_files
from mcp_glpi.glpi import assistance as glpi_assistance


class DummyResult:
    def __init__(self, summary_text='Ticket created (id=99): Demo', payload=None):
        self._summary_text = summary_text
        self._payload = payload or {'payload': {'name': 'Demo'}}

    def summary(self):
        return self._summary_text

    def as_dict(self):
        return self._payload


def _extract_json(response):
    assert response
    content = response[0]
    assert content.type == 'text'
    return json.loads(content.text)


def test_unknown_command_returns_friendly_message():
    response = CommandHandler('nope').execute()
    payload = _extract_json(response)
    assert payload['ok'] is False
    assert payload['command'] == 'nope'
    assert payload['error']['type'] == 'unknown_command'
    assert payload['error']['message'] == 'Herramienta desconocida: nope'


def test_session_validate_uses_session_module(monkeypatch):
    monkeypatch.setattr(glpi_session, 'get_full_session_data', lambda: {'status': 'OK'})
    response = CommandHandler('session_validate').execute()
    payload = _extract_json(response)
    assert payload == {
        'ok': True,
        'command': 'session_validate',
        'data': {'status': 'OK'},
    }


def test_entityprofile_list_uses_session_module(monkeypatch):
    monkeypatch.setattr(
        glpi_session,
        'get_my_profiles_data',
        lambda: [{'id': 22, 'name': 'Administrativo - Solicitante', 'entities': [{'id': 2, 'name': 'Administrativo', 'is_recursive': True}]}],
    )
    response = CommandHandler('entityprofile_list', {}).execute()
    payload = _extract_json(response)
    assert payload == {
        'ok': True,
        'command': 'entityprofile_list',
        'data': [{'id': 22, 'name': 'Administrativo - Solicitante', 'entities': [{'id': 2, 'name': 'Administrativo', 'is_recursive': True}]}],
    }


_SAMPLE_PROFILES = [
    {
        'id': 22,
        'name': 'Administrativo - Solicitante',
        'entities': [
            {'id': 2, 'name': 'Administrativo', 'is_recursive': True},
        ],
    },
    {
        'id': 24,
        'name': 'Desarrollador',
        'entities': [
            {'id': 6, 'name': 'Desarrollo', 'is_recursive': False},
            {'id': 9, 'name': 'QA', 'is_recursive': False},
        ],
    },
]


def test_resolve_profile_name_switches_and_picks_first_entity(monkeypatch):
    monkeypatch.setattr(glpi_session, 'get_my_profiles_data', lambda: _SAMPLE_PROFILES)
    captured = {}

    def fake_all_tickets(**kwargs):
        captured.update(kwargs)
        return [{'id': 1}]

    monkeypatch.setattr(glpi_tickets, 'all_tickets', fake_all_tickets)

    response = CommandHandler('ticket_list', {'profile_id': 'Desarrollador'}).execute()
    payload = _extract_json(response)

    assert payload['ok'] is True
    assert captured['profile_id'] == 24
    assert captured['entity_id'] == 6
    notes = payload['resolution_notes']
    assert any('Desarrollador' in n for n in notes)
    assert any('Desarrollo' in n for n in notes)


def test_resolve_entity_name_finds_profile_and_entity(monkeypatch):
    monkeypatch.setattr(glpi_session, 'get_my_profiles_data', lambda: _SAMPLE_PROFILES)
    captured = {}

    def fake_all_tickets(**kwargs):
        captured.update(kwargs)
        return [{'id': 1}]

    monkeypatch.setattr(glpi_tickets, 'all_tickets', fake_all_tickets)

    response = CommandHandler('ticket_list', {'entity_id': 'QA'}).execute()
    payload = _extract_json(response)

    assert payload['ok'] is True
    assert captured['entity_id'] == 9
    assert captured['profile_id'] == 24
    assert 'resolution_notes' in payload


def test_resolve_entity_name_scoped_to_given_numeric_profile(monkeypatch):
    # 'QA' exists both under profile 24 and under profile 30 in this test;
    # an explicit numeric profile_id must scope the entity-name search.
    profiles = _SAMPLE_PROFILES + [
        {'id': 30, 'name': 'Otro perfil', 'entities': [{'id': 40, 'name': 'QA', 'is_recursive': False}]},
    ]
    monkeypatch.setattr(glpi_session, 'get_my_profiles_data', lambda: profiles)
    captured = {}

    def fake_all_tickets(**kwargs):
        captured.update(kwargs)
        return [{'id': 1}]

    monkeypatch.setattr(glpi_tickets, 'all_tickets', fake_all_tickets)

    response = CommandHandler('ticket_list', {'entity_id': 'QA', 'profile_id': 24}).execute()
    payload = _extract_json(response)

    assert payload['ok'] is True
    assert captured['entity_id'] == 9
    assert captured['profile_id'] == 24


def test_resolve_entity_name_ambiguous_is_validation_error(monkeypatch):
    profiles = _SAMPLE_PROFILES + [
        {'id': 30, 'name': 'Otro perfil', 'entities': [{'id': 40, 'name': 'QA', 'is_recursive': False}]},
    ]
    monkeypatch.setattr(glpi_session, 'get_my_profiles_data', lambda: profiles)

    response = CommandHandler('ticket_list', {'entity_id': 'QA'}).execute()
    payload = _extract_json(response)

    assert payload['ok'] is False
    assert payload['error']['type'] == 'validation_error'
    assert 'ambiguo' in payload['error']['message']


def test_resolve_profile_name_ambiguous_is_validation_error(monkeypatch):
    profiles = _SAMPLE_PROFILES + [
        {'id': 31, 'name': 'Desarrollador', 'entities': []},
    ]
    monkeypatch.setattr(glpi_session, 'get_my_profiles_data', lambda: profiles)

    response = CommandHandler('ticket_list', {'profile_id': 'Desarrollador'}).execute()
    payload = _extract_json(response)

    assert payload['ok'] is False
    assert payload['error']['type'] == 'validation_error'
    assert 'ambiguo' in payload['error']['message']


def test_resolve_profile_name_not_found_is_validation_error(monkeypatch):
    monkeypatch.setattr(glpi_session, 'get_my_profiles_data', lambda: _SAMPLE_PROFILES)

    response = CommandHandler('ticket_list', {'profile_id': 'No Existe'}).execute()
    payload = _extract_json(response)

    assert payload['ok'] is False
    assert payload['error']['type'] == 'validation_error'
    assert 'No se encontro el perfil' in payload['error']['message']


def test_resolve_entity_name_not_found_is_validation_error(monkeypatch):
    monkeypatch.setattr(glpi_session, 'get_my_profiles_data', lambda: _SAMPLE_PROFILES)

    response = CommandHandler('ticket_list', {'entity_id': 'No Existe'}).execute()
    payload = _extract_json(response)

    assert payload['ok'] is False
    assert payload['error']['type'] == 'validation_error'
    assert 'No se encontro la entidad' in payload['error']['message']


def test_resolve_profile_name_without_entities_is_validation_error(monkeypatch):
    profiles = [{'id': 50, 'name': 'Sin Entidades', 'entities': []}]
    monkeypatch.setattr(glpi_session, 'get_my_profiles_data', lambda: profiles)

    response = CommandHandler('ticket_list', {'profile_id': 'Sin Entidades'}).execute()
    payload = _extract_json(response)

    assert payload['ok'] is False
    assert payload['error']['type'] == 'validation_error'
    assert 'no tiene entidades' in payload['error']['message']


def test_numeric_entity_and_profile_id_do_not_trigger_name_resolution(monkeypatch):
    def boom():
        raise AssertionError('get_my_profiles_data should not be called for numeric ids')

    monkeypatch.setattr(glpi_session, 'get_my_profiles_data', boom)
    captured = {}

    def fake_all_tickets(**kwargs):
        captured.update(kwargs)
        return [{'id': 1}]

    monkeypatch.setattr(glpi_tickets, 'all_tickets', fake_all_tickets)

    response = CommandHandler('ticket_list', {'entity_id': '6', 'profile_id': '24'}).execute()
    payload = _extract_json(response)

    assert payload['ok'] is True
    assert captured['entity_id'] == 6
    assert captured['profile_id'] == 24
    assert 'resolution_notes' not in payload


def test_ticket_delete_requires_ticket_id():
    response = CommandHandler('ticket_delete', {}).execute()
    payload = _extract_json(response)
    assert payload['ok'] is False
    assert payload['error']['type'] == 'validation_error'


def test_ticket_delete_forwards_arguments(monkeypatch):
    captured = {}

    def fake_delete_ticket(**kwargs):
        captured.update(kwargs)
        return DummyResult(summary_text='Deleted ticket 10', payload={'payload': kwargs})

    monkeypatch.setattr(glpi_tickets, 'delete_ticket', fake_delete_ticket)

    response = CommandHandler(
        'ticket_delete', {'ticket_id': 10, 'purge': True, 'entity_id': 3}
    ).execute()
    payload = _extract_json(response)

    assert payload['ok'] is True
    assert payload['summary'] == 'Deleted ticket 10'
    assert captured['ticket_id'] == 10
    assert captured['purge'] is True
    assert captured['entity_id'] == 3


def test_change_delete_forwards_arguments(monkeypatch):
    captured = {}

    def fake_delete_change(**kwargs):
        captured.update(kwargs)
        return DummyResult(summary_text='Deleted change 20', payload={'payload': kwargs})

    monkeypatch.setattr(glpi_changes, 'delete_change', fake_delete_change)

    response = CommandHandler('change_delete', {'change_id': 20}).execute()
    payload = _extract_json(response)

    assert payload['ok'] is True
    assert payload['summary'] == 'Deleted change 20'
    assert captured['change_id'] == 20
    assert captured['entity_id'] is None


def test_list_tickets_with_blank_entity_id_is_treated_as_omitted(monkeypatch):
    captured = {}

    def fake_all_tickets(**kwargs):
        captured.update(kwargs)
        return [{'id': 1}]

    monkeypatch.setattr(glpi_tickets, 'all_tickets', fake_all_tickets)

    response = CommandHandler('ticket_list', {'entity_id': ''}).execute()
    payload = _extract_json(response)

    assert payload['ok'] is True
    assert captured['entity_id'] is None


def test_ticket_add_with_blank_entity_id_is_treated_as_omitted(monkeypatch):
    captured = {}

    def fake_create_ticket(**kwargs):
        captured.update(kwargs)
        return DummyResult(payload={'payload': kwargs, 'response': {'id': 1, 'name': 'Demo'}})

    monkeypatch.setattr(glpi_tickets, 'create_ticket', fake_create_ticket)

    response = CommandHandler('ticket_add', {'name': 'Demo', 'entity_id': '  '}).execute()
    payload = _extract_json(response)

    assert payload['ok'] is True
    assert captured['entity_id'] is None


def test_ticket_list_forwards_entity_id(monkeypatch):
    captured = {}

    def fake_all_tickets(**kwargs):
        captured.update(kwargs)
        return [{'id': 1}]

    monkeypatch.setattr(glpi_tickets, 'all_tickets', fake_all_tickets)

    CommandHandler('ticket_list', {'entity_id': '6'}).execute()

    assert captured['entity_id'] == 6


def test_ticket_add_forwards_entity_id_alias(monkeypatch):
    captured = {}

    def fake_create_ticket(**kwargs):
        captured.update(kwargs)
        return DummyResult(payload={'payload': kwargs, 'response': {'id': 1, 'name': 'Demo'}})

    monkeypatch.setattr(glpi_tickets, 'create_ticket', fake_create_ticket)

    CommandHandler('ticket_add', {'name': 'Demo', 'entities_id': '8'}).execute()

    assert captured['entity_id'] == 8


def test_ticket_list_forwards_profile_id(monkeypatch):
    captured = {}

    def fake_all_tickets(**kwargs):
        captured.update(kwargs)
        return [{'id': 1}]

    monkeypatch.setattr(glpi_tickets, 'all_tickets', fake_all_tickets)

    CommandHandler('ticket_list', {'profile_id': '24'}).execute()

    assert captured['profile_id'] == 24


def test_ticket_add_forwards_profile_id_alias(monkeypatch):
    captured = {}

    def fake_create_ticket(**kwargs):
        captured.update(kwargs)
        return DummyResult(payload={'payload': kwargs, 'response': {'id': 1, 'name': 'Demo'}})

    monkeypatch.setattr(glpi_tickets, 'create_ticket', fake_create_ticket)

    CommandHandler('ticket_add', {'name': 'Demo', 'profiles_id': '17'}).execute()

    assert captured['profile_id'] == 17


def test_ticket_list_normalises_arguments(monkeypatch):
    captured = {}

    def fake_all_tickets(**kwargs):
        captured.update(kwargs)
        return [{'id': 1}]

    monkeypatch.setattr(glpi_tickets, 'all_tickets', fake_all_tickets)

    response = CommandHandler(
        'ticket_list',
        {
            'limit': '5',
            'offset': '2',
            'expand_dropdowns': 'true',
            'include_deleted': '1',
            'filters': {'status': 'open'},
        },
    ).execute()

    payload = _extract_json(response)
    assert payload == {
        'ok': True,
        'command': 'ticket_list',
        'data': [{'id': 1}],
    }
    assert captured['limit'] == 5
    assert captured['offset'] == 2
    assert captured['expand_dropdowns'] is True
    assert captured['include_deleted'] is True
    assert captured['filters'] == {'status': 'open'}


def test_ticket_list_defaults_to_dict_output(monkeypatch):
    captured = {}

    def fake_all_tickets(**kwargs):
        captured.update(kwargs)
        return {'tickets': [{'id': 1}], 'range': None}

    monkeypatch.setattr(glpi_tickets, 'all_tickets', fake_all_tickets)

    response = CommandHandler('ticket_list', {}).execute()

    payload = _extract_json(response)
    assert payload == {
        'ok': True,
        'command': 'ticket_list',
        'data': {'tickets': [{'id': 1}], 'range': None},
    }
    assert captured['output'] == 'dict'


def test_ticket_add_wraps_result_with_summary(monkeypatch):
    captured = {}

    def fake_create_ticket(**kwargs):
        captured.update(kwargs)
        return DummyResult(payload={'payload': kwargs, 'response': {'id': 42, 'name': 'Demo'}})

    monkeypatch.setattr(glpi_tickets, 'create_ticket', fake_create_ticket)

    response = CommandHandler(
        'ticket_add',
        {
            'name': 'Demo',
            'content': 'desc',
            'additional': {'foo': 'bar'},
        },
    ).execute()

    payload = _extract_json(response)
    assert payload['ok'] is True
    assert payload['command'] == 'ticket_add'
    assert payload['summary'] == 'Ticket created (id=99): Demo'
    assert payload['data']['payload']['additional_fields']['foo'] == 'bar'
    assert captured['name'] == 'Demo'
    assert captured['content'] == 'desc'


def test_ticket_add_value_error_is_reported(monkeypatch):
    def failing_create_ticket(**_kwargs):
        raise ValueError('boom')

    monkeypatch.setattr(glpi_tickets, 'create_ticket', failing_create_ticket)

    response = CommandHandler('ticket_add', {'name': 'Demo'}).execute()
    payload = _extract_json(response)
    assert payload['ok'] is False
    assert payload['error']['type'] == 'validation_error'
    assert payload['error']['message'] == 'Invalid argument: boom'


def test_change_add_merges_pr_links(monkeypatch):
    captured = {}

    def fake_create_change(**kwargs):
        captured.update(kwargs)
        return DummyResult(
            summary_text='Change created (id=77): Demo',
            payload={'payload': kwargs, 'response': {'id': 77, 'name': 'Demo'}},
        )

    monkeypatch.setattr(glpi_changes, 'create_change', fake_create_change)

    response = CommandHandler(
        'change_add',
        {
            'name': 'Demo change',
            'pr_links': [
                'https://example.com/pr/1',
                '  https://example.com/pr/2  ',
                '',
            ],
            'additional': {'other': 'value'},
        },
    ).execute()

    payload = _extract_json(response)
    assert payload['ok'] is True
    assert payload['summary'] == 'Change created (id=77): Demo'
    additional_fields = captured['additional_fields']
    assert additional_fields['other'] == 'value'
    assert additional_fields['controlistcontent'] == (
        '<p>https://example.com/pr/1</p><p>https://example.com/pr/2</p>'
    )


def test_change_update_merges_pr_links(monkeypatch):
    captured = {}

    def fake_update_change(**kwargs):
        captured.update(kwargs)
        return DummyResult(summary_text='Change updated', payload={'payload': kwargs})

    monkeypatch.setattr(glpi_changes, 'update_change', fake_update_change)

    original_fields = {'status': 3, 'controlistcontent': '<p>existing</p>'}
    response = CommandHandler(
        'change_update',
        {
            'change_id': 55,
            'fields': original_fields,
            'pr_links': ['https://example.com/pr/3'],
        },
    ).execute()

    payload = _extract_json(response)
    assert payload['ok'] is True
    assert payload['summary'] == 'Change updated'
    assert captured['change_id'] == 55
    merged_fields = captured['fields']
    assert merged_fields is not original_fields
    assert merged_fields['status'] == 3
    assert merged_fields['controlistcontent'] == '<p>existing</p><p>https://example.com/pr/3</p>'


def test_item_type_list_uses_generic_module(monkeypatch):
    monkeypatch.setattr(
        glpi_generic, 'list_itemtypes', lambda: [{'itemtype': 'Ticket', 'description': 'x'}]
    )
    response = CommandHandler('item_type_list', {}).execute()
    payload = _extract_json(response)
    assert payload['ok'] is True
    assert payload['data'] == [{'itemtype': 'Ticket', 'description': 'x'}]


def test_item_subtype_list_forwards_itemtype_filter(monkeypatch):
    captured = {}

    def fake_list_subtypes(itemtype):
        captured['itemtype'] = itemtype
        return [{'itemtype': 'Ticket', 'subtype': 'ITILFollowup', 'description': 'x'}]

    monkeypatch.setattr(glpi_generic, 'list_subtypes', fake_list_subtypes)

    response = CommandHandler('item_subtype_list', {'itemtype': 'Ticket'}).execute()
    payload = _extract_json(response)

    assert payload['ok'] is True
    assert captured['itemtype'] == 'Ticket'


def test_item_subtype_list_works_without_itemtype(monkeypatch):
    captured = {}

    def fake_list_subtypes(itemtype):
        captured['itemtype'] = itemtype
        return []

    monkeypatch.setattr(glpi_generic, 'list_subtypes', fake_list_subtypes)

    response = CommandHandler('item_subtype_list', {}).execute()
    payload = _extract_json(response)

    assert payload['ok'] is True
    assert captured['itemtype'] is None


def test_item_list_requires_itemtype():
    response = CommandHandler('item_list', {}).execute()
    payload = _extract_json(response)
    assert payload['ok'] is False
    assert payload['error']['type'] == 'validation_error'


def test_item_list_forwards_arguments(monkeypatch):
    captured = {}

    def fake_list_items(itemtype, **kwargs):
        captured['itemtype'] = itemtype
        captured.update(kwargs)
        return {'items': [{'id': 1}], 'range': None}

    monkeypatch.setattr(glpi_generic, 'list_items', fake_list_items)

    response = CommandHandler('item_list', {'itemtype': 'Ticket', 'limit': '5'}).execute()
    payload = _extract_json(response)

    assert payload['ok'] is True
    assert payload['data'] == {'items': [{'id': 1}], 'range': None}
    assert captured['itemtype'] == 'Ticket'
    assert captured['limit'] == 5


def test_item_list_reports_domain_value_error_as_validation_error(monkeypatch):
    # Any ValueError raised by the domain layer (glpi/generic.py) -- not
    # specifically an unsupported-itemtype rejection, since item_list no
    # longer restricts itemtype -- must surface as a validation_error.
    def failing_list_items(itemtype, **kwargs):
        raise ValueError(f"itemtype is required")

    monkeypatch.setattr(glpi_generic, 'list_items', failing_list_items)

    response = CommandHandler('item_list', {'itemtype': 'User'}).execute()
    payload = _extract_json(response)

    assert payload['ok'] is False
    assert payload['error']['type'] == 'validation_error'


def test_item_get_requires_itemtype_and_id():
    response = CommandHandler('item_get', {'itemtype': 'Ticket'}).execute()
    payload = _extract_json(response)
    assert payload['ok'] is False
    assert payload['error']['type'] == 'validation_error'


def test_item_get_forwards_arguments(monkeypatch):
    captured = {}

    def fake_get_item(itemtype, item_id, **kwargs):
        captured['itemtype'] = itemtype
        captured['item_id'] = item_id
        captured.update(kwargs)
        return {'id': item_id}

    monkeypatch.setattr(glpi_generic, 'get_item', fake_get_item)

    response = CommandHandler('item_get', {'itemtype': 'Ticket', 'id': '47'}).execute()
    payload = _extract_json(response)

    assert payload['ok'] is True
    assert payload['data'] == {'id': '47'}
    assert captured['itemtype'] == 'Ticket'
    assert captured['item_id'] == '47'


def test_item_get_reports_domain_value_error_as_validation_error(monkeypatch):
    # Same as above for item_get's domain layer.
    def failing_get_item(itemtype, item_id, **kwargs):
        raise ValueError(f"itemtype is required")

    monkeypatch.setattr(glpi_generic, 'get_item', failing_get_item)

    response = CommandHandler('item_get', {'itemtype': 'User', 'id': 1}).execute()
    payload = _extract_json(response)

    assert payload['ok'] is False
    assert payload['error']['type'] == 'validation_error'


def test_item_subitem_list_requires_itemtype_id_and_subtype():
    response = CommandHandler('item_subitem_list', {'itemtype': 'Ticket'}).execute()
    payload = _extract_json(response)
    assert payload['ok'] is False
    assert payload['error']['type'] == 'validation_error'


def test_item_subitem_list_forwards_arguments(monkeypatch):
    captured = {}

    def fake_list_subitems(itemtype, item_id, subtype, **kwargs):
        captured['itemtype'] = itemtype
        captured['item_id'] = item_id
        captured['subtype'] = subtype
        captured.update(kwargs)
        return {'items': [], 'range': None}

    monkeypatch.setattr(glpi_generic, 'list_subitems', fake_list_subitems)

    response = CommandHandler(
        'item_subitem_list', {'itemtype': 'Ticket', 'id': 47, 'subtype': 'ITILFollowup', 'entity_id': '11'}
    ).execute()
    payload = _extract_json(response)

    assert payload['ok'] is True
    assert captured['itemtype'] == 'Ticket'
    assert captured['item_id'] == 47
    assert captured['subtype'] == 'ITILFollowup'
    assert captured['entity_id'] == 11


def test_item_delete_requires_itemtype_and_id():
    response = CommandHandler('item_delete', {'itemtype': 'Ticket'}).execute()
    payload = _extract_json(response)
    assert payload['ok'] is False
    assert payload['error']['type'] == 'validation_error'


def test_item_delete_forwards_arguments(monkeypatch):
    captured = {}

    def fake_delete_item(itemtype, item_id, **kwargs):
        captured['itemtype'] = itemtype
        captured['item_id'] = item_id
        captured.update(kwargs)
        return DummyResult(summary_text='Deleted Ticket 15', payload={'response': {'deleted': [15]}})

    monkeypatch.setattr(glpi_generic, 'delete_item', fake_delete_item)

    response = CommandHandler(
        'item_delete', {'itemtype': 'Ticket', 'id': 15, 'purge': True, 'entity_id': '6'}
    ).execute()
    payload = _extract_json(response)

    assert payload['ok'] is True
    assert payload['summary'] == 'Deleted Ticket 15'
    assert captured['itemtype'] == 'Ticket'
    assert captured['item_id'] == 15
    assert captured['purge'] is True
    assert captured['entity_id'] == 6


def test_file_upload_requires_file_path():
    response = CommandHandler('file_upload', {}).execute()
    payload = _extract_json(response)
    assert payload['ok'] is False
    assert payload['error']['type'] == 'validation_error'


def test_file_upload_forwards_arguments(monkeypatch):
    captured = {}

    def fake_upload_document(file_path, **kwargs):
        captured['file_path'] = file_path
        captured.update(kwargs)
        return DummyResult(
            summary_text='Document created (id=5): Doc',
            payload={'response': {'id': 5}},
        )

    monkeypatch.setattr(glpi_files, 'upload_document', fake_upload_document)

    response = CommandHandler(
        'file_upload', {'file_path': 'C:/tmp/doc.txt', 'name': 'Doc', 'entity_id': '6'}
    ).execute()
    payload = _extract_json(response)

    assert payload['ok'] is True
    assert payload['summary'] == 'Document created (id=5): Doc'
    assert captured['file_path'] == 'C:/tmp/doc.txt'
    assert captured['name'] == 'Doc'
    assert captured['entity_id'] == 6


def test_file_download_requires_document_id_and_destination():
    response = CommandHandler('file_download', {'document_id': 1}).execute()
    payload = _extract_json(response)
    assert payload['ok'] is False
    assert payload['error']['type'] == 'validation_error'


def test_file_download_forwards_arguments(monkeypatch):
    captured = {}

    def fake_download_document(document_id, destination_path, **kwargs):
        captured['document_id'] = document_id
        captured['destination_path'] = destination_path
        captured.update(kwargs)
        return DummyResult(
            summary_text='Downloaded document 5',
            payload={'response': {'bytes_written': 4}},
        )

    monkeypatch.setattr(glpi_files, 'download_document', fake_download_document)

    response = CommandHandler(
        'file_download',
        {'document_id': 5, 'destination_path': 'C:/tmp/out.bin', 'profile_id': '24'},
    ).execute()
    payload = _extract_json(response)

    assert payload['ok'] is True
    assert captured['document_id'] == 5
    assert captured['destination_path'] == 'C:/tmp/out.bin'
    assert captured['profile_id'] == 24


def test_file_link_requires_document_item_type_and_item_id():
    response = CommandHandler('file_link', {'document_id': 1}).execute()
    payload = _extract_json(response)
    assert payload['ok'] is False
    assert payload['error']['type'] == 'validation_error'


def test_file_link_forwards_arguments(monkeypatch):
    captured = {}

    def fake_link_item(**kwargs):
        captured.update(kwargs)
        return DummyResult(
            summary_text='Linked document 1 to Ticket 47',
            payload={'response': {'id': 9}},
        )

    monkeypatch.setattr(glpi_files, 'link_item', fake_link_item)

    response = CommandHandler(
        'file_link', {'document_id': 1, 'item_type': 'Ticket', 'item_id': 47, 'entity_id': '6'}
    ).execute()
    payload = _extract_json(response)

    assert payload['ok'] is True
    assert captured['document_id'] == 1
    assert captured['item_type'] == 'Ticket'
    assert captured['item_id'] == 47
    assert captured['entity_id'] == 6


def test_file_unlink_requires_document_id_and_link_id():
    response = CommandHandler('file_unlink', {'document_id': 1}).execute()
    payload = _extract_json(response)
    assert payload['ok'] is False
    assert payload['error']['type'] == 'validation_error'


def test_file_unlink_forwards_arguments(monkeypatch):
    captured = {}

    def fake_unlink_item(**kwargs):
        captured.update(kwargs)
        return DummyResult(
            summary_text='Unlinked document 1 from relation 9',
            payload={'response': {}},
        )

    monkeypatch.setattr(glpi_files, 'unlink_item', fake_unlink_item)

    response = CommandHandler(
        'file_unlink', {'document_id': 1, 'link_id': 9, 'purge': True}
    ).execute()
    payload = _extract_json(response)

    assert payload['ok'] is True
    assert captured['document_id'] == 1
    assert captured['link_id'] == 9
    assert captured['purge'] is True


def test_assistance_item_user_add_requires_itemtype_and_id():
    response = CommandHandler('assistance_item_user_add', {'users': {'users_id': 5}}).execute()
    payload = _extract_json(response)
    assert payload['ok'] is False
    assert payload['error']['type'] == 'validation_error'


def test_assistance_item_user_add_forwards_arguments(monkeypatch):
    captured = {}

    def fake_assign_assistance_users(**kwargs):
        captured.update(kwargs)
        return DummyResult(
            summary_text='Assigned 1 user(s) to Change 2620',
            payload={'id': 2620, 'response': {}},
        )

    monkeypatch.setattr(glpi_assistance, 'assign_assistance_users', fake_assign_assistance_users)

    response = CommandHandler(
        'assistance_item_user_add',
        {
            'itemtype': 'Change',
            'id': 2620,
            'users': {'users_id': 18, 'type': 1, 'use_notification': 0},
            'entity_id': '6',
        },
    ).execute()
    payload = _extract_json(response)

    assert payload['ok'] is True
    assert captured['itemtype'] == 'Change'
    assert captured['item_id'] == 2620
    assert captured['users'] == {'users_id': 18, 'type': 1, 'use_notification': 0}
    assert captured['entity_id'] == 6


def test_assistance_item_group_add_requires_itemtype_and_id():
    response = CommandHandler('assistance_item_group_add', {'groups': {'groups_id': 5}}).execute()
    payload = _extract_json(response)
    assert payload['ok'] is False
    assert payload['error']['type'] == 'validation_error'


def test_assistance_item_group_add_forwards_arguments(monkeypatch):
    captured = {}

    def fake_assign_assistance_groups(**kwargs):
        captured.update(kwargs)
        return DummyResult(
            summary_text='Assigned 1 group(s) to Ticket 2079',
            payload={'id': 2079, 'response': {}},
        )

    monkeypatch.setattr(glpi_assistance, 'assign_assistance_groups', fake_assign_assistance_groups)

    response = CommandHandler(
        'assistance_item_group_add',
        {
            'itemtype': 'Ticket',
            'id': 2079,
            'groups': {'groups_id': 5, 'type': 1, 'use_notification': 0},
            'entity_id': '6',
        },
    ).execute()
    payload = _extract_json(response)

    assert payload['ok'] is True
    assert captured['itemtype'] == 'Ticket'
    assert captured['item_id'] == 2079
    assert captured['groups'] == {'groups_id': 5, 'type': 1, 'use_notification': 0}
    assert captured['entity_id'] == 6


def test_assistance_item_followup_add_requires_itemtype_and_id():
    response = CommandHandler('assistance_item_followup_add', {'content': 'hola'}).execute()
    payload = _extract_json(response)
    assert payload['ok'] is False
    assert payload['error']['type'] == 'validation_error'


def test_assistance_item_followup_add_forwards_arguments(monkeypatch):
    captured = {}

    def fake_add_assistance_followup(**kwargs):
        captured.update(kwargs)
        return DummyResult(
            summary_text='Added follow-up to Change 2620',
            payload={'id': 2620, 'response': {}},
        )

    monkeypatch.setattr(glpi_assistance, 'add_assistance_followup', fake_add_assistance_followup)

    response = CommandHandler(
        'assistance_item_followup_add',
        {
            'itemtype': 'Change',
            'id': 2620,
            'content': 'pruebas de ticketssss',
            'is_private': 0,
            'entity_id': '6',
        },
    ).execute()
    payload = _extract_json(response)

    assert payload['ok'] is True
    assert captured['itemtype'] == 'Change'
    assert captured['item_id'] == 2620
    assert captured['content'] == 'pruebas de ticketssss'
    assert captured['is_private'] is False
    assert captured['entity_id'] == 6
