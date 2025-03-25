from dump_things_service.utils import cleaned_json


def test_cleaned_json():
    dirty_data = {
        'pid': 'trr379:contributors/michael-hanke',
        'schema_type': 'dlsocial:Person',
        'identifiers': [
            {
                'notation': '0000-0001-6398-6370',
                'creator': 'https://orcid.org',
                'schema_type': 'dlidentifiers:Identifier',
                'empty': None,
            }
        ],
        'empty': None,
        'family_name': 'Hanke',
        'given_name': 'Michael',
        'honorific_name_prefix': 'Prof. Dr.',
        '@type': 'Person',
    }
    clean_data = cleaned_json(dirty_data)
    assert clean_data is not dirty_data
    assert clean_data == {
        'pid': 'trr379:contributors/michael-hanke',
        'schema_type': 'dlsocial:Person',
        'identifiers': [
            {
                'notation': '0000-0001-6398-6370',
                'creator': 'https://orcid.org',
                'schema_type': 'dlidentifiers:Identifier',
            }
        ],
        'family_name': 'Hanke',
        'given_name': 'Michael',
        'honorific_name_prefix': 'Prof. Dr.',
    }
