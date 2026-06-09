"""Note Pydantic schemas for the Second Brain."""

from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema


class NoteBase(BaseSchema):
    title: str = Field(min_length=1, max_length=500)
    content: str = Field(min_length=1)
    tags: list[str] | None = Field(default=None)
    is_archived: bool = Field(default=False)


class NoteCreate(NoteBase):
    pass


class NoteUpdate(BaseSchema):
    title: str | None = Field(default=None, min_length=1, max_length=500)
    content: str | None = Field(default=None, min_length=1)
    tags: list[str] | None = None
    is_archived: bool | None = None


class NoteRead(NoteBase, TimestampSchema):
    id: UUID
    user_id: UUID
    document_id: str | None = None


class NoteList(BaseSchema):
    items: list[NoteRead]
    total: int
