"""Billing routes — Plans, Checkout, Portal, Subscription management, Credits.

Routes are pure HTTP plumbing. All business logic — repositories, Stripe calls,
credit accounting — lives in :class:`app.services.billing.BillingService`.
"""

from typing import Any

from fastapi import APIRouter, Header, Query, Request, status
from sqlalchemy import func, select

from app.api.deps import ActiveOrg, BillingSvc, CurrentUser, DBSession
from app.core.config import settings
from app.db.models.chat_file import ChatFile
from app.db.models.rag_document import RAGDocument
from app.schemas.billing import (
    CheckoutSessionCreate,
    CheckoutSessionRead,
    PlanList,
    PlanRead,
    PortalSessionRead,
    SubscriptionChangePlan,
    SubscriptionRead,
)

router = APIRouter()


@router.get("/plans", response_model=PlanList)
async def list_plans(billing_service: BillingSvc) -> Any:
    """Return all active plans with their prices. Suitable for the pricing page."""
    plans = await billing_service.list_active_plans()
    return PlanList(plans=plans)


@router.get("/plans/{code}", response_model=PlanRead)
async def get_plan(code: str, billing_service: BillingSvc) -> Any:
    """Return a single active plan by code."""
    return await billing_service.get_plan(code)


@router.post("/checkout", response_model=CheckoutSessionRead, status_code=status.HTTP_201_CREATED)
async def create_checkout_session(
    data: CheckoutSessionCreate,
    current_user: CurrentUser,
    active_org: ActiveOrg,
    billing_service: BillingSvc,
) -> Any:
    """Create a Stripe Checkout session and return the redirect URL."""
    url = await billing_service.create_checkout_session(
        active_org.id,
        user=current_user,
        seats=data.seats,
        price_id=str(data.price_id),
        success_url=data.success_url,
        cancel_url=data.cancel_url,
    )
    return CheckoutSessionRead(url=url)


@router.post("/portal", response_model=PortalSessionRead)
async def create_portal_session(
    current_user: CurrentUser,
    active_org: ActiveOrg,
    billing_service: BillingSvc,
) -> Any:
    """Open the Stripe Customer Portal for managing the active org's subscription."""
    url = await billing_service.create_portal_session(active_org.id)
    return PortalSessionRead(url=url)


@router.get("/me/subscription", response_model=SubscriptionRead | None)
async def get_subscription(
    current_user: CurrentUser,
    active_org: ActiveOrg,
    billing_service: BillingSvc,
) -> Any:
    """Get the active subscription for the current organization."""
    return await billing_service.get_subscription(active_org.id)


@router.patch("/me/subscription", response_model=SubscriptionRead)
async def change_plan(
    data: SubscriptionChangePlan,
    current_user: CurrentUser,
    active_org: ActiveOrg,
    billing_service: BillingSvc,
) -> Any:
    """Upgrade or downgrade the current organization's subscription plan."""
    return await billing_service.change_plan(active_org.id, data.new_price_id)


@router.delete("/me/subscription", response_model=SubscriptionRead)
async def cancel_subscription(
    current_user: CurrentUser,
    active_org: ActiveOrg,
    billing_service: BillingSvc,
    at_period_end: bool = Query(True, description="Cancel at period end (recommended)"),
) -> Any:
    """Cancel the active subscription. Defaults to end-of-period cancellation."""
    return await billing_service.cancel_subscription(active_org.id, at_period_end=at_period_end)


@router.post("/me/subscription/reactivate", response_model=SubscriptionRead)
async def reactivate_subscription(
    current_user: CurrentUser,
    active_org: ActiveOrg,
    billing_service: BillingSvc,
) -> Any:
    """Undo a scheduled cancellation if the period hasn't ended yet."""
    return await billing_service.reactivate_subscription(active_org.id)


@router.get("/me/storage")
async def get_storage_usage(
    current_user: CurrentUser,
    active_org: ActiveOrg,
    db: DBSession,
) -> dict[str, Any]:
    """Sum bytes used by chat-attached files (per-user) and RAG docs (per-org)."""
    chat_bytes = (
        await db.execute(
            select(func.coalesce(func.sum(ChatFile.size), 0)).where(
                ChatFile.user_id == current_user.id
            )
        )
    ).scalar_one()
    rag_bytes = (
        await db.execute(
            select(func.coalesce(func.sum(RAGDocument.filesize), 0)).where(
                RAGDocument.organization_id == active_org.id
            )
        )
    ).scalar_one()
    return {
        "chat_bytes": int(chat_bytes),
        "rag_bytes": int(rag_bytes),
        "total_bytes": int(chat_bytes) + int(rag_bytes),
        # Soft cap surfaced by the gauge — not enforced server-side yet.
        "limit_bytes": settings.STORAGE_SOFT_LIMIT_BYTES,
    }


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(
    request: Request,
    billing_service: BillingSvc,
    stripe_signature: str = Header(..., alias="stripe-signature"),
) -> Any:
    """Receive and process Stripe webhook events.

    Stripe sends a ``stripe-signature`` header for HMAC payload verification.
    This endpoint is intentionally unauthenticated.
    """
    payload = await request.body()
    await billing_service.handle_webhook_event(payload, stripe_signature)
    return {"received": True}
