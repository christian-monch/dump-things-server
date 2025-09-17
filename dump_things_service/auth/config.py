"""Use configuration information to fetch token permissions, ids, and incomng_label """

from dump_things_service.auth import (
    AuthenticationInfo,
    AuthenticationSource,
    InvalidTokenError,
)
from dump_things_service.config import (
    InstanceConfig,
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

        token_info = self.instance_config.tokens.get(self.collection, {}).get(token, missing)
        if token_info is missing:
            msg = f'Token not valid for collection `{self.collection}`'
            raise InvalidTokenError(msg)

        return AuthenticationInfo(
            token_permission=token_info['permissions'],
            user_id=token_info['user_id'],
            incoming_label=token_info['incoming_label'],
        )
