"""Weekly summary task — generates a summary of the week's notes."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from celery import shared_task
from sqlalchemy import select

from app.db.models.user import User
from app.db.session import async_session_maker
from app.repositories import note as note_repo

logger = logging.getLogger(__name__)


def _build_summary(username: str, notes: list) -> str:
    """Build a text summary from a week's notes."""
    if not notes:
        return f"No notes recorded for {username} this week."

    topics = set()
    for n in notes:
        if n.tags:
            topics.update(n.tags)

    lines = [
        f"Weekly Summary for {username}",
        "",
        f"You wrote {len(notes)} notes this week across "
        f"{len(topics)} topics: {', '.join(sorted(topics)) if topics else 'general'}.",
        "",
        "Notes this week:",
    ]
    for n in notes:
        lines.append(f"- **{n.title}**: {n.content[:150]}{'...' if len(n.content) > 150 else ''}")
    return "\n".join(lines)


@shared_task(
    name="weekly_summary.generate_weekly_summary",
    max_retries=1,
    soft_time_limit=600,
    time_limit=720,
)
def generate_weekly_summary() -> str:
    """Generate weekly summaries for all users.

    Runs as a scheduled beat task (default: Sunday 9 AM).
    Queries the past 7 days of notes per user and creates a summary note.
    """
    async def _run() -> None:
        week_ago = datetime.now(UTC) - timedelta(days=7)
        today = datetime.now(UTC).date()
        title = f"Week of {today.strftime('%B %d, %Y')}"

        async with async_session_maker() as db:
            result = await db.execute(select(User).where(User.is_active.is_(True)))
            users = result.scalars().all()

            for user in users:
                items, _ = await note_repo.list_for_user(
                    db, user_id=user.id, skip=0, limit=200)

                week_notes = [
                    n for n in items
                    if n.created_at.replace(tzinfo=UTC) >= week_ago
                    and "summary" not in (n.tags or [])
                    and "journal" not in (n.tags or [])
                ]

                summary_text = _build_summary(
                    user.full_name or user.email, week_notes)

                from app.repositories.note import create
                await create(
                    db, user_id=user.id, title=title,
                    content=summary_text,
                    tags=["summary", "weekly", "auto"])

                logger.info(
                    "Weekly summary generated for %s (%d notes)",
                    user.email, len(week_notes))

    asyncio.run(_run())
    return "ok"
