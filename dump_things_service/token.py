import hashlib

from pydantic import BaseModel


class TokenPermission(BaseModel):
    curated_read: bool = False
    incoming_read: bool = False
    incoming_write: bool = False
    curated_write: bool = False
    zones_access: bool = False


def get_token_parts(token: str) -> list[str]:
    parts = token.split('-', 1)
    if len(parts) != 2:
        msg = 'Invalid token format'
        raise ValueError(msg)
    return parts


def hash_token(token: str) -> str:
    parts = get_token_parts(token)
    hasher = hashlib.sha256()
    hasher.update(parts[1].encode())
    return f'{parts[0]}-{hasher.hexdigest()}'
