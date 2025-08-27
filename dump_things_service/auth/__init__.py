import abc

from dump_things_service.config import TokenPermission


class AuthenticationError(Exception):
    """Exception for dumpthings authentication errors."""
    pass


class RemoteAuthenticationError(AuthenticationError):
    """Exception for remote authentication errors."""
    def __init__(self, status: int, message: str):
        self.status = status
        self.message = message
        super().__init__(f'Authentication failed with status {status}: {message}')


class AuthenticationSource(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def authenticate(
        self,
        token: str,
        collection: str,
    ) -> TokenPermission:
        """
        Authenticate a user based on the provided token and collection.

        :param token: The authentication token.
        :param collection: The collection to authenticate against.
        :return: TokenPermissions
        """
        raise NotImplemented
