"""SMTP email sender — wraps smtplib with asyncio."""

import asyncio
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.core.config import settings

logger = logging.getLogger(__name__)


class EmailService:
    """Simple SMTP email sender. Wraps synchronous smtplib via asyncio.to_thread."""

    def __init__(self):
        self.host = settings.SMTP_HOST
        self.port = settings.SMTP_PORT
        self.user = settings.SMTP_USER or ""
        self.password = settings.SMTP_PASSWORD or ""
        self.from_addr = settings.SMTP_FROM or "noreply@myaiagent.local"

    async def send(self, *, to: str, subject: str, html_body: str) -> bool:
        """Send an HTML email. Returns True on success, False on failure."""
        msg = MIMEMultipart("alternative")
        msg["From"] = self.from_addr
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(MIMEText(html_body, "html", "utf-8"))

        def _send_sync():
            if settings.ENVIRONMENT == "local":
                # In local dev with Mailpit/Mailhog, use no-auth
                with smtplib.SMTP(self.host, self.port) as server:
                    server.sendmail(self.from_addr, [to], msg.as_string())
            else:
                # Production: TLS + auth
                with smtplib.SMTP(self.host, self.port) as server:
                    server.starttls()
                    if self.user and self.password:
                        server.login(self.user, self.password)
                    server.sendmail(self.from_addr, [to], msg.as_string())

        try:
            await asyncio.to_thread(_send_sync)
            logger.info("Email sent to %s: %s", to, subject)
            return True
        except Exception:
            logger.exception("Failed to send email to %s", to)
            return False
