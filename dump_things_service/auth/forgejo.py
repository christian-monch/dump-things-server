
import requests

from . import (
    AuthenticationSource,
    RemoteAuthenticationError,
)
from ..config import TokenPermission


class ForgejoAuthenticationSource(AuthenticationSource):
    def __init__(
        self,
        api_url: str
    ):
        self.api_url = api_url

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
        raise RemoteAuthenticationError(status=r.status_code, message=r.text)

    def _get_permissions(
            self,
            token: str,
            user: str,
            repo: str,
    ) -> TokenPermission:

        r = requests.get(
            url=f'{self.api_url}/repos/{user}/{repo}',
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
        raise RemoteAuthenticationError(status=r.status_code, message=r.text)

    def authenticate(
        self,
        token: str,
        collection: str,
    ) -> TokenPermission:
        return self._get_permissions(
            token,
            self._get_user_for_token(token)['login'],
            collection,
        )
