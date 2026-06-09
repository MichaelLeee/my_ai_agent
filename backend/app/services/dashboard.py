"""Dashboard aggregation service — stats, activity, insights."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from app.db.models.insight import Insight
from app.db.models.note import Note
from app.db.models.note_link import NoteLink
from app.repositories import insight as insight_repo
from app.repositories import note as note_repo


class DashboardService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_dashboard(self, user_id: UUID) -> dict:
        """Aggregate all dashboard data in one call."""
        stats = await self._get_stats(user_id)
        top_tags = await self._get_top_tags(user_id)
        recent = await self._get_recent_activity(user_id)
        insights_summary = await self._get_insights_summary(user_id)

        return {
            "stats": stats,
            "top_tags": top_tags,
            "recent_activity": recent,
            "insights_summary": insights_summary,
        }

    async def _get_stats(self, user_id: UUID) -> dict:
        # Total notes (non-archived)
        total_notes = await self.db.scalar(
            select(func.count()).where(
                Note.user_id == user_id, Note.is_archived.is_(False)))

        # Total links for user's notes
        total_links = await self.db.scalar(
            select(func.count()).where(
                NoteLink.source_note_id.in_(
                    select(Note.id).where(Note.user_id == user_id))))

        # Unread insights
        unread = await insight_repo.get_unread(self.db, user_id=user_id)
        unread_insights = len(unread)

        # Journal streak
        journal_streak = await self._get_journal_streak(user_id)

        # Journal entries this week
        week_ago = datetime.now(UTC) - timedelta(days=7)
        journal_this_week = await self.db.scalar(
            select(func.count()).where(
                Note.user_id == user_id,
                Note.tags.cast(str).ilike("%journal%"),
                Note.created_at >= week_ago))

        return {
            "total_notes": total_notes or 0,
            "total_links": total_links or 0,
            "unread_insights": unread_insights,
            "journal_streak": journal_streak,
            "journal_this_week": journal_this_week or 0,
        }

    async def _get_journal_streak(self, user_id: UUID) -> int:
        """Count consecutive days with a journal entry, counting back from today."""
        result = await self.db.execute(
            select(Note.created_at).where(
                Note.user_id == user_id,
                Note.tags.cast(str).ilike("%journal%"),
            ).order_by(Note.created_at.desc()).limit(365))
        dates = sorted({
            r.created_at.replace(tzinfo=UTC).strftime("%Y-%m-%d")
            for r in result.all()
        }, reverse=True)

        if not dates:
            return 0

        today = datetime.now(UTC).strftime("%Y-%m-%d")
        if dates[0] not in (today, self._yesterday_str()):
            return 0

        streak = 1
        for i in range(len(dates) - 1):
            d1 = datetime.strptime(dates[i], "%Y-%m-%d").date()
            d2 = datetime.strptime(dates[i + 1], "%Y-%m-%d").date()
            if (d1 - d2).days == 1:
                streak += 1
            else:
                break
        return streak

    def _yesterday_str(self) -> str:
        return (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")

    async def _get_top_tags(self, user_id: UUID) -> list[dict]:
        result = await self.db.execute(
            select(
                func.jsonb_array_elements_text(Note.tags).label("tag"),
                func.count().label("cnt"),
            ).where(
                Note.user_id == user_id,
                Note.tags.is_not(None),
            ).group_by("tag").order_by(func.count().desc()).limit(10))
        return [{"tag": row.tag, "count": row.cnt} for row in result.all()]

    async def _get_recent_activity(self, user_id: UUID) -> list[dict]:
        """Merged feed of recent notes, insights, and links."""
        activity = []

        # Recent notes
        notes_result = await self.db.execute(
            select(Note.id, Note.title, Note.created_at).where(
                Note.user_id == user_id, Note.is_archived.is_(False),
            ).order_by(Note.created_at.desc()).limit(5))
        for r in notes_result.all():
            activity.append({
                "type": "note",
                "id": str(r.id), "title": r.title,
                "timestamp": r.created_at.isoformat() if r.created_at else None,
            })

        # Recent insights
        insights_result = await self.db.execute(
            select(Insight.id, Insight.type, Insight.title, Insight.created_at).where(
                Insight.user_id == user_id, Insight.is_dismissed.is_(False),
            ).order_by(Insight.created_at.desc()).limit(5))
        for r in insights_result.all():
            activity.append({
                "type": "insight",
                "id": str(r.id), "title": r.title,
                "insight_type": r.type,
                "timestamp": r.created_at.isoformat() if r.created_at else None,
            })

        activity.sort(
            key=lambda a: a["timestamp"] or "",
            reverse=True)
        return activity[:10]

    async def _get_insights_summary(self, user_id: UUID) -> dict:
        result = await self.db.execute(
            select(Insight.type, func.count()).where(
                Insight.user_id == user_id,
                Insight.is_read.is_(False),
                Insight.is_dismissed.is_(False),
            ).group_by(Insight.type))
        return {row.type: row.count for row in result.all()}
