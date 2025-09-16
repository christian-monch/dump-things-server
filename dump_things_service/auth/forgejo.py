"""Use Forgejo instance to fetch token permissions, ids, and incomng_label """
from __future__ import annotations

import time
from functools import wraps
from typing import Callable

import requests
from requests.exceptions import Timeout

from dump_things_service import (
    HTTP_300_MULTIPLE_CHOICES,
    HTTP_401_UNAUTHORIZED,
)
from dump_things_service.auth import (
    AuthenticationError,
    AuthenticationInfo,
    AuthenticationSource,
    InvalidTokenError,
)
from dump_things_service.config import TokenPermission

# Timeout for requests
_timeout = 10

_cached_data = {}


# Cache data based on specific input variables
def cache_on(
    inputs: list[int | str],
    duration: int = 3600,
) -> Callable:
    """ Cache results based on a subset of inputs for a given time """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            key = (
                func.__qualname__,
                *tuple(
                    args[x] if isinstance(x, int)
                    else kwargs[x]
                    for x in inputs if (
                        isinstance(x, int)
                        or isinstance(x, str) and x in kwargs
                    )
                )
            )
            cached_data = _cached_data.get(key)
            if cached_data is None or time.time() - cached_data[0] > duration:
                _cached_data[key] = (time.time(), func(*args, **kwargs))
            return _cached_data[key][1]
        return wrapper
    return decorator


class RemoteAuthenticationError(AuthenticationError):
    """Exception for remote authentication errors."""
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(f'Authentication failed with status {status}: {message}')


class ForgejoAuthenticationSource(AuthenticationSource):
    def __init__(
        self,
        api_url: str,
        organization: str,
        team: str,
        repository: str | None = None
    ):
        """
        Create a Forgejo authentication source.

        A token will be authorized if the associated user exists, is part of
        team `team`, and if the repository is accessible by the team `team`.
        The token permissions are taken from the unit mapping `repo.code` in the
        team definition.

        :param api_url: Forgejo API URL
        :param organization: The name of the organization that defines the team
        :param team:  The name of the team
        :param repository:  Optional repository. If this is provided, access
            will only be granted if the team has access to the repository.
        """
        self.api_url = api_url[:-1] if api_url[-1] == '/' else api_url
        self.organization = organization
        self.team = team
        self.repository = repository

    def _get_json_from_endpoint(
        self,
        endpoint: str,
        token: str,
    ):
        try:
            r = requests.get(
                url=f'{self.api_url}/{endpoint}',
                headers={
                    'Accept': 'application/json',
                    'Authorization': f'token {token}',
                },
                timeout=_timeout,
            )
        except Timeout as e:
            msg = f'timeout in request to {self.api_url}'
            raise RemoteAuthenticationError(
                status=HTTP_401_UNAUTHORIZED,
                message=msg,
            ) from e

        if r.status_code >= HTTP_300_MULTIPLE_CHOICES:
            msg = f'invalid token: ({r.status_code}): {r.txt}'
            raise InvalidTokenError(msg)
        return r.json()

    @cache_on([1])
    def _get_user(
            self,
            token: str,
    ) -> dict:
        return self._get_json_from_endpoint('user', token)

    @cache_on([1])
    def _get_organization(self, token: str) -> dict:
        return self._get_json_from_endpoint(
            f'orgs/{self.organization}',
            token,
        )

    @cache_on([1])
    def _get_teams_for_user(self, token: str) -> dict:
        r = self._get_json_from_endpoint('user/teams', token)
        return {team['name']: team for team in r}

    @cache_on([1, 2])
    def _get_teams_for_organization(
        self,
        token: str,
        organization: str,
    ):
        r = self._get_json_from_endpoint(
            f'orgs/{organization}/teams',
            token,
        )
        return {team['name']: team for team in r}

    @cache_on([1, 2, 3])
    def _get_teams_for_repo(
        self,
        token: str,
        organization: str,
        repository: str,
    ):
        r = self._get_json_from_endpoint(
            f'repos/{organization}/{repository}/teams',
            token,
        )
        return {team['name']: team for team in r}

    @staticmethod
    def _get_permissions(code_permission) -> TokenPermission:
        read = code_permission in ('read', 'write')
        write = code_permission == 'write'
        return TokenPermission(
            curated_read=read,
            incoming_read=read,
            incoming_write=write,
        )

    def authenticate(
        self,
        token: str,
    ) -> AuthenticationInfo:

        user_teams = self._get_teams_for_user(token)
        if self.team not in user_teams:
            msg = f'token user is not member of team `{self.team}`'
            raise RemoteAuthenticationError(
                status=HTTP_401_UNAUTHORIZED,
                message=msg,
            )

        organization = self._get_organization(token)
        user_info = self._get_user(token)

        if self.repository is not None:
            organization_teams = self._get_teams_for_repo(
                token,
                self.organization,
                self.repository,
            )
        else:
            organization_teams = self._get_teams_for_organization(
                token,
                self.organization,
            )

        # Check that the configured team exists
        team = organization_teams.get(self.team)
        if not team:
            if self.repository is not None:
                msg = f'team `{self.team}` has no access to repository `{self.repository}`'
            else:
                msg = f'organization `{self.organization}` has no team `{self.team}`'
            raise RemoteAuthenticationError(
                status=HTTP_401_UNAUTHORIZED,
                message=msg,
            )

        # Get the repo.code permissions from the team definition
        code_permissions = team['units_map'].get('repo.code')
        if not code_permissions:
            msg = f'no `repo.code`-unit defined for team `{self.team}` in organization {self.organization}'
            raise RemoteAuthenticationError(
                status=HTTP_401_UNAUTHORIZED,
                message=msg,
            )

        return AuthenticationInfo(
            token_permission=self._get_permissions(code_permissions),
            user_id=user_info['email'],
            incoming_label=f'forgejo-{organization["name"]}-{team["name"]}',
        )
