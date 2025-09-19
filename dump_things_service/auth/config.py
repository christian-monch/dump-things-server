"""Use configuration information to fetch token permissions, ids, and incomng_label """

from dump_things_service.auth import (
    AuthenticationInfo,
    AuthenticationSource,
    InvalidTokenError,
)
from dump_things_service.config import (
    InstanceConfig,
)
from dump_things_service.token import (
    get_token_parts,
    hash_token,
)

missing = {}


class ConfigAuthenticationSource(AuthenticationSource):
    def __init__(
        self,
        instance_config: InstanceConfig,
        collection: str,
    ):
        self.instance_config = instance_config
        self.collection = collection

    def authenticate(
        self,
        token: str,
    ) -> AuthenticationInfo:

        token = self._resolve_hashed_token(token)
        token_info = self.instance_config.tokens.get(self.collection, {}).get(token, missing)
        if token_info is missing:
            msg = f'Token not valid for collection `{self.collection}`'
            raise InvalidTokenError(msg)

        return AuthenticationInfo(
            token_permission=token_info['permissions'],
            user_id=token_info['user_id'],
            incoming_label=token_info['incoming_label'],
        )

    def _resolve_hashed_token(
        self,
        token: str
    ) -> str:

        try:
            token_id, _ = get_token_parts(token)
            if token_id in self.instance_config.hashed_tokens[self.collection]:
                return hash_token(token)
        except ValueError:
            pass
        return token
