"""Use Forgejo instance to fetch token permissions, ids, and incomng_label

Note: for some reason, the request:

    /api/v1/repos/{owner}/{repo}

does not require a token. If the owner and the repo are known, the request
will emit a complete repository-record including the complete owner-record.
"""
from __future__ import annotations

import logging
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

logger = logging.getLogger('dump_things_service')

# Timeout for requests
_timeout = 10


# Base class for classes that use method-level caching. The cache lives in
# the class instance and will be deleted when the instance is deleted.
class MethodCache:
    def __init__(self):
        self.__cached_data = {}

    @staticmethod
    def cache_temporary(
        duration: int = 3600,
    ) -> Callable:
        """ Cache results for a given time (default: 3600 seconds) """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                self = args[0]
                key = (func.__qualname__, *(args[1:]), *(kwargs.items()))
                cached_data = self.__cached_data.get(key)
                if cached_data is None or time.time() - cached_data[0] > duration:
                    self.__cached_data[key] = (time.time(), func(*args, **kwargs))
                return self.__cached_data[key][1]
            return wrapper
        return decorator


class RemoteAuthenticationError(AuthenticationError):
    """Exception for remote authentication errors."""
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(f'Authentication failed with status {status}: {message}')


class ForgejoAuthenticationSource(AuthenticationSource, MethodCache):
    def __init__(
        self,
        api_url: str,
        organization: str,
        team: str,
        label_type: str,
        repository: str | None = None,
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
        :param label_type:  'team' or 'user', determines how the incoming label
            is created.
        :param repository:  Optional repository. If this is provided, access
            will only be granted if the team has access to the repository.
        """
        super().__init__()
        self.api_url = api_url[:-1] if api_url[-1] == '/' else api_url
        self.organization = organization
        self.team = team
        self.label_type = label_type
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
        except requests.exceptions.RequestException as e:
            msg = f'could not read from {self.api_url}/{endpoint}'
            raise RemoteAuthenticationError(
                status=HTTP_401_UNAUTHORIZED,
                message=msg,
            ) from e

        if r.status_code >= HTTP_300_MULTIPLE_CHOICES:
            msg = f'invalid token: ({r.status_code}): {r.text}'
            raise InvalidTokenError(msg)
        return r.json()

    def _get_user(
            self,
            token: str,
    ) -> dict:
        return self._get_json_from_endpoint('user', token)

    @MethodCache.cache_temporary()
    def _get_organization(self, token: str) -> dict:
        return self._get_json_from_endpoint(
            f'orgs/{self.organization}',
            token,
        )

    def _get_teams_for_user(self, token: str) -> dict:
        r = self._get_json_from_endpoint('user/teams', token)
        return {team['name']: team for team in r}

    @MethodCache.cache_temporary()
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

    @MethodCache.cache_temporary()
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
    def _get_permissions(code_permission: str) -> TokenPermission:
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

        logger.debug(f'starting Forgejo authentication: {self.api_url}, {self.organization}, {self.team}')

        user_teams = self._get_teams_for_user(token)
        logger.debug(f'user_teams: {user_teams}')

        if self.team not in user_teams:
            logger.debug(f'{self.team} not in user\'s teams')
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
        logger.debug(f'organization_teams: {organization_teams}')

        # Check that the configured team exists
        team = organization_teams.get(self.team)
        if not team:
            logger.debug(f'{self.team} not in organization teams')
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
            logger.debug(f'no unit `repo.code` in team {self.team}')
            msg = f'no `repo.code`-unit defined for team `{self.team}` in organization {self.organization}'
            raise RemoteAuthenticationError(
                status=HTTP_401_UNAUTHORIZED,
                message=msg,
            )

        logger.debug(f'authentication success, team permissions: {code_permissions}')
        return AuthenticationInfo(
            token_permission=self._get_permissions(code_permissions),
            user_id=user_info['email'],
            incoming_label=
                f'forgejo-team-{organization["name"]}-{team["name"]}'
                if self.label_type == 'team'
                else f'forgejo-user-{user_info["login"]}',
        )
