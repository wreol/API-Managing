"""Pydantic request/response schemas for API key management."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------
class AddKeyRequest(BaseModel):
    provider: str = Field(..., min_length=1, max_length=50)
    key_value: str = Field(..., min_length=1)
    label: str = Field(..., min_length=1, max_length=200)
    tags: list[str] | None = None


class UpdateKeyRequest(BaseModel):
    label: str | None = Field(default=None, min_length=1, max_length=200)
    tags: list[str] | None = None


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------
class KeyResponse(BaseModel):
    id: str
    provider: str
    label: str
    masked_key: str
    status: str = "ok"
    permission: str | None = None  # None = owner, "read" = view only, "use" = full access

    model_config = {"from_attributes": True}

    @field_validator("id", mode="before")
    @classmethod
    def coerce_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v


class KeyDetailResponse(BaseModel):
    id: str
    provider: str
    label: str
    masked_key: str
    tags: list | None = None
    is_active: bool = True
    status: str = "ok"

    model_config = {"from_attributes": True}

    @field_validator("id", mode="before")
    @classmethod
    def coerce_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v


class KeyCopyResponse(BaseModel):
    key_value: str
