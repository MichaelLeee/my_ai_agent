"""Agent memory tools — remember, recall, forget."""

from uuid import UUID

from pydantic_ai import RunContext

from app.agents.deps import Deps
from app.core.config import settings
from app.db.session import async_session_maker
from app.repositories import agent_memory as memory_repo


_embedding_service = None


def _get_embedder():
    global _embedding_service
    if _embedding_service is None:
        from app.services.rag.embeddings import EmbeddingService
        _embedding_service = EmbeddingService(settings=settings.rag)
    return _embedding_service


async def remember(
    ctx: RunContext[Deps], key: str, value: str, importance: int = 3,
) -> str:
    """Store a fact about the user in persistent memory.

    Use this whenever you learn something important about the user —
    preferences, projects they're working on, decisions they've made,
    tools they use, people they work with, goals they mention.

    Args:
        key: Short label for the memory (e.g. "preferred_language", "current_project").
        value: The fact to remember.
        importance: 1 (trivial) to 5 (critical). Default 3.

    Returns:
        Confirmation.
    """
    user_id = ctx.deps.user_id
    if not user_id:
        return "Error: not authenticated."

    uid = UUID(user_id)
    async with async_session_maker() as db:
        memory = await memory_repo.upsert(
            db, user_id=uid, key=key, value=value,
            importance=max(1, min(5, importance)),
            source="conversation")

        # Embed the memory for semantic recall
        try:
            embedder = _get_embedder()
            embedding = await embedder.embed_query(f"{key}: {value}")
            await memory_repo.store_embedding(
                db, memory_id=memory.id, embedding=embedding)
        except Exception:
            pass  # Embedding is best-effort

    return f"Remembered: {key}"


async def recall(ctx: RunContext[Deps], query: str) -> str:
    """Search your persistent memory for relevant facts about the user.

    Use this at the start of conversations or when the user asks about
    something you should remember. Returns the top matching memories.

    Args:
        query: What to search for (e.g. "programming languages",
               "current projects", "user preferences").

    Returns:
        Formatted list of matching memories or a message if none found.
    """
    user_id = ctx.deps.user_id
    if not user_id:
        return "Error: not authenticated."

    uid = UUID(user_id)
    embedder = _get_embedder()
    embedding = await embedder.embed_query(query)

    async with async_session_maker() as db:
        results = await memory_repo.search_by_embedding(
            db, user_id=uid, embedding=embedding)

    if not results:
        return "No relevant memories found."

    lines = [f"Memories about '{query}':"]
    for memory, score in results[:5]:
        lines.append(f"- {memory.key}: {memory.value} (relevance: {score:.2f})")
        await memory_repo.record_access(async_session_maker(), memory_id=memory.id)

    return "\n".join(lines)


async def forget(ctx: RunContext[Deps], key: str) -> str:
    """Delete a memory by its key.

    Use when the user asks to forget something, or when a stored fact
    is no longer accurate.

    Args:
        key: The memory key to delete.

    Returns:
        Confirmation or not-found message.
    """
    user_id = ctx.deps.user_id
    if not user_id:
        return "Error: not authenticated."

    uid = UUID(user_id)
    async with async_session_maker() as db:
        deleted = await memory_repo.delete_by_key(db, user_id=uid, key=key)

    return f"Forgot: {key}" if deleted else f"No memory found with key: {key}"
