"""Weekly email digest task — insights, stats, forgotten notes."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta

from celery import shared_task
from sqlalchemy import select

from app.core.config import settings
from app.db.models.user import User
from app.db.session import async_session_maker
from app.services.dashboard import DashboardService
from app.services.email import EmailService

logger = logging.getLogger(__name__)


def _build_digest_html(
    user_email: str, stats: dict, top_tags: list[dict],
    insights: dict, journal_streak: int,
) -> str:
    tag_html = "".join(
        f'<span style="display:inline-block;margin:2px 4px;padding:2px 8px;'
        f'border-radius:12px;background:#1a1a2e;color:#e0e0e0;font-size:12px">'
        f'{t["tag"]} ({t["count"]})</span>'
        for t in top_tags[:8]
    ) if top_tags else "<p>No tags this week.</p>"

    insight_html = ""
    for itype, count in insights.items():
        insight_html += (
            f'<tr><td style="padding:6px 12px;text-transform:capitalize">{itype}</td>'
            f'<td style="padding:6px 12px;text-align:right">{count}</td></tr>'
        )
    if not insight_html:
        insight_html = "<tr><td colspan='2'>No new insights this week.</td></tr>"

    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"></head>
<body style="font-family:-apple-system,BlinkMacSystemFont,sans-serif;max-width:560px;margin:0 auto;padding:24px;color:#e0e0e0;background:#0e0e0c">
<h1 style="font-size:22px;margin-bottom:4px">Your Weekly Digest</h1>
<p style="color:#888;font-size:13px;margin-top:0">{datetime.now(UTC).strftime('%B %d, %Y')}</p>

<div style="background:#1a1a2e;border-radius:12px;padding:20px;margin:20px 0">
  <h2 style="font-size:15px;margin:0 0 12px">Stats</h2>
  <table style="width:100%;border-collapse:collapse;font-size:14px">
    <tr><td style="padding:6px 0">Notes this week</td><td style="text-align:right;font-weight:600">{stats.get('total_notes', 0)}</td></tr>
    <tr><td style="padding:6px 0">Links</td><td style="text-align:right;font-weight:600">{stats.get('total_links', 0)}</td></tr>
    <tr><td style="padding:6px 0">Unread insights</td><td style="text-align:right;font-weight:600">{stats.get('unread_insights', 0)}</td></tr>
    <tr><td style="padding:6px 0">Journal streak</td><td style="text-align:right;font-weight:600">{journal_streak} days</td></tr>
  </table>
</div>

<div style="background:#1a1a2e;border-radius:12px;padding:20px;margin:20px 0">
  <h2 style="font-size:15px;margin:0 0 12px">Top Tags</h2>
  {tag_html}
</div>

<div style="background:#1a1a2e;border-radius:12px;padding:20px;margin:20px 0">
  <h2 style="font-size:15px;margin:0 0 12px">Pending Insights</h2>
  <table style="width:100%;border-collapse:collapse;font-size:14px">
    {insight_html}
  </table>
</div>

<p style="color:#555;font-size:11px;margin-top:24px">
  Sent by My AI Agent. <a href="{settings.FRONTEND_URL}/settings/notifications" style="color:#888">Manage notifications</a>.
</p>
</body></html>"""


@shared_task(
    name="digest.send_weekly_digest",
    max_retries=2, soft_time_limit=600, time_limit=720,
)
def send_weekly_digest() -> str:
    """Send weekly digest to all users with email_digest enabled."""
    async def _run() -> None:
        email_service = EmailService()
        async with async_session_maker() as db:
            result = await db.execute(
                select(User).where(
                    User.is_active.is_(True),
                    User.email_digest_enabled.is_(True),
                ))
            users = result.scalars().all()

            for user in users:
                try:
                    dashboard = DashboardService(db)
                    data = await dashboard.get_dashboard(user.id)
                    html = _build_digest_html(
                        user.email, data["stats"], data["top_tags"],
                        data["insights_summary"],
                        data["stats"]["journal_streak"],
                    )
                    ok = await email_service.send(
                        to=user.email,
                        subject="Your Weekly Second Brain Digest",
                        html_body=html,
                    )
                    if ok:
                        logger.info("Digest sent to %s", user.email)
                except Exception:
                    logger.exception("Digest failed for %s", user.email)

    asyncio.run(_run())
    return "ok"
