"""Morning briefing agent tool — surfaces proactive insights to the user."""

from uuid import UUID

from pydantic_ai import RunContext

from app.agents.deps import Deps
from app.db.session import async_session_maker
from app.repositories import insight as insight_repo
from app.repositories import note as note_repo


async def morning_briefing(ctx: RunContext[Deps]) -> str:
    """Get the user's unread insights and morning briefing.

    Call this at the start of every conversation. If there are unread
    insights, surface them naturally. Don't read them all at once —
    mention the top one and ask if the user wants to hear more.
    """
    user_id = ctx.deps.user_id
    if not user_id:
        return ""

    uid = UUID(user_id)
    async with async_session_maker() as db:
        unread = await insight_repo.get_unread(db, user_id=uid)

    if not unread:
        return ""

    top = unread[0]
    await insight_repo.mark_read(async_session_maker(), insight_id=top.id)

    lines = [f"I noticed something while you were away:\n"]
    lines.append(f"**{top.title}**")
    if top.content:
        lines.append(top.content[:300])

    if len(unread) > 1:
        lines.append(f"\nYou have {len(unread) - 1} more insights. "
                     "Want to hear them?")

    return "\n".join(lines)


async def auto_link_tool(
    ctx: RunContext[Deps], insight_id: str, action: str = "link",
) -> str:
    """Accept or reject a suggested link between notes.

    Args:
        insight_id: The insight ID containing the link suggestion.
        action: "link" to create the link, "dismiss" to ignore.

    Returns:
        Confirmation message.
    """
    user_id = ctx.deps.user_id
    if not user_id:
        return "Error: not authenticated."

    uid = UUID(user_id)
    iid = UUID(insight_id)

    async with async_session_maker() as db:
        insights, _ = await insight_repo.list_for_user(
            db, user_id=uid, skip=0, limit=50)
        insight = next((i for i in insights if i.id == iid), None)
        if not insight:
            return "Insight not found."

        if action == "link" and insight.related_note_ids and \
           len(insight.related_note_ids) >= 2:
            nid1, nid2 = insight.related_note_ids[:2]
            from app.repositories.note import create_link
            try:
                await create_link(
                    db, source_note_id=UUID(nid1), target_note_id=UUID(nid2))
                await insight_repo.dismiss(db, insight_id=iid)
                return "Notes linked successfully."
            except Exception:
                return "These notes are already linked."

        await insight_repo.dismiss(db, insight_id=iid)
        return "Insight dismissed."
