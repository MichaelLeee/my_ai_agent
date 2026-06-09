"""Surface tools — forgotten notes, tag suggestions, smart suggestions."""

import re
from uuid import UUID

from pydantic_ai import RunContext

from app.agents.deps import Deps
from app.db.session import async_session_maker
from app.repositories import insight as insight_repo
from app.repositories import note as note_repo


async def forgotten_notes(ctx: RunContext[Deps]) -> str:
    """Surface notes the user hasn't visited in 90+ days.

    Call this once per conversation to check for forgotten notes. If any
    are found, mention one naturally and ask if the user wants to review
    more.
    """
    user_id = ctx.deps.user_id
    if not user_id:
        return ""

    uid = UUID(user_id)
    async with async_session_maker() as db:
        unread = await insight_repo.get_unread_by_type(
            db, user_id=uid, type="surface")

    if not unread:
        return ""

    top = unread[0]
    await insight_repo.mark_read(async_session_maker(), insight_id=top.id)

    lines = ["Here's something you might have forgotten:\n"]
    lines.append(f"**{top.title}**")
    if top.content:
        lines.append(top.content[:300])

    if len(unread) > 1:
        lines.append(f"\nYou have {len(unread) - 1} more forgotten notes. "
                     "Want to see them?")

    return "\n".join(lines)


async def suggest_tags(
    ctx: RunContext[Deps], title: str, content: str,
) -> str:
    """Suggest tags for a note based on the user's existing tag vocabulary.

    Use this before creating a note or when the user asks for tag ideas.
    Matches words in the title and content against tags the user has used
    before, ordered by frequency.

    Args:
        title: The note title.
        content: The note content.

    Returns:
        Comma-separated list of suggested tags, or a message if no matches.
    """
    user_id = ctx.deps.user_id
    if not user_id:
        return "Error: not authenticated."

    uid = UUID(user_id)
    async with async_session_maker() as db:
        user_tags = await note_repo.get_user_tags(db, user_id=uid)

    if not user_tags:
        return ("No existing tags found. Start tagging your notes and "
                "suggestions will improve over time.")

    # Tokenize: lowercase alphanumeric words, min 3 chars
    text = f"{title} {content}".lower()
    words = set(re.findall(r"[a-z0-9]{3,}", text))

    # Match words against user's tag vocabulary
    scored: list[tuple[str, int]] = []
    for tag, freq in user_tags:
        tag_lower = tag.lower()
        score = 0
        # Direct tag match
        if tag_lower in text:
            score = freq * 2
        else:
            # Partial word matches
            for word in words:
                if word in tag_lower or tag_lower in word:
                    score += freq
        if score > 0:
            scored.append((tag, score))

    scored.sort(key=lambda x: x[1], reverse=True)

    if not scored:
        return "No matching tags found in your vocabulary."

    top = [tag for tag, _ in scored[:5]]
    return "Suggested tags: " + ", ".join(top)


async def smart_suggestions(ctx: RunContext[Deps]) -> str:
    """Get actionable suggestions based on note patterns.

    Call this once per conversation. If suggestions exist, present the
    most relevant one and ask if the user wants to hear more.
    """
    user_id = ctx.deps.user_id
    if not user_id:
        return ""

    uid = UUID(user_id)
    async with async_session_maker() as db:
        unread = await insight_repo.get_unread_by_type(
            db, user_id=uid, type="suggestion")

    if not unread:
        return ""

    top = unread[0]
    await insight_repo.mark_read(async_session_maker(), insight_id=top.id)

    lines = ["Here's a suggestion based on your activity:\n"]
    lines.append(f"**{top.title}**")
    if top.content:
        lines.append(top.content[:300])

    if len(unread) > 1:
        lines.append(f"\nYou have {len(unread) - 1} more suggestions. "
                     "Want to hear them?")

    return "\n".join(lines)
