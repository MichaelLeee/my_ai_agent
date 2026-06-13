"""API key repository — CRUD + prefix lookup."""

from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.db.models.api_key import ApiKey


async def create(
    db: AsyncSession, *, user_id: UUID, name: str,
    key_prefix: str, key_hash: str,
) -> ApiKey:
    key = ApiKey(
        user_id=user_id, name=name, key_prefix=key_prefix, key_hash=key_hash)
    db.add(key)
    await db.flush()
    await db.refresh(key)
    return key


async def list_for_user(
    db: AsyncSession, *, user_id: UUID, skip: int = 0, limit: int = 50,
) -> tuple[list[ApiKey], int]:
    base = select(ApiKey).where(ApiKey.user_id == user_id)
    total = (await db.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar_one()
    result = await db.execute(
        base.order_by(ApiKey.created_at.desc()).offset(skip).limit(limit))
    return list(result.scalars().all()), total


async def get_by_prefix(
    db: AsyncSession, *, key_prefix: str,
) -> ApiKey | None:
    result = await db.execute(
        select(ApiKey).where(
            ApiKey.key_prefix == key_prefix,
            ApiKey.is_revoked.is_(False)))
    return result.scalar_one_or_none()


async def record_usage(db: AsyncSession, *, key_id: UUID) -> None:
    await db.execute(
        update(ApiKey).where(ApiKey.id == key_id).values(
            last_used_at=func.now()))
    await db.flush()


async def revoke(db: AsyncSession, *, key_id: UUID, user_id: UUID) -> bool:
    result = await db.execute(
        select(ApiKey).where(ApiKey.id == key_id, ApiKey.user_id == user_id))
    key = result.scalar_one_or_none()
    if not key:
        return False
    key.is_revoked = True
    await db.flush()
    return True
