from __future__ import annotations

from fastapi import HTTPException

from dump_things_service import (
    HTTP_403_FORBIDDEN,
    HTTP_404_NOT_FOUND,
)
from dump_things_service.config import (
    TokenPermission,
    InstanceConfig,
    get_default_token_name,
    get_token_store,
    join_default_token_permissions,
)
from dump_things_service.backends.record_dir import RecordDirStore


def check_collection(
    instance_config: InstanceConfig,
    collection: str,
):
    if collection not in instance_config.collections:
        raise HTTPException(
            status_code=HTTP_404_NOT_FOUND,
            detail=f'No such collection: "{collection}".',
        )


def get_permissions(
    instance_config: InstanceConfig,
    api_key: str | None,
    collection: str,
) -> tuple[TokenPermission, RecordDirStore | None, str | None]:
    check_collection(instance_config, collection)

    token = get_default_token_name(instance_config, collection) if api_key is None else api_key
    token_store, token_permissions = get_token_store(instance_config, collection, token)

    final_permissions = join_default_token_permissions(instance_config, token_permissions, collection)
    if not final_permissions.incoming_read and not final_permissions.curated_read:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail=f'No read access to curated or incoming data in collection "{collection}".',
        )
    return final_permissions, token_store, token
