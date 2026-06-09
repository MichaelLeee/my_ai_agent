"""Contradiction tools — surface contradictory claims to the agent."""

from uuid import UUID

from pydantic_ai import RunContext

from app.agents.deps import Deps
from app.db.session import async_session_maker
from app.repositories import insight as insight_repo
from app.repositories import note as note_repo


async def contradictions(ctx: RunContext[Deps]) -> str:
    """Surface possible contradictions between recent notes and older ones.

    Call this once per conversation. If contradictions are found, present
    one naturally — "You said X last month, but this week you wrote Y.
    Want to reconcile these?"
    """
    user_id = ctx.deps.user_id
    if not user_id:
        return ""

    uid = UUID(user_id)
    async with async_session_maker() as db:
        unread = await insight_repo.get_unread_by_type(
            db, user_id=uid, type="contradiction")

    if not unread:
        return ""

    top = unread[0]
    await insight_repo.mark_read(async_session_maker(), insight_id=top.id)

    lines = ["I noticed something that might contradict what you wrote before:\n"]
    lines.append(f"**{top.title}**")
    if top.content:
        lines.append(top.content[:300])

    if len(unread) > 1:
        lines.append(f"\nYou have {len(unread) - 1} more contradictions. "
                     "Want to review them?")

    return "\n".join(lines)
