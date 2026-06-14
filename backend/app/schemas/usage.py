"""Pydantic request/response schemas for usage dashboard."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------
class ProviderBreakdown(BaseModel):
    provider: str
    calls: int = 0
    tokens: int = 0
    cost: float = 0.0


class KeyBreakdown(BaseModel):
    key_id: str
    key_label: str
    provider: str
    calls: int = 0
    tokens: int = 0
    cost: float = 0.0


class UsageSummaryResponse(BaseModel):
    total_calls: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    by_provider: list[ProviderBreakdown] = []


class TrendDataPoint(BaseModel):
    period: str  # ISO date string, e.g. "2026-06-14"
    calls: int = 0
    tokens: int = 0
    cost: float = 0.0
