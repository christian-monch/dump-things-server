from __future__ import annotations

import json

import pytest

from dump_things_service.auth.forgejo import ForgejoAuthenticationSource
from dump_things_service.token import TokenPermission

user_1 = {
    'id': 1,
    'login': 'user_1',
    'email': 'user_1@example.com',
    'username': 'user_1',
    '@type': 'user',
}

org_1 = {
    'id': 1,
    'name': 'org_1',
    '@type': 'org'
}

repo_1 = {
    'id': 3,
    'owner': user_1,
    'name': 'repo_1',
}

team_template = """{{
    "id": {id},
    "name": "team_{id}",
    "units_map": {{
        "repo.code": "read",
        "repo.actions": "{action}"
    }},
    "@type": "team"
}}
"""

team_1 = json.loads(team_template.format(id=1, action='none'))
team_2 = json.loads(team_template.format(id=2, action='none'))
team_3 = json.loads(team_template.format(id=3, action='write'))

def setup_http_server(http_server) -> None:
    http_server.expect_request('/api/v1/user').respond_with_json(user_1)
    http_server.expect_request('/api/v1/user/teams').respond_with_json([team_1, team_3])
    http_server.expect_request('/api/v1/orgs/org_1').respond_with_json(org_1)
    http_server.expect_request('/api/v1/orgs/org_1/teams').respond_with_json([team_1, team_2, team_3])
    http_server.expect_request('/api/v1/repos/org_1/repo_1/teams').respond_with_json([team_1, team_2, team_3])


@pytest.mark.parametrize('repository', ['repo_1', None])
@pytest.mark.parametrize('label_type', ['user', 'team'])
def test_forgejo_auth_team(httpserver, label_type, repository):
    setup_http_server(httpserver)

    forgejo_auth_source = ForgejoAuthenticationSource(
        api_url=httpserver.url_for('/api/v1'),
        organization='org_1',
        team='team_1',
        label_type=label_type,
        repository=repository,
    )

    r = forgejo_auth_source.authenticate(token='something')
    if label_type == 'team':
        assert r.incoming_label == 'forgejo-team-org_1-team_1'
    else:
        assert r.incoming_label == 'forgejo-user-user_1'
    assert r.token_permission == TokenPermission(
        curated_read=True,
        incoming_read=True,
        incoming_write=False,
    )
    assert r.user_id == 'user_1@example.com'


@pytest.mark.parametrize('repository', ['repo_1', None])
@pytest.mark.parametrize('label_type', ['user', 'team'])
def test_forgejo_auth_curator(httpserver, label_type, repository):
    setup_http_server(httpserver)

    forgejo_auth_source = ForgejoAuthenticationSource(
        api_url=httpserver.url_for('/api/v1'),
        organization='org_1',
        team='team_3',
        label_type=label_type,
        repository=repository,
    )

    r = forgejo_auth_source.authenticate(token='something')
    if label_type == 'team':
        assert r.incoming_label == 'forgejo-team-org_1-team_3'
    else:
        assert r.incoming_label == 'forgejo-user-user_1'
    assert r.token_permission == TokenPermission(
        curated_read=True,
        incoming_read=True,
        incoming_write=True,
        curated_write=True,
        zones_access=True,
    )
    assert r.user_id == 'user_1@example.com'
