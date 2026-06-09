"""AgentMemory Pydantic schemas."""

from datetime import datetime
from uuid import UUID

from app.schemas.base import BaseSchema, TimestampSchema


class MemoryCreate(BaseSchema):
    key: str
    value: str
    importance: int = 3
    source: str = "conversation"


class MemoryRead(BaseSchema, TimestampSchema):
    id: UUID
    user_id: UUID
    key: str
    value: str
    source: str
    importance: int
    access_count: int
    last_accessed_at: datetime | None = None


class MemoryList(BaseSchema):
    items: list[MemoryRead]
    total: int
