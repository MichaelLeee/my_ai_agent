"""Insight database model — agent-generated observations about the user's notes."""

import uuid

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class Insight(Base, TimestampMixin):
    """An agent-generated insight about the user's Second Brain.

    Types:
      - connection: semantically similar notes that should be linked
      - pattern: recurring topic/theme across multiple notes
      - contradiction: a note that appears to contradict an earlier one
      - suggestion: an action the user might want to take
      - summary: a daily/weekly briefing
    """

    __tablename__ = "insights"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    type: Mapped[str] = mapped_column(
        String(20), nullable=False,
    )
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    related_note_ids: Mapped[list | None] = mapped_column(JSONB, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_dismissed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="insights")

    def __repr__(self) -> str:
        return f"<Insight(id={self.id}, type={self.type!r}, title={self.title!r})>"
