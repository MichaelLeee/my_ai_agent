"""Agent memory repository — CRUD + semantic recall."""

import json
from uuid import UUID

from sqlalchemy import delete, select, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.db.models.agent_memory import AgentMemory


async def upsert(
    db: AsyncSession, *, user_id: UUID, key: str, value: str,
    importance: int = 3, source: str = "conversation",
) -> AgentMemory:
    """Create or update a memory by user_id + key."""
    existing = await db.execute(
        select(AgentMemory).where(
            AgentMemory.user_id == user_id, AgentMemory.key == key))
    memory = existing.scalar_one_or_none()

    if memory:
        memory.value = value
        memory.importance = importance
        memory.source = source
    else:
        memory = AgentMemory(
            user_id=user_id, key=key, value=value,
            importance=importance, source=source)
        db.add(memory)

    await db.flush()
    await db.refresh(memory)
    return memory


async def list_for_user(
    db: AsyncSession, *, user_id: UUID, skip: int = 0, limit: int = 50,
) -> tuple[list[AgentMemory], int]:
    base = select(AgentMemory).where(AgentMemory.user_id == user_id)
    total = (await db.execute(
        select(func.count()).select_from(base.subquery())
    )).scalar_one()
    result = await db.execute(
        base.order_by(AgentMemory.importance.desc(), AgentMemory.updated_at.desc())
        .offset(skip).limit(limit))
    return list(result.scalars().all()), total


async def delete_by_key(db: AsyncSession, *, user_id: UUID, key: str) -> bool:
    result = await db.execute(
        delete(AgentMemory).where(
            AgentMemory.user_id == user_id, AgentMemory.key == key))
    await db.flush()
    return result.rowcount > 0


async def record_access(db: AsyncSession, *, memory_id: UUID) -> None:
    await db.execute(
        update(AgentMemory).where(AgentMemory.id == memory_id).values(
            access_count=AgentMemory.access_count + 1,
            last_accessed_at=func.now()))
    await db.flush()


async def search_by_embedding(
    db: AsyncSession, *, user_id: UUID, embedding: list[float],
    limit: int = 5,
) -> list[AgentMemory]:
    """Semantic search over memories using pgvector cosine distance."""
    query = text("""
        SELECT id, key, value, source, importance, access_count,
               last_accessed_at, created_at, updated_at,
               1 - (embedding <=> :embedding) AS score
        FROM agent_memories
        WHERE user_id = :user_id
        ORDER BY embedding <=> :embedding
        LIMIT :limit
    """)
    result = await db.execute(
        query,
        {"user_id": user_id, "embedding": json.dumps(embedding), "limit": limit})
    rows = result.all()
    memories = []
    for row in rows:
        m = AgentMemory(
            id=row.id, user_id=user_id, key=row.key, value=row.value,
            source=row.source, importance=row.importance,
            access_count=row.access_count, last_accessed_at=row.last_accessed_at,
            created_at=row.created_at, updated_at=row.updated_at)
        memories.append((m, float(row.score)))
    return memories


async def store_embedding(
    db: AsyncSession, *, memory_id: UUID, embedding: list[float],
) -> None:
    await db.execute(
        text("UPDATE agent_memories SET embedding = :embedding WHERE id = :id"),
        {"id": memory_id, "embedding": json.dumps(embedding)})
    await db.flush()
