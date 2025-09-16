from pydantic import BaseModel


class TokenPermission(BaseModel):
    curated_read: bool = False
    incoming_read: bool = False
    incoming_write: bool = False
