"""Pydantic request/response schemas for alert rules and events."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------
class CreateAlertRuleRequest(BaseModel):
    type: str = Field(..., pattern=r"^(budget|call_count)$")
    threshold: float = Field(..., gt=0)
    provider: str | None = None
    key_id: str | None = None
    notify_email: str = Field(..., min_length=3, max_length=255)


class UpdateAlertRuleRequest(BaseModel):
    type: str | None = Field(None, pattern=r"^(budget|call_count)$")
    threshold: float | None = Field(None, gt=0)
    is_active: bool | None = None
    notify_email: str | None = Field(None, min_length=3, max_length=255)


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------
class AlertRuleResponse(BaseModel):
    id: str
    type: str
    threshold: float
    provider: str | None = None
    key_id: str | None = None
    notify_email: str
    is_active: bool

    model_config = {"from_attributes": True}

    @field_validator("id", "key_id", mode="before")
    @classmethod
    def coerce_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v


class AlertEventResponse(BaseModel):
    id: str
    rule_id: str
    triggered_at: datetime
    threshold_pct: float
    message: str
    is_read: bool
    email_sent: bool

    model_config = {"from_attributes": True}

    @field_validator("id", "rule_id", mode="before")
    @classmethod
    def coerce_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v
