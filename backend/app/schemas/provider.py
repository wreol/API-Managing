"""Pydantic request/response schemas for Provider API."""

from __future__ import annotations

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Response schemas
# ---------------------------------------------------------------------------

class ProviderInfoResponse(BaseModel):
    """Info about a single registered provider."""

    name: str
    label: str
    is_custom: bool = False


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------

class CustomProviderRequest(BaseModel):
    """Request to register a custom provider."""

    name: str = Field(..., min_length=1, max_length=50)
    label: str = Field(..., min_length=1, max_length=200)
    base_url: str = Field(..., min_length=1, max_length=500)
    usage_endpoint: str = Field(default="/v1/usage", max_length=300)
    auth_type: str = Field(default="bearer", pattern=r"^(bearer|custom_header)$")
    auth_header_name: str = Field(default="X-API-Key", max_length=100)
    field_mapping: dict = Field(default_factory=dict)
