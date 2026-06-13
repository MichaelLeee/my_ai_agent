"""Per-user API key model for programmatic access."""

import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class ApiKey(Base, TimestampMixin):
    """A user-created API key for CLI, script, or integration access."""

    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True)
    name: Mapped[str] = mapped_column(
        String(100), nullable=False)
    key_prefix: Mapped[str] = mapped_column(
        String(12), nullable=False, index=True, unique=True)
    key_hash: Mapped[str] = mapped_column(
        Text, nullable=False)
    last_used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True)
    is_revoked: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="api_keys")

    def __repr__(self) -> str:
        return f"<ApiKey(id={self.id}, name={self.name!r}, revoked={self.is_revoked})>"
