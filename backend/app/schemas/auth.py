"""Pydantic request/response schemas for authentication."""

from pydantic import BaseModel, Field, field_validator
from uuid import UUID


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------
class RegisterRequest(BaseModel):
    email: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=8)
    display_name: str = Field(..., min_length=1, max_length=100)


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=1, max_length=255)
    password: str = Field(..., min_length=1)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(..., min_length=1)


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------
class UserResponse(BaseModel):
    id: str
    email: str
    display_name: str
    oauth_provider: str | None = None
    email_verified: bool = False

    model_config = {"from_attributes": True}

    @field_validator("id", mode="before")
    @classmethod
    def coerce_uuid_to_str(cls, v):
        if isinstance(v, UUID):
            return str(v)
        return v


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse
