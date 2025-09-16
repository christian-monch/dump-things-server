"""Token-based authentication handlers

The authentication handlers are used to authenticate a token and to
determine:

- the permissions associated with the token
- the user id associated with the token
- the incoming_label to be used with the token

"""
from __future__ import annotations

import abc
import dataclasses
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dump_things_service.token import TokenPermission


class AuthenticationError(Exception):
    """Exception for dumpthings authentication errors."""


class InvalidTokenError(AuthenticationError):
    """Exception for invalid token errors."""


@dataclasses.dataclass
class AuthenticationInfo:
    token_permission: TokenPermission
    user_id: str
    incoming_label: str | None


class AuthenticationSource(metaclass=abc.ABCMeta):
    @abc.abstractmethod
    def authenticate(
        self,
        token: str,
    ) -> AuthenticationInfo:
        """
        Authenticate a user based on the provided token and collection.

        :param token: The authentication token.
        :return: AuthenticationInfo
        :raises AuthenticationError: If authentication fails.
        """
        raise NotImplementedError
