"""Use configuration information to fetch token permissions, ids, and incomng_label """

from dump_things_service.auth import (
    AuthenticationError,
    AuthenticationInfo,
    AuthenticationSource,
    InvalidTokenError,
)
from dump_things_service.config import (
    InstanceConfig,
    TokenPermission,
)


missing = dict()


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

        token_store_info = self.instance_config.token_stores.get(token, missing)
        if token_store_info is missing:
            raise InvalidTokenError()

        # Get the permissions, user_id, and incoming_label for this token
        # and collection from the configuration.
        token_collection_info = token_store_info.get(self.collection, missing)
        if token_collection_info is missing:
            raise InvalidTokenError(f'Token not valid for collection {self.collection}')

        return AuthenticationInfo(
            token_permission=token_collection_info['permissions'],
            user_id=token_store_info['user_id'],
            incoming_label=(
                # An incoming label might not be defined in the configuration,
                # if the token has no incoming read or write access.
                self.instance_config.zones[self.collection][token]
                if token in self.instance_config.zones.get(self.collection, {})
                else None
            )
        )
