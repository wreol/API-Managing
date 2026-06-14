"""Pydantic request/response schemas for team sharing."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------
class ShareRequest(BaseModel):
    key_id: UUID
    shared_with_email: str = Field(..., min_length=1, max_length=255)
    permission: str = Field(..., pattern=r"^(read|use)$")


class UpdateSharePermissionRequest(BaseModel):
    permission: str = Field(..., pattern=r"^(read|use)$")


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------
class ShareResponse(BaseModel):
    id: str
    key_id: str
    shared_by_email: str
    shared_with_email: str
    permission: str

    model_config = {"from_attributes": True}

    @field_validator("id", "key_id", mode="before")
    @classmethod
    def coerce_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v
