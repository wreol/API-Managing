"""Pydantic request/response schemas for alert rules and events."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------
class CreateAlertRuleRequest(BaseModel):
    key_id: str = Field(..., min_length=1)
    notify_email: str = Field(..., min_length=3, max_length=255)


class UpdateAlertRuleRequest(BaseModel):
    is_active: bool | None = None
    notify_email: str | None = Field(None, min_length=3, max_length=255)


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------
class AlertRuleResponse(BaseModel):
    id: str
    type: str
    key_id: str
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
