"""Workflow agent tools — read notes, chain operations."""

from uuid import UUID

from pydantic_ai import RunContext

from app.agents.deps import Deps
from app.db.session import async_session_maker
from app.repositories import note as note_repo


async def get_note(ctx: RunContext[Deps], identifier: str) -> str:
    """Read the full content of a specific note.

    Use when you need to read a note's complete content — search_notes only
    returns snippets. Call this after finding relevant notes via search_notes
    or list_notes.

    Args:
        identifier: The note ID (UUID format) or exact title.

    Returns:
        Full note content with metadata, or an error if not found.
    """
    user_id = ctx.deps.user_id
    if not user_id:
        return "Error: not authenticated."

    uid = UUID(user_id)
    async with async_session_maker() as db:
        # Try UUID first
        try:
            note_id = UUID(identifier)
            note = await note_repo.get_by_id(db, note_id=note_id)
            if note and str(note.user_id) == str(uid):
                return _format_note(note)
        except (ValueError, TypeError):
            pass

        # Fall back to title match
        items, total = await note_repo.list_for_user(
            db, user_id=uid, skip=0, limit=200)
        for note in items:
            if note.title.lower().strip() == identifier.lower().strip():
                return _format_note(note)

    return f"Note '{identifier}' not found."


def _format_note(note) -> str:
    tags_str = ", ".join(note.tags) if note.tags else "none"
    created = note.created_at.strftime("%Y-%m-%d %H:%M") if note.created_at else "unknown"
    return (
        f"**{note.title}**\n"
        f"Tags: {tags_str}\n"
        f"Created: {created}\n"
        f"---\n"
        f"{note.content}"
    )
