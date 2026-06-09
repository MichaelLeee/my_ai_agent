"""Daily Journal agent tool — prompts reflection, retrieves context."""

from datetime import UTC, datetime

from pydantic_ai import RunContext

from app.agents.deps import Deps
from app.db.session import async_session_maker
from app.repositories import note as note_repo


async def daily_journal(ctx: RunContext[Deps]) -> str:
    """Start or continue the daily journal.

    Call this at the beginning of every conversation to check if the user
    has journaled today. If they haven't, prompt them with context from
    their recent journal entries.

    Returns:
        A journal prompt or a summary of today's entry if already journaled.
    """
    user_id = ctx.deps.user_id
    if not user_id:
        return "Error: not authenticated."

    from uuid import UUID

    uid = UUID(user_id)
    today = datetime.now(UTC).date()

    async with async_session_maker() as db:
        items, _ = await note_repo.list_for_user(
            db, user_id=uid, skip=0, limit=100, tag="journal")
        today_entries = [n for n in items if n.created_at.date() == today]
        past_entries = [n for n in items if n.created_at.date() != today][:5]

    if today_entries:
        lines = ["You've already journaled today:\n"]
        for n in today_entries:
            lines.append(f"- **{n.title}**: {n.content[:200]}")
        return "\n".join(lines)

    if past_entries:
        topics = " | ".join(n.title for n in past_entries[:3])
        return (
            "The user hasn't journaled yet today. Recent journal topics: "
            f"{topics}. Ask what they worked on today or what's on their "
            "mind. Keep it conversational. When they respond, use "
            "create_note to save it with tags: ['journal']."
        )

    return (
        "The user hasn't journaled yet today and has no past entries. "
        "Ask a simple opening question like: 'What did you work on today?' "
        "or 'What's on your mind?' When they respond, use create_note "
        "to save it with tags: ['journal']."
    )
