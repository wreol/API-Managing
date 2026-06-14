"""Team Sharing API routes — share keys with other users."""

import uuid

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.team import ShareRequest, ShareResponse, UpdateSharePermissionRequest
from app.services.audit_service import AuditService
from app.services.team_service import TeamService

router = APIRouter(prefix="/api/v1/team", tags=["team"])


# ---------------------------------------------------------------------------
# POST /api/v1/team/share — Share a key with another user
# ---------------------------------------------------------------------------
@router.post("/share", response_model=ShareResponse)
async def share_key(
    body: ShareRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team_service = TeamService(db)
    result = await team_service.share_key(
        user=current_user,
        key_id=body.key_id,
        shared_with_email=body.shared_with_email,
        permission=body.permission,
    )

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="key_shared",
        resource_type="key_share",
        resource_id=uuid.UUID(result.id),
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return result


# ---------------------------------------------------------------------------
# GET /api/v1/team/shares — List shares (sent or received)
# ---------------------------------------------------------------------------
@router.get("/shares", response_model=list[ShareResponse])
async def list_shares(
    direction: str = "sent",
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team_service = TeamService(db)
    return await team_service.list_shares(user=current_user, direction=direction)


# ---------------------------------------------------------------------------
# PATCH /api/v1/team/share/{id} — Change permission level
# ---------------------------------------------------------------------------
@router.patch("/share/{share_id}", response_model=ShareResponse)
async def update_share_permission(
    share_id: uuid.UUID,
    body: UpdateSharePermissionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team_service = TeamService(db)
    return await team_service.update_permission(
        user=current_user,
        share_id=share_id,
        permission=body.permission,
    )


# ---------------------------------------------------------------------------
# DELETE /api/v1/team/share/{id} — Revoke a share
# ---------------------------------------------------------------------------
@router.delete("/share/{share_id}")
async def revoke_share(
    share_id: uuid.UUID,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    team_service = TeamService(db)
    await team_service.revoke_share(user=current_user, share_id=share_id)

    # Audit log
    audit_service = AuditService(db)
    await audit_service.log(
        user_id=current_user.id,
        action="share_revoked",
        resource_type="key_share",
        resource_id=share_id,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )

    return {"message": "Share revoked"}
