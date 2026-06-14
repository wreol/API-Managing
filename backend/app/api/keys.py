"""Key Vault API routes — CRUD, copy, and test endpoints."""

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.api_key import (
    AddKeyRequest,
    UpdateKeyRequest,
    KeyResponse,
    KeyDetailResponse,
    KeyCopyResponse,
)
from app.services.audit_service import AuditService
from app.services.key_service import KeyService

router = APIRouter(prefix="/api/v1/keys", tags=["keys"])


# ---------------------------------------------------------------------------
# POST /api/v1/keys — Add a new API key
# ---------------------------------------------------------------------------
@router.post("", response_model=KeyResponse)
async def add_key(
    body: AddKeyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    key_service = KeyService(db)
    return await key_service.add_key(
        user=current_user,
        provider=body.provider,
        key_value=body.key_value,
        label=body.label,
        tags=body.tags,
    )


# ---------------------------------------------------------------------------
# GET /api/v1/keys — List user's active keys
# ---------------------------------------------------------------------------
@router.get("", response_model=list[KeyResponse])
async def list_keys(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    key_service = KeyService(db)
    return await key_service.list_keys(user=current_user)


# ---------------------------------------------------------------------------
# GET /api/v1/keys/{id} — Key detail
# ---------------------------------------------------------------------------
@router.get("/{key_id}", response_model=KeyDetailResponse)
async def get_key(
    key_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    key_service = KeyService(db)
    return await key_service.get_key(user=current_user, key_id=key_id)


# ---------------------------------------------------------------------------
# PATCH /api/v1/keys/{id} — Update label/tags
# ---------------------------------------------------------------------------
@router.patch("/{key_id}", response_model=KeyResponse)
async def update_key(
    key_id: uuid.UUID,
    body: UpdateKeyRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    key_service = KeyService(db)
    return await key_service.update_key(
        user=current_user,
        key_id=key_id,
        label=body.label,
        tags=body.tags,
    )


# ---------------------------------------------------------------------------
# DELETE /api/v1/keys/{id} — Soft delete
# ---------------------------------------------------------------------------
@router.delete("/{key_id}")
async def delete_key(
    key_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    key_service = KeyService(db)
    await key_service.delete_key(user=current_user, key_id=key_id)
    return {"message": "Key deleted"}


# ---------------------------------------------------------------------------
# POST /api/v1/keys/{id}/copy — Decrypt and return key value
# ---------------------------------------------------------------------------
@router.post("/{key_id}/copy", response_model=KeyCopyResponse)
async def copy_key(
    key_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    key_service = KeyService(db)
    result = await key_service.copy_key(user=current_user, key_id=key_id)

    # Record audit log
    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="key_copied",
        resource_type="api_key",
        resource_id=key_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return result


# ---------------------------------------------------------------------------
# POST /api/v1/keys/{id}/test — Test connection to provider
# ---------------------------------------------------------------------------
@router.post("/{key_id}/test")
async def test_key(
    key_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    key_service = KeyService(db)
    return await key_service.test_key(user=current_user, key_id=key_id)
