"""Reflection loop tasks — auto-linking, pattern detection, morning briefing."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from celery import shared_task
from sqlalchemy import select

from app.db.models.user import User
from app.db.session import async_session_maker
from app.repositories import insight as insight_repo
from app.repositories import note as note_repo
from app.services.note import NoteService

logger = logging.getLogger(__name__)

AUTO_LINK_SIMILARITY = 0.7
CONTRADICTION_SIMILARITY = 0.65
PATTERN_MIN_NOTES = 3
FORGOTTEN_DAYS = 90
SUGGEST_SUMMARY_MIN_NOTES = 5
SUGGEST_ORGANIZE_MIN_NOTES = 10
SUGGEST_REVIEW_DECISIONS_MIN = 3


def _group_by_tag(notes: list) -> dict[str, list]:
    groups: dict[str, list] = {}
    for n in notes:
        if n.tags:
            for tag in n.tags:
                groups.setdefault(tag, []).append(n)
    return groups


CONTRADICTION_PHRASES = [
    "but actually", "on second thought", "i was wrong about",
    "the opposite", "this contradicts", "i no longer think",
    "changed my mind on", "that was wrong", "i take that back",
    "i was mistaken", "actually, that's not right", "i realize now",
]


def _has_contradiction_markers(text: str) -> bool:
    text_lower = text.lower()
    return any(p in text_lower for p in CONTRADICTION_PHRASES)


async def _detect_forgotten_notes(db, user_id, all_notes) -> None:
    """Surface notes older than FORGOTTEN_DAYS that have no links."""
    old_notes = await note_repo.get_old_unlinked_notes(
        db, user_id=user_id, days=FORGOTTEN_DAYS)

    for note in old_notes:
        links = await note_repo.list_links(db, note_id=note.id)
        if links:
            continue  # Already connected
        if note.tags and "journal" in note.tags:
            continue  # Skip journal entries — they're intentionally transient

        await insight_repo.create(
            db, user_id=user_id, type="surface",
            title=f"Forgotten: {note.title}",
            content="You haven't revisited or connected this note in "
            f"{FORGOTTEN_DAYS}+ days. Want to review it?",
            related_note_ids=[str(note.id)])


async def _detect_contradictions(db, user_id, recent_notes, service) -> None:
    """Check recent notes for contradiction markers and find opposing older notes."""
    for note in recent_notes:
        text = f"{note.title} {note.content}"
        if not _has_contradiction_markers(text):
            continue
        if not note.document_id:
            continue

        try:
            results = await service.search(
                user_id=user_id,
                query=note.title,
                limit=5)
            for r in results:
                rid = r.get("note_id")
                if not rid or rid == str(note.id):
                    continue
                if r.get("score", 0) < CONTRADICTION_SIMILARITY:
                    continue
                target = await note_repo.get_by_id(db, note_id=rid)
                if not target:
                    continue

                await insight_repo.create(
                    db, user_id=user_id, type="contradiction",
                    title=f"Possible contradiction: {note.title} vs {target.title}",
                    content=f"Your recent note '{note.title}' seems to "
                    f"contradict '{target.title}' from earlier. "
                    "Want to reconcile these?",
                    related_note_ids=[str(note.id), rid])
                break  # One contradiction per note is enough
        except Exception:
            pass


async def _generate_suggestions(db, user_id, recent_notes, all_notes) -> None:
    """Generate actionable suggestions based on note patterns."""
    now = datetime.now(UTC)

    # 1. Five or more notes on the same tag → suggest creating a summary
    groups = _group_by_tag(all_notes)
    for tag, tagged in groups.items():
        if tag == "journal":
            continue  # Don't suggest summarizing journals
        if len(tagged) >= SUGGEST_SUMMARY_MIN_NOTES:
            await insight_repo.create(
                db, user_id=user_id, type="suggestion",
                title=f"Summarize your {tag} notes?",
                content=f"You have {len(tagged)} notes tagged '{tag}'. "
                "Want me to create a summary pulling them together?",
                related_note_ids=[str(n.id) for n in tagged[:10]])

    # 2. Ten or more notes with zero links → suggest organizing
    unlinked = 0
    for n in all_notes:
        links = await note_repo.list_links(db, note_id=n.id)
        if not links:
            unlinked += 1
    if unlinked >= SUGGEST_ORGANIZE_MIN_NOTES:
        await insight_repo.create(
            db, user_id=user_id, type="suggestion",
            title=f"You have {unlinked} unconnected notes",
            content="Try linking related notes together — it builds your "
            "knowledge graph and makes everything more discoverable.",
            related_note_ids=[str(n.id) for n in all_notes[:5]])

    # 3. Three or more "decision"-tagged notes in 7 days → suggest review
    week_ago = now - timedelta(days=7)
    decisions = [
        n for n in recent_notes
        if n.tags and "decision" in n.tags
        and n.created_at.replace(tzinfo=UTC) >= week_ago
    ]
    if len(decisions) >= SUGGEST_REVIEW_DECISIONS_MIN:
        await insight_repo.create(
            db, user_id=user_id, type="suggestion",
            title=f"You made {len(decisions)} decisions this week",
            content="Want to review them together? Here they are: " +
            ", ".join(n.title for n in decisions),
            related_note_ids=[str(n.id) for n in decisions])

    # 4. Journal streak of 5+ consecutive days
    journal_dates: set[str] = set()
    for n in all_notes:
        if n.tags and "journal" in n.tags:
            journal_dates.add(
                n.created_at.replace(tzinfo=UTC).strftime("%Y-%m-%d"))
    sorted_dates = sorted(journal_dates)
    streak = 1
    max_streak = 1
    for i in range(1, len(sorted_dates)):
        prev = datetime.strptime(sorted_dates[i - 1], "%Y-%m-%d").date()
        curr = datetime.strptime(sorted_dates[i], "%Y-%m-%d").date()
        if (curr - prev).days == 1:
            streak += 1
            max_streak = max(max_streak, streak)
        else:
            streak = 1
    if max_streak >= 5:
        await insight_repo.create(
            db, user_id=user_id, type="suggestion",
            title=f"You've journaled {max_streak} days in a row!",
            content="Consistency is the foundation of a great Second Brain. "
            "Keep the streak going!",
            related_note_ids=None)


@shared_task(
    name="reflection.run_reflection_loop",
    max_retries=1, soft_time_limit=300, time_limit=360,
)
def run_reflection_loop() -> str:
    """Run reflection for all active users. No LLM — heuristics only.

    Auto-link: embed recent notes, semantic search for similar,
    create connection insights if similarity > threshold.

    Pattern detection: group by tag, flag topics with 3+ recent notes.
    """
    async def _run() -> None:
        async with async_session_maker() as db:
            result = await db.execute(select(User).where(User.is_active.is_(True)))
            users = result.scalars().all()

            for user in users:
                items, _ = await note_repo.list_for_user(
                    db, user_id=user.id, skip=0, limit=100)
                recent = [n for n in items if n.created_at.replace(tzinfo=UTC) >
                          datetime.now(UTC) - timedelta(hours=24)]

                if len(recent) < 2:
                    continue

                # ── Pattern detection ──────────────────────
                groups = _group_by_tag(recent)
                for tag, tagged_notes in groups.items():
                    if len(tagged_notes) >= PATTERN_MIN_NOTES:
                        titles = ", ".join(n.title for n in tagged_notes[:5])
                        await insight_repo.create(
                            db, user_id=user.id, type="pattern",
                            title=f"You've been writing about {tag}",
                            content=f"You created {len(tagged_notes)} notes tagged "
                            f"'{tag}' recently: {titles}. Want to dive deeper?",
                            related_note_ids=[str(n.id) for n in tagged_notes])

                # ── Entity extraction ─────────────────────
                for note in recent:
                    text = f"{note.title} {note.content}"
                    entities = []
                    if any(p in text.lower() for p in
                           ["i think", "i believe", "it seems", "my take",
                            "in my opinion", "probably", "i suspect"]):
                        entities.append("claim")
                    if any(p in text.lower() for p in
                           ["decided to", "we decided", "going with",
                            "settled on", "final decision", "chose to"]):
                        entities.append("decision")
                    if any(p in text.lower() for p in
                           ["should we", "what if", "how do i",
                            "wonder if", "not sure about", "question:"]):
                        entities.append("question")
                    if entities:
                        await insight_repo.create(
                            db, user_id=user.id,
                            type="entity", title=f"Detected: {'+'.join(entities)}",
                            content=f"Note '{note.title}' appears to contain a "
                            f"{'/'.join(entities)}. You might want to review it.",
                            related_note_ids=[str(note.id)])

                # ── Auto-link suggestions ─────────────────
                service = NoteService(db)
                for note in recent:
                    if not note.document_id:
                        continue
                    try:
                        results = await service.search(
                            user_id=user.id,
                            query=f"{note.title} {note.content[:200]}",
                            limit=5)
                        for r in results:
                            rid = r.get("note_id")
                            if not rid or rid == str(note.id):
                                continue
                            if r.get("score", 0) < AUTO_LINK_SIMILARITY:
                                continue
                            target = await note_repo.get_by_id(
                                db, note_id=rid)
                            if not target:
                                continue
                            # Check if already linked
                            existing = await note_repo.list_links(
                                db, note_id=note.id)
                            linked_ids = {
                                str(l.source_note_id) for l in existing
                            } | {str(l.target_note_id) for l in existing}
                            if rid in linked_ids:
                                continue
                            await insight_repo.create(
                                db, user_id=user.id, type="connection",
                                title=f"Are '{note.title}' and '{target.title}' related?",
                                content=f"These notes appear semantically similar "
                                f"(score: {r.get('score', 0):.2f}). Link them?",
                                related_note_ids=[str(note.id), rid])
                    except Exception:
                        pass

                # ── Forgotten note surface ─────────────────
                await _detect_forgotten_notes(db, user.id, items)

                # ── Contradiction detection ────────────────
                await _detect_contradictions(db, user.id, recent, service)

                # ── Smart suggestions ──────────────────────
                await _generate_suggestions(db, user.id, recent, items)

    asyncio.run(_run())
    return "ok"


@shared_task(
    name="reflection.generate_morning_briefing",
    max_retries=1, soft_time_limit=600, time_limit=720,
)
def generate_morning_briefing() -> str:
    """Generate a morning briefing for all active users.

    Collects unread insights, recent journal entries, and new notes,
    then writes a summary insight.
    """
    async def _run() -> None:
        async with async_session_maker() as db:
            result = await db.execute(select(User).where(User.is_active.is_(True)))
            users = result.scalars().all()

            for user in users:
                insights, _ = await insight_repo.list_for_user(
                    db, user_id=user.id, skip=0, limit=50)
                unread = [i for i in insights if not i.is_read]
                items, _ = await note_repo.list_for_user(
                    db, user_id=user.id, skip=0, limit=200)

                week_ago = datetime.now(UTC) - timedelta(days=7)
                recent_notes = [
                    n for n in items
                    if n.created_at.replace(tzinfo=UTC) >= week_ago
                    and "summary" not in (n.tags or [])
                ]

                journal_notes = [
                    n for n in recent_notes if n.tags and "journal" in n.tags
                ]

                briefing_parts = []
                if journal_notes:
                    briefing_parts.append(
                        f"You journaled {len(journal_notes)} times this week.")
                if len(recent_notes) > 0:
                    topics = set()
                    for n in recent_notes:
                        if n.tags:
                            topics.update(n.tags)
                    if topics:
                        briefing_parts.append(
                            f"Topics: {', '.join(sorted(topics))}")
                if unread:
                    briefing_parts.append(
                        f"You have {len(unread)} unread insights.")

                if not briefing_parts:
                    continue

                today = datetime.now(UTC).date()
                await insight_repo.create(
                    db, user_id=user.id, type="summary",
                    title=f"Morning Briefing — {today.strftime('%B %d')}",
                    content="\n\n".join(briefing_parts),
                    related_note_ids=[str(n.id) for n in recent_notes[:10]])

                logger.info(
                    "Morning briefing generated for %s", user.email)

    asyncio.run(_run())
    return "ok"
