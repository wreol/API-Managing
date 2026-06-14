"""Alert Engine API endpoints — AlertRule CRUD and AlertEvent listing."""

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.alert import (
    AlertRuleResponse,
    AlertEventResponse,
    CreateAlertRuleRequest,
    UpdateAlertRuleRequest,
)
from app.services.alert_service import AlertService

router = APIRouter(prefix="/api/v1/alerts", tags=["alerts"])


# ---------------------------------------------------------------------------
# GET /api/v1/alerts/rules — List alert rules
# ---------------------------------------------------------------------------
@router.get("/rules", response_model=list[AlertRuleResponse])
async def list_rules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert_service = AlertService(db)
    return await alert_service.list_rules(user=current_user)


# ---------------------------------------------------------------------------
# POST /api/v1/alerts/rules — Create alert rule
# ---------------------------------------------------------------------------
@router.post("/rules", response_model=AlertRuleResponse, status_code=201)
async def create_rule(
    body: CreateAlertRuleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert_service = AlertService(db)
    return await alert_service.create_rule(
        user=current_user,
        key_id=body.key_id,
        notify_email=body.notify_email,
    )


# ---------------------------------------------------------------------------
# PATCH /api/v1/alerts/rules/{id} — Update alert rule
# ---------------------------------------------------------------------------
@router.patch("/rules/{rule_id}", response_model=AlertRuleResponse)
async def update_rule(
    rule_id: uuid.UUID,
    body: UpdateAlertRuleRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert_service = AlertService(db)
    return await alert_service.update_rule(
        user=current_user,
        rule_id=rule_id,
        data=body,
    )


# ---------------------------------------------------------------------------
# DELETE /api/v1/alerts/rules/{id} — Delete alert rule
# ---------------------------------------------------------------------------
@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert_service = AlertService(db)
    await alert_service.delete_rule(user=current_user, rule_id=rule_id)
    return {"message": "Alert rule deleted"}


# ---------------------------------------------------------------------------
# GET /api/v1/alerts/events — List alert events
# ---------------------------------------------------------------------------
@router.get("/events", response_model=list[AlertEventResponse])
async def list_events(
    unread_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert_service = AlertService(db)
    return await alert_service.list_events(
        user=current_user,
        unread_only=unread_only,
    )


# ---------------------------------------------------------------------------
# PATCH /api/v1/alerts/events/{id}/read — Mark event as read
# ---------------------------------------------------------------------------
@router.patch("/events/{event_id}/read", response_model=AlertEventResponse)
async def mark_event_read(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    alert_service = AlertService(db)
    return await alert_service.mark_event_read(
        user=current_user,
        event_id=event_id,
    )
