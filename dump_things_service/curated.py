from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from dump_things_service.api_key import api_key_header_scheme
router = APIRouter()


@router.get('/{collection}/curated/record/{class_name}')
async def read_curated_records_of_type(
        collection: str,
        class_name: str,
        matching: str | None = None,
        api_key: str = Depends(api_key_header_scheme),
):
    _check_collection
