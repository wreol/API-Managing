"""Usage data aggregation service for dashboard endpoints."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select, func, and_, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ApiKey
from app.models.usage_record import UsageRecord
from app.models.user import User
from app.schemas.usage import (
    UsageSummaryResponse,
    ProviderBreakdown,
    KeyBreakdown,
    TrendDataPoint,
)


class UsageService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # GET /api/v1/usage/summary
    # ------------------------------------------------------------------
    async def get_summary(
        self,
        *,
        user: User,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> UsageSummaryResponse:
        """Aggregate usage across all keys for the authenticated user."""
        # Get all key IDs for this user
        key_ids_subq = select(ApiKey.id).where(ApiKey.user_id == user.id)

        # Build base query
        conditions = [UsageRecord.key_id.in_(key_ids_subq)]
        if from_date is not None:
            conditions.append(cast(UsageRecord.period_start, Date) >= from_date)
        if to_date is not None:
            conditions.append(cast(UsageRecord.period_end, Date) <= to_date)

        # Total aggregates
        agg_result = await self.db.execute(
            select(
                func.coalesce(func.sum(UsageRecord.calls), 0).label("total_calls"),
                func.coalesce(
                    func.sum(UsageRecord.tokens_in) + func.sum(UsageRecord.tokens_out),
                    0,
                ).label("total_tokens"),
                func.coalesce(func.sum(UsageRecord.cost_estimate), 0.0).label(
                    "total_cost"
                ),
            ).where(and_(*conditions))
        )
        agg = agg_result.one_or_none()
        total_calls = agg.total_calls if agg else 0
        total_tokens = agg.total_tokens if agg else 0
        total_cost = float(agg.total_cost) if agg else 0.0

        # By-provider breakdown
        provider_result = await self.db.execute(
            select(
                UsageRecord.provider,
                func.coalesce(func.sum(UsageRecord.calls), 0).label("calls"),
                func.coalesce(
                    func.sum(UsageRecord.tokens_in) + func.sum(UsageRecord.tokens_out),
                    0,
                ).label("tokens"),
                func.coalesce(func.sum(UsageRecord.cost_estimate), 0.0).label("cost"),
            )
            .where(and_(*conditions))
            .group_by(UsageRecord.provider)
            .order_by(UsageRecord.provider)
        )
        by_provider = [
            ProviderBreakdown(
                provider=row.provider,
                calls=row.calls,
                tokens=row.tokens,
                cost=float(row.cost),
            )
            for row in provider_result.all()
        ]

        return UsageSummaryResponse(
            total_calls=total_calls,
            total_tokens=total_tokens,
            total_cost=total_cost,
            by_provider=by_provider,
        )

    # ------------------------------------------------------------------
    # GET /api/v1/usage/trend
    # ------------------------------------------------------------------
    async def get_trend(
        self,
        *,
        user: User,
        from_date: date | None = None,
        to_date: date | None = None,
        granularity: str = "day",
    ) -> list[TrendDataPoint]:
        """Return time-series usage data grouped by period."""
        key_ids_subq = select(ApiKey.id).where(ApiKey.user_id == user.id)

        conditions = [UsageRecord.key_id.in_(key_ids_subq)]
        if from_date is not None:
            conditions.append(cast(UsageRecord.period_start, Date) >= from_date)
        if to_date is not None:
            conditions.append(cast(UsageRecord.period_end, Date) <= to_date)

        # Group by period_start date
        result = await self.db.execute(
            select(
                UsageRecord.period_start.label("period"),
                func.coalesce(func.sum(UsageRecord.calls), 0).label("calls"),
                func.coalesce(
                    func.sum(UsageRecord.tokens_in) + func.sum(UsageRecord.tokens_out),
                    0,
                ).label("tokens"),
                func.coalesce(func.sum(UsageRecord.cost_estimate), 0.0).label("cost"),
            )
            .where(and_(*conditions))
            .group_by(UsageRecord.period_start)
            .order_by(UsageRecord.period_start)
        )

        trend = []
        for row in result.all():
            period_str = (
                row.period.isoformat()
                if isinstance(row.period, date)
                else str(row.period)
            )
            trend.append(
                TrendDataPoint(
                    period=period_str,
                    calls=row.calls,
                    tokens=row.tokens,
                    cost=float(row.cost),
                )
            )
        return trend

    # ------------------------------------------------------------------
    # GET /api/v1/usage/by-provider
    # ------------------------------------------------------------------
    async def get_by_provider(
        self,
        *,
        user: User,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[ProviderBreakdown]:
        """Return per-provider usage breakdown."""
        key_ids_subq = select(ApiKey.id).where(ApiKey.user_id == user.id)

        conditions = [UsageRecord.key_id.in_(key_ids_subq)]
        if from_date is not None:
            conditions.append(cast(UsageRecord.period_start, Date) >= from_date)
        if to_date is not None:
            conditions.append(cast(UsageRecord.period_end, Date) <= to_date)

        result = await self.db.execute(
            select(
                UsageRecord.provider,
                func.coalesce(func.sum(UsageRecord.calls), 0).label("calls"),
                func.coalesce(
                    func.sum(UsageRecord.tokens_in) + func.sum(UsageRecord.tokens_out),
                    0,
                ).label("tokens"),
                func.coalesce(func.sum(UsageRecord.cost_estimate), 0.0).label("cost"),
            )
            .where(and_(*conditions))
            .group_by(UsageRecord.provider)
            .order_by(UsageRecord.provider)
        )

        return [
            ProviderBreakdown(
                provider=row.provider,
                calls=row.calls,
                tokens=row.tokens,
                cost=float(row.cost),
            )
            for row in result.all()
        ]

    # ------------------------------------------------------------------
    # GET /api/v1/usage/by-key
    # ------------------------------------------------------------------
    async def get_by_key(
        self,
        *,
        user: User,
        from_date: date | None = None,
        to_date: date | None = None,
    ) -> list[KeyBreakdown]:
        """Return per-key usage breakdown."""
        key_ids_subq = select(ApiKey.id).where(ApiKey.user_id == user.id)

        conditions = [UsageRecord.key_id.in_(key_ids_subq)]
        if from_date is not None:
            conditions.append(cast(UsageRecord.period_start, Date) >= from_date)
        if to_date is not None:
            conditions.append(cast(UsageRecord.period_end, Date) <= to_date)

        result = await self.db.execute(
            select(
                UsageRecord.key_id,
                UsageRecord.provider,
                func.coalesce(func.sum(UsageRecord.calls), 0).label("calls"),
                func.coalesce(
                    func.sum(UsageRecord.tokens_in) + func.sum(UsageRecord.tokens_out),
                    0,
                ).label("tokens"),
                func.coalesce(func.sum(UsageRecord.cost_estimate), 0.0).label("cost"),
            )
            .where(and_(*conditions))
            .group_by(UsageRecord.key_id, UsageRecord.provider)
            .order_by(UsageRecord.key_id)
        )

        breakdowns = []
        for row in result.all():
            # Fetch key label
            key_result = await self.db.execute(
                select(ApiKey.label).where(ApiKey.id == row.key_id)
            )
            key_row = key_result.one_or_none()
            key_label = key_row.label if key_row else "Unknown"

            breakdowns.append(
                KeyBreakdown(
                    key_id=str(row.key_id),
                    key_label=key_label,
                    provider=row.provider,
                    calls=row.calls,
                    tokens=row.tokens,
                    cost=float(row.cost),
                )
            )
        return breakdowns
