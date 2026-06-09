"""Note link database model — bi-directional note connections."""

import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin


class NoteLink(Base, TimestampMixin):
    """A link between two notes in the Second Brain."""

    __tablename__ = "note_links"
    __table_args__ = (
        UniqueConstraint(
            "source_note_id", "target_note_id",
            name="uq_note_link_source_target"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("notes.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    target_note_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("notes.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    link_type: Mapped[str] = mapped_column(
        String(20), nullable=False, default="relates_to",
    )

    source_note: Mapped["Note"] = relationship(
        "Note", foreign_keys=[source_note_id], back_populates="source_links")
    target_note: Mapped["Note"] = relationship(
        "Note", foreign_keys=[target_note_id], back_populates="target_links")

    def __repr__(self) -> str:
        return f"<NoteLink({self.source_note_id} → {self.target_note_id})>"
