"""Insight Pydantic schemas."""

from uuid import UUID

from app.schemas.base import BaseSchema, TimestampSchema


class InsightRead(BaseSchema, TimestampSchema):
    id: UUID
    user_id: UUID
    type: str
    title: str
    content: str
    related_note_ids: list[str] | None = None
    is_read: bool
    is_dismissed: bool


class InsightList(BaseSchema):
    items: list[InsightRead]
    total: int
