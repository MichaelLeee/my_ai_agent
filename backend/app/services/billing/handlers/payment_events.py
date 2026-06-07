"""Handlers for checkout.session.* and payment_intent.* events."""

import logging

import stripe
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


async def handle_checkout_completed(db: AsyncSession, event: stripe.Event) -> None:
    session = event.data.object
    if session.mode != "payment":
        # subscription mode — handled by customer.subscription.created
        return
    logger.info("checkout_completed_payment", extra={"session_id": session.id})


async def handle_payment_intent_succeeded(db: AsyncSession, event: stripe.Event) -> None:
    logger.info("payment_intent_succeeded", extra={"pi_id": event.data.object.id})


async def handle_payment_intent_failed(db: AsyncSession, event: stripe.Event) -> None:
    logger.warning("payment_intent_failed", extra={"pi_id": event.data.object.id})
