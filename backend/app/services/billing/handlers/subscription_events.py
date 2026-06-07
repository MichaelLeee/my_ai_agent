"""Handlers for customer.subscription.* webhook events."""

import logging
from datetime import UTC, datetime

import stripe
from sqlalchemy.ext.asyncio import AsyncSession

import app.repositories.organization as org_repo
import app.repositories.plan as plan_repo
import app.repositories.subscription as sub_repo
from app.db.models.subscription import Subscription, SubscriptionStatus

logger = logging.getLogger(__name__)


async def _sync_from_stripe(db: AsyncSession, stripe_sub: stripe.Subscription) -> Subscription:
    price_obj = stripe_sub["items"]["data"][0]["price"]
    price = await plan_repo.get_price_by_stripe_id(db, price_obj["id"])
    org = await org_repo.get_by_stripe_customer(db, stripe_sub.customer)

    if not org:
        logger.error(
            "subscription_org_not_found",
            extra={"customer_id": stripe_sub.customer},
        )
        raise ValueError(f"No org found for customer {stripe_sub.customer}")

    fields = {
        "stripe_subscription_id": stripe_sub.id,
        "stripe_customer_id": stripe_sub.customer,
        "stripe_item_id": stripe_sub["items"]["data"][0]["id"],
        "price_id": price.id if price else None,
        "organization_id": org.id,
        "seats_quantity": stripe_sub["items"]["data"][0].get("quantity", 1),
        "status": SubscriptionStatus(stripe_sub.status),
        "current_period_start": datetime.fromtimestamp(stripe_sub.current_period_start, UTC),
        "current_period_end": datetime.fromtimestamp(stripe_sub.current_period_end, UTC),
        "cancel_at_period_end": stripe_sub.cancel_at_period_end,
        "canceled_at": datetime.fromtimestamp(stripe_sub.canceled_at, UTC)
        if stripe_sub.canceled_at
        else None,
        "trial_start": datetime.fromtimestamp(stripe_sub.trial_start, UTC)
        if stripe_sub.trial_start
        else None,
        "trial_end": datetime.fromtimestamp(stripe_sub.trial_end, UTC)
        if stripe_sub.trial_end
        else None,
    }

    existing = await sub_repo.get_by_stripe_id(db, stripe_sub.id)
    if existing:
        return await sub_repo.update(db, db_sub=existing, **fields)

    return await sub_repo.create(db, **fields)


async def handle_created(db: AsyncSession, event: stripe.Event) -> None:
    await _sync_from_stripe(db, event.data.object)


async def handle_updated(db: AsyncSession, event: stripe.Event) -> None:
    stripe_sub = event.data.object
    await _sync_from_stripe(db, stripe_sub)
    prev = event.data.previous_attributes
    if prev is None:
        return


async def handle_deleted(db: AsyncSession, event: stripe.Event) -> None:
    stripe_sub = event.data.object
    sub = await sub_repo.get_by_stripe_id(db, stripe_sub.id)
    if sub:
        sub.status = SubscriptionStatus.CANCELED
        sub.canceled_at = (
            datetime.fromtimestamp(stripe_sub.canceled_at, UTC)
            if stripe_sub.canceled_at
            else datetime.now(UTC)
        )
        await db.flush()


async def handle_trial_ending(db: AsyncSession, event: stripe.Event) -> None:
    stripe_sub = event.data.object
    logger.info("subscription_trial_ending", extra={"stripe_sub_id": stripe_sub.id})
