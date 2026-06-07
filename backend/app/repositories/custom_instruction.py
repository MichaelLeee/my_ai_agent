"""Custom instruction repository — pure data access functions."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.db.models.custom_instruction import CustomInstruction


async def list_for_user(
    db: AsyncSession, *, user_id: UUID, skip: int = 0, limit: int = 50
) -> tuple[list[CustomInstruction], int]:
    """List all instructions for a user with pagination."""
    total = (await db.execute(
        select(func.count()).select_from(CustomInstruction).where(
            CustomInstruction.user_id == user_id
        )
    )).scalar_one()

    result = await db.execute(
        select(CustomInstruction)
        .where(CustomInstruction.user_id == user_id)
        .order_by(CustomInstruction.updated_at.desc().nulls_last(), CustomInstruction.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    return list(result.scalars().all()), total


async def get_by_id(db: AsyncSession, *, instruction_id: UUID) -> CustomInstruction | None:
    """Get a single instruction by ID."""
    result = await db.execute(
        select(CustomInstruction).where(CustomInstruction.id == instruction_id)
    )
    return result.scalar_one_or_none()


async def get_active_for_user(
    db: AsyncSession, *, user_id: UUID
) -> list[CustomInstruction]:
    """Get all active instructions for a user."""
    result = await db.execute(
        select(CustomInstruction)
        .where(CustomInstruction.user_id == user_id, CustomInstruction.is_active.is_(True))
        .order_by(CustomInstruction.created_at.asc())
    )
    return list(result.scalars().all())


async def create(
    db: AsyncSession, *, user_id: UUID, name: str, content: str, is_active: bool = False
) -> CustomInstruction:
    """Create a new custom instruction."""
    instruction = CustomInstruction(
        user_id=user_id, name=name, content=content, is_active=is_active
    )
    db.add(instruction)
    await db.flush()
    await db.refresh(instruction)
    return instruction


async def update(
    db: AsyncSession, *, db_instruction: CustomInstruction, update_data: dict
) -> CustomInstruction:
    """Update an existing instruction."""
    for field, value in update_data.items():
        setattr(db_instruction, field, value)
    await db.flush()
    await db.refresh(db_instruction)
    return db_instruction


async def delete_instruction(db: AsyncSession, *, db_instruction: CustomInstruction) -> None:
    """Delete an instruction."""
    await db.delete(db_instruction)
    await db.flush()


async def deactivate_others(
    db: AsyncSession, *, user_id: UUID, exclude_id: UUID
) -> None:
    """Deactivate all other active instructions for the user."""
    from sqlalchemy import update

    await db.execute(
        update(CustomInstruction)
        .where(
            CustomInstruction.user_id == user_id,
            CustomInstruction.is_active.is_(True),
            CustomInstruction.id != exclude_id,
        )
        .values(is_active=False)
    )
    await db.flush()
