"""Custom instruction database model.

Users can create and activate system prompt overrides that the
agent picks up at runtime to customize its behavior.
"""

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class CustomInstruction(Base, TimestampMixin):
    """A user-defined system prompt override for the AI agent."""

    __tablename__ = "custom_instructions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(255), nullable=False
    )
    content: Mapped[str] = mapped_column(
        Text, nullable=False
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )

    user: Mapped["User"] = relationship("User", back_populates="custom_instructions")

    def __repr__(self) -> str:
        return (
            f"<CustomInstruction(id={self.id}, name={self.name!r}, "
            f"is_active={self.is_active})>"
        )
