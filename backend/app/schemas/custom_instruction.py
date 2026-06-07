"""Custom instruction Pydantic schemas."""

from uuid import UUID

from pydantic import Field

from app.schemas.base import BaseSchema, TimestampSchema


class InstructionBase(BaseSchema):
    """Shared fields for custom instruction."""

    name: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1, max_length=5000)


class InstructionCreate(InstructionBase):
    """Schema for creating a new custom instruction."""

    is_active: bool = Field(default=False)


class InstructionUpdate(BaseSchema):
    """Schema for updating a custom instruction. All fields optional."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = Field(default=None, min_length=1, max_length=5000)
    is_active: bool | None = None


class InstructionRead(InstructionBase, TimestampSchema):
    """Schema for reading a custom instruction."""

    id: UUID
    user_id: UUID
    is_active: bool


class InstructionList(BaseSchema):
    """Paginated list of custom instructions."""

    items: list[InstructionRead]
    total: int
