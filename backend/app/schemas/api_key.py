"""ApiKey Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema


class ApiKeyCreate(BaseSchema):
    name: str = Field(max_length=100, description="Label for this key (e.g. 'CLI', 'Zapier')")


class ApiKeyRead(BaseSchema):
    """Returned once on creation — includes the plain key. Never stored."""
    id: UUID
    name: str
    key: str = Field(description="The full API key. Copy it now — it won't be shown again.")
    created_at: datetime


class ApiKeyListItem(BaseSchema, TimestampSchema):
    id: UUID
    name: str
    key_prefix: str
    last_used_at: datetime | None = None
    is_revoked: bool


class ApiKeyList(BaseSchema):
    items: list[ApiKeyListItem]
    total: int
