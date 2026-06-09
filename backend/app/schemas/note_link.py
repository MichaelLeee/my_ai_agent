"""Note link Pydantic schemas."""

from uuid import UUID

from app.schemas.base import BaseSchema, TimestampSchema


class NoteLinkCreate(BaseSchema):
    source_note_id: UUID
    target_note_id: UUID
    link_type: str = "relates_to"


class NoteLinkRead(TimestampSchema):
    id: UUID
    source_note_id: UUID
    target_note_id: UUID
    link_type: str
