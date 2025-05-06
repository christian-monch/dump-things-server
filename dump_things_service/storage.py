from __future__ import annotations

import enum
import hashlib
from functools import partial
from pathlib import Path
from typing import (
    Callable,
    Literal,
)

import yaml
from pydantic import BaseModel

config_file_name = '.dumpthings.yaml'
token_config_file_name = '.token_config.yaml'  # noqa: S105
ignored_files = {'.', '..', config_file_name}


class MappingMethod(enum.Enum):
    digest_md5 = 'digest-md5'
    digest_md5_p3 = 'digest-md5-p3'
    digest_sha1 = 'digest-sha1'
    digest_sha1_p3 = 'digest-sha1-p3'
    after_last_colon = 'after-last-colon'


class CollectionDirConfig(BaseModel):
    type: Literal['records']
    version: Literal[1]
    schema: str
    format: Literal['yaml']
    idfx: MappingMethod


class TokenPermission(BaseModel):
    curated_read: bool = False
    incoming_read: bool = False
    incoming_write: bool = False


class TokenModes(enum.Enum):
    READ_CURATED = 'READ_CURATED'
    READ_COLLECTION = 'READ_COLLECTION'
    WRITE_COLLECTION = 'WRITE_COLLECTION'
    READ_SUBMISSIONS = 'READ_SUBMISSIONS'
    WRITE_SUBMISSIONS = 'WRITE_SUBMISSIONS'
    SUBMIT = 'SUBMIT'
    SUBMIT_ONLY = 'SUBMIT_ONLY'
    NOTHING = 'NOTHING'


mode_mapping = {
    TokenModes.READ_CURATED: TokenPermission(curated_read=True),
    TokenModes.READ_COLLECTION: TokenPermission(curated_read=True, incoming_read=True),
    TokenModes.WRITE_COLLECTION: TokenPermission(
        curated_read=True, incoming_read=True, incoming_write=True
    ),
    TokenModes.READ_SUBMISSIONS: TokenPermission(incoming_read=True),
    TokenModes.WRITE_SUBMISSIONS: TokenPermission(
        incoming_read=True, incoming_write=True
    ),
    TokenModes.SUBMIT: TokenPermission(curated_read=True, incoming_write=True),
    TokenModes.SUBMIT_ONLY: TokenPermission(incoming_write=True),
    TokenModes.NOTHING: TokenPermission(),
}


class TokenCollectionConfig(BaseModel):
    mode: TokenModes
    incoming_label: str


class TokenConfig(BaseModel):
    user_id: str
    collections: dict[str, TokenCollectionConfig]


class CollectionConfig(BaseModel):
    curated: Path
    incoming: Path | None = None


class GlobalConfig(BaseModel):
    type: Literal['collections']
    version: Literal[1]
    collections: dict[str, CollectionConfig]
    tokens: dict[str, TokenConfig]


def get_hex_digest(hasher: Callable, data: str) -> str:
    hash_context = hasher(data.encode())
    return hash_context.hexdigest()


def mapping_digest_p3(
    hasher: Callable,
    pid: str,
    suffix: str,
) -> Path:
    hex_digest = get_hex_digest(hasher, pid)
    return Path(hex_digest[:3]) / (hex_digest[3:] + '.' + suffix)


def mapping_digest(hasher: Callable, pid: str, suffix: str) -> Path:
    hex_digest = get_hex_digest(hasher, pid)
    return Path(hex_digest + '.' + suffix)


def mapping_after_last_colon(pid: str, suffix: str) -> Path:
    plain_result = pid.split(':')[-1]
    # Escape any colons and slashes in the pid
    escaped_result = (
        plain_result.replace('_', '__').replace('/', '_s').replace('.', '_d')
    )
    return Path(escaped_result + '.' + suffix)


mapping_functions = {
    MappingMethod.digest_md5: partial(mapping_digest, hashlib.md5),
    MappingMethod.digest_md5_p3: partial(mapping_digest_p3, hashlib.md5),
    MappingMethod.digest_sha1: partial(mapping_digest, hashlib.sha1),
    MappingMethod.digest_sha1_p3: partial(mapping_digest_p3, hashlib.sha1),
    MappingMethod.after_last_colon: mapping_after_last_colon,
}


def get_mapping_function(collection_config: CollectionDirConfig):
    return mapping_functions[collection_config.idfx]


def get_permissions(mode: TokenModes) -> TokenPermission:
    return mode_mapping[mode]


class Storage:
    @staticmethod
    def get_config_from_file(path: Path) -> GlobalConfig:
        return GlobalConfig(**yaml.load(path.read_text(), Loader=yaml.SafeLoader))

    @staticmethod
    def get_config(path: Path, file_name=config_file_name) -> GlobalConfig:
        return Storage.get_config_from_file(path / file_name)

    @staticmethod
    def get_collection_dir_config(
        path: Path, file_name=config_file_name
    ) -> CollectionDirConfig:
        return CollectionDirConfig(
            **yaml.load((path / file_name).read_text(), Loader=yaml.SafeLoader)
        )
