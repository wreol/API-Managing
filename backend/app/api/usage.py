"""Usage Dashboard API endpoints — summary, trend, by-provider, by-key."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.usage import (
    UsageSummaryResponse,
    TrendDataPoint,
    ProviderBreakdown,
    KeyBreakdown,
)
from app.services.usage_service import UsageService

router = APIRouter(prefix="/api/v1/usage", tags=["usage"])


# ---------------------------------------------------------------------------
# GET /api/v1/usage/summary — aggregate usage overview
# ---------------------------------------------------------------------------
@router.get("/summary", response_model=UsageSummaryResponse)
async def usage_summary(
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    usage_service = UsageService(db)
    return await usage_service.get_summary(
        user=current_user,
        from_date=from_date,
        to_date=to_date,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/usage/trend — time series data
# ---------------------------------------------------------------------------
@router.get("/trend", response_model=list[TrendDataPoint])
async def usage_trend(
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    granularity: str = Query("day", pattern=r"^(hour|day|month)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    usage_service = UsageService(db)
    return await usage_service.get_trend(
        user=current_user,
        from_date=from_date,
        to_date=to_date,
        granularity=granularity,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/usage/by-provider — per-provider breakdown
# ---------------------------------------------------------------------------
@router.get("/by-provider", response_model=list[ProviderBreakdown])
async def usage_by_provider(
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    usage_service = UsageService(db)
    return await usage_service.get_by_provider(
        user=current_user,
        from_date=from_date,
        to_date=to_date,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/usage/by-key — per-key breakdown
# ---------------------------------------------------------------------------
@router.get("/by-key", response_model=list[KeyBreakdown])
async def usage_by_key(
    from_date: date | None = Query(None, alias="from"),
    to_date: date | None = Query(None, alias="to"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    usage_service = UsageService(db)
    return await usage_service.get_by_key(
        user=current_user,
        from_date=from_date,
        to_date=to_date,
    )
