"""Handlers for invoice.* webhook events."""

import logging

import stripe
from sqlalchemy.ext.asyncio import AsyncSession

import app.repositories.subscription as sub_repo

logger = logging.getLogger(__name__)


def _format_amount(invoice) -> str:
    amount = (invoice.amount_paid or invoice.amount_due or 0) / 100
    currency = (invoice.currency or "usd").upper()
    return f"{currency} {amount:.2f}"


async def _send_payment_succeeded_email(invoice) -> None:
    pass


async def _send_payment_failed_email(invoice) -> None:
    pass


async def handle_payment_succeeded(db: AsyncSession, event: stripe.Event) -> None:
    invoice = event.data.object
    if invoice.billing_reason not in (
        "subscription_create",
        "subscription_cycle",
        "subscription_update",
    ):
        return

    sub = await sub_repo.get_by_stripe_id(db, invoice.subscription)
    if not sub:
        logger.warning(
            "invoice_sub_not_found",
            extra={"subscription_id": invoice.subscription},
        )
        return
    # Note: monthly credit grants are handled by customer.subscription.updated
    # (period rollover) and customer.subscription.created (first activation).
    # We don't grant here to avoid double-crediting on renewal.

    await _send_payment_succeeded_email(invoice)


async def handle_payment_failed(db: AsyncSession, event: stripe.Event) -> None:
    invoice = event.data.object
    logger.warning(
        "invoice_payment_failed",
        extra={"invoice_id": invoice.id, "subscription_id": invoice.subscription},
    )
    await _send_payment_failed_email(invoice)


async def handle_upcoming(db: AsyncSession, event: stripe.Event) -> None:
    invoice = event.data.object
    logger.info(
        "invoice_upcoming",
        extra={"invoice_id": invoice.id, "subscription_id": invoice.subscription},
    )
