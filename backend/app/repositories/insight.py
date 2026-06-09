"""Insight repository — pure data access functions."""

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.db.models.insight import Insight


async def create(
    db: AsyncSession, *, user_id: UUID, type: str, title: str, content: str,
    related_note_ids: list[str] | None = None,
) -> Insight:
    insight = Insight(
        user_id=user_id, type=type, title=title, content=content,
        related_note_ids=related_note_ids)
    db.add(insight)
    await db.flush()
    await db.refresh(insight)
    return insight


async def list_for_user(
    db: AsyncSession, *, user_id: UUID, skip: int = 0, limit: int = 50,
    include_dismissed: bool = False,
) -> tuple[list[Insight], int]:
    base = select(Insight).where(Insight.user_id == user_id)
    if not include_dismissed:
        base = base.where(Insight.is_dismissed.is_(False))

    total = (await db.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar_one()

    result = await db.execute(
        base.order_by(Insight.created_at.desc()).offset(skip).limit(limit))
    return list(result.scalars().all()), total


async def get_unread(db: AsyncSession, *, user_id: UUID) -> list[Insight]:
    result = await db.execute(
        select(Insight).where(
            Insight.user_id == user_id,
            Insight.is_read.is_(False),
            Insight.is_dismissed.is_(False),
        ).order_by(Insight.created_at.desc()).limit(10))
    return list(result.scalars().all())


async def mark_read(db: AsyncSession, *, insight_id: UUID) -> None:
    await db.execute(
        update(Insight).where(Insight.id == insight_id).values(is_read=True))
    await db.flush()


async def get_unread_by_type(db: AsyncSession, *, user_id: UUID, type: str) -> list[Insight]:
    result = await db.execute(
        select(Insight).where(
            Insight.user_id == user_id,
            Insight.type == type,
            Insight.is_read.is_(False),
            Insight.is_dismissed.is_(False),
        ).order_by(Insight.created_at.desc()).limit(10))
    return list(result.scalars().all())


async def dismiss(db: AsyncSession, *, insight_id: UUID) -> None:
    await db.execute(
        update(Insight).where(Insight.id == insight_id).values(is_dismissed=True))
    await db.flush()
