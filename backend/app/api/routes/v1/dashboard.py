"""Dashboard API — aggregated stats and activity feed."""

from typing import Any

from fastapi import APIRouter

from app.api.deps import CurrentUser, DBSession
from app.services.dashboard import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=None)
async def get_dashboard(
    db: DBSession, user: CurrentUser,
) -> Any:
    service = DashboardService(db)
    return await service.get_dashboard(user.id)
