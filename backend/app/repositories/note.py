"""Note repository — pure data access functions."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.db.models.note import Note
from app.db.models.note_link import NoteLink


async def list_for_user(
    db: AsyncSession, *, user_id: UUID, skip: int = 0, limit: int = 50,
    tag: str | None = None,
) -> tuple[list[Note], int]:
    """List notes for a user, newest first."""
    base = select(Note).where(
        Note.user_id == user_id, Note.is_archived.is_(False))
    if tag:
        base = base.where(Note.tags.cast(str).ilike(f"%{tag}%"))

    total = (await db.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar_one()

    result = await db.execute(
        base.order_by(Note.updated_at.desc().nulls_last(), Note.created_at.desc())
        .offset(skip).limit(limit)
    )
    return list(result.scalars().all()), total


async def get_by_id(db: AsyncSession, *, note_id: UUID) -> Note | None:
    result = await db.execute(select(Note).where(Note.id == note_id))
    return result.scalar_one_or_none()


async def create(
    db: AsyncSession, *, user_id: UUID, title: str, content: str,
    tags: list[str] | None = None, is_archived: bool = False,
) -> Note:
    note = Note(user_id=user_id, title=title, content=content,
                tags=tags, is_archived=is_archived)
    db.add(note)
    await db.flush()
    await db.refresh(note)
    return note


async def update(
    db: AsyncSession, *, db_note: Note, update_data: dict,
) -> Note:
    for field, value in update_data.items():
        setattr(db_note, field, value)
    await db.flush()
    await db.refresh(db_note)
    return db_note


async def delete_note(db: AsyncSession, *, db_note: Note) -> None:
    await db.delete(db_note)
    await db.flush()


# ── Note Links ──────────────────────────────────────────────────

async def create_link(
    db: AsyncSession, *, source_note_id: UUID, target_note_id: UUID,
    link_type: str = "relates_to",
) -> NoteLink:
    link = NoteLink(source_note_id=source_note_id, target_note_id=target_note_id,
                    link_type=link_type)
    db.add(link)
    await db.flush()
    await db.refresh(link)
    return link


async def delete_link(
    db: AsyncSession, *, source_note_id: UUID, target_note_id: UUID,
) -> bool:
    from app.db.models.note_link import NoteLink
    result = await db.execute(
        select(NoteLink).where(
            NoteLink.source_note_id == source_note_id,
            NoteLink.target_note_id == target_note_id))
    link = result.scalar_one_or_none()
    if link:
        await db.delete(link)
        await db.flush()
        return True
    return False


async def list_links(
    db: AsyncSession, *, note_id: UUID,
) -> list[NoteLink]:
    result = await db.execute(
        select(NoteLink).where(
            (NoteLink.source_note_id == note_id) |
            (NoteLink.target_note_id == note_id)
        ).order_by(NoteLink.created_at.desc())
    )
    return list(result.scalars().all())


async def get_old_unlinked_notes(
    db: AsyncSession, *, user_id: UUID, days: int = 90, limit: int = 20,
) -> list[Note]:
    """Notes older than `days` that may be forgotten — not archived, fetched for link-check."""
    cutoff = func.now() - func.make_interval(days=days)
    result = await db.execute(
        select(Note).where(
            Note.user_id == user_id,
            Note.is_archived.is_(False),
            Note.created_at < cutoff,
        ).order_by(Note.created_at.asc()).limit(limit)
    )
    return list(result.scalars().all())


async def get_user_tags(
    db: AsyncSession, *, user_id: UUID,
) -> list[tuple[str, int]]:
    """All unique tags used by a user, ordered by frequency descending."""
    result = await db.execute(
        select(
            func.jsonb_array_elements_text(Note.tags).label("tag"),
            func.count().label("cnt"),
        ).where(
            Note.user_id == user_id,
            Note.tags.is_not(None),
        ).group_by("tag").order_by(func.count().desc()).limit(100)
    )
    return [(row.tag, row.cnt) for row in result.all()]
