"""Billing service — delegates to app.services.billing.* module (PostgreSQL async).

Single facade exposed to the API layer for everything billing-related: plans, checkout,
portal, subscription management, credits, and usage. Routes never touch repositories or
the ``app.services.billing.*`` services directly.
"""

import logging
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

import app.repositories.plan as plan_repo
from app.core.exceptions import BadRequestError, NotFoundError
from app.db.models.plan import Plan
from app.db.models.subscription import Subscription
from app.db.models.user import User
from app.repositories import organization_repo
from app.services.billing.checkout_service import CheckoutService
from app.services.billing.exceptions import InvalidWebhookError
from app.services.billing.stripe_client import StripeClient
from app.services.billing.subscription_service import SubscriptionService
from app.services.billing.webhook_handler import WebhookHandler

logger = logging.getLogger(__name__)


class BillingService:
    """Facade over CheckoutService, SubscriptionService, WebhookHandler, CreditService."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self._checkout = CheckoutService(db)
        self._subscription = SubscriptionService(db)

    # -- Plans --

    async def list_active_plans(self) -> list[Plan]:
        return await plan_repo.list_active_plans(self.db)

    async def get_plan(self, code: str) -> Plan:
        plan = await plan_repo.get_plan_by_code(self.db, code)
        if not plan:
            raise NotFoundError(message="Plan not found", details={"code": code})
        return plan

    # -- Checkout / Portal --

    async def create_checkout_session(
        self,
        org_id: uuid.UUID,
        *,
        seats: int = 1,
        price_id: str | None = None,
        success_url: str,
        cancel_url: str,
        user: User | None = None,
    ) -> str:
        """Create a Stripe Checkout session URL."""
        if not price_id:
            raise BadRequestError(message="price_id is required")

        org = await organization_repo.get_by_id(self.db, org_id)
        if org is None:
            raise NotFoundError(message="Organization not found", details={"org_id": str(org_id)})

        price_uuid = uuid.UUID(price_id) if isinstance(price_id, str) else price_id
        result = await self._checkout.create_checkout(
            user=user,
            org_id=org.id,
            price_id=price_uuid,
            seats=seats,
            success_url=success_url,
            cancel_url=cancel_url,
        )
        return result["url"]

    async def create_portal_session(self, org_id: uuid.UUID) -> str:
        """Create a Stripe Customer Portal URL."""
        org = await organization_repo.get_by_id(self.db, org_id)
        if org is None:
            raise NotFoundError(message="Organization not found", details={"org_id": str(org_id)})
        return await self._checkout.create_portal_session(org_id=org.id)

    # -- Webhook --

    async def handle_webhook_event(self, payload: bytes, sig_header: str) -> None:
        """Verify and dispatch a Stripe webhook event."""
        try:
            event = StripeClient.construct_event(payload=payload, signature=sig_header)
        except InvalidWebhookError as exc:
            raise BadRequestError(message=str(exc)) from exc

        handler = WebhookHandler(self.db)
        await handler.dispatch(event)

    # -- Subscription management --

    async def get_subscription(self, org_id: uuid.UUID) -> Subscription | None:
        return await self._subscription.get_for_org(org_id)

    async def cancel_subscription(
        self, org_id: uuid.UUID, *, at_period_end: bool = True
    ) -> Subscription:
        return await self._subscription.cancel(org_id=org_id, at_period_end=at_period_end)

    async def reactivate_subscription(self, org_id: uuid.UUID) -> Subscription:
        return await self._subscription.reactivate(org_id=org_id)

    async def change_plan(self, org_id: uuid.UUID, new_price_id: uuid.UUID) -> Subscription:
        return await self._subscription.change_plan(org_id=org_id, new_price_id=new_price_id)
