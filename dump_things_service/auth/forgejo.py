"""Use Forgejo instance to fetch token permissions, ids, and incomng_label """
import requests

from dump_things_service.auth import (
    AuthenticationError,
    AuthenticationInfo,
    AuthenticationSource,
    InvalidTokenError,
)
from dump_things_service.config import TokenPermission


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
        repo: str,
    ):
        self.api_url = api_url
        self.repo = repo

    def _get_user_for_token(
        self,
        token: str,
    ) -> dict:
        r = requests.get(
            url=f'{self.api_url}/user',
            headers={
                'Accept': 'application/json',
                'Authorization': f'token {token}',
            },
        )
        if 200 <= r.status_code < 300:
            return r.json()
        raise InvalidTokenError(f'Invalid token: ({r.status_code}: {r.text})')

    def _get_permissions(
            self,
            token: str,
            user: str,
    ) -> TokenPermission:

        r = requests.get(
            url=f'{self.api_url}/repos/{user}/{self.repo}',
            headers=
            {
                'Accept': 'application/json',
                'Authorization': f'token {token}',
            },
        )

        if 200 <= r.status_code < 300:
            return TokenPermission(
                curated_read=r.json()['permissions']['pull'],
                incoming_read=r.json()['permissions']['pull'],
                incoming_write=r.json()['permissions']['push'],
            )
        raise RemoteAuthenticationError(
            status=r.status_code,
            message=f'repository not found: \'{user}/{self.repo}\'. '
                    f'(message from host: {r.text})'
        )

    def authenticate(
        self,
        token: str,
    ) -> AuthenticationInfo:
        user_info = self._get_user_for_token(token)
        return AuthenticationInfo(
            token_permission=self._get_permissions(
                token,
                user_info['login'],
            ),
            user_id=user_info['email'],
            incoming_label='forgejo-' + user_info['login'],
        )
