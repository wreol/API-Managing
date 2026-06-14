"""Alert business logic: key health monitoring rules and events."""

from __future__ import annotations

import uuid

from fastapi import HTTPException
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert_rule import AlertRule
from app.models.alert_event import AlertEvent
from app.models.user import User
from app.schemas.alert import (
    AlertRuleResponse,
    AlertEventResponse,
    CreateAlertRuleRequest,
    UpdateAlertRuleRequest,
)


class AlertService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Rule CRUD
    # ------------------------------------------------------------------
    async def create_rule(
        self,
        *,
        user: User,
        key_id: str,
        notify_email: str,
    ) -> AlertRuleResponse:
        if not user.email_verified:
            raise HTTPException(
                status_code=403,
                detail="Email must be verified before creating alert rules",
            )

        rule = AlertRule(
            id=uuid.uuid4(),
            user_id=user.id,
            key_id=uuid.UUID(key_id),
            type="key_health",
            notify_email=notify_email,
            is_active=True,
        )
        self.db.add(rule)
        await self.db.flush()

        return AlertRuleResponse(
            id=str(rule.id),
            type=rule.type,
            key_id=str(rule.key_id),
            notify_email=rule.notify_email,
            is_active=rule.is_active,
        )

    async def list_rules(self, *, user: User) -> list[AlertRuleResponse]:
        result = await self.db.execute(
            select(AlertRule).where(AlertRule.user_id == user.id)
        )
        rules = result.scalars().all()
        return [
            AlertRuleResponse(
                id=str(r.id),
                type=r.type,
                key_id=str(r.key_id),
                notify_email=r.notify_email,
                is_active=r.is_active,
            )
            for r in rules
        ]

    async def update_rule(
        self,
        *,
        user: User,
        rule_id: uuid.UUID,
        data: UpdateAlertRuleRequest,
    ) -> AlertRuleResponse:
        rule = await self._get_owned_rule(user, rule_id)

        if data.is_active is not None:
            rule.is_active = data.is_active
        if data.notify_email is not None:
            rule.notify_email = data.notify_email

        await self.db.flush()

        return AlertRuleResponse(
            id=str(rule.id),
            type=rule.type,
            key_id=str(rule.key_id),
            notify_email=rule.notify_email,
            is_active=rule.is_active,
        )

    async def delete_rule(self, *, user: User, rule_id: uuid.UUID) -> None:
        rule = await self._get_owned_rule(user, rule_id)
        await self.db.delete(rule)
        await self.db.flush()

    # ------------------------------------------------------------------
    # Event listing
    # ------------------------------------------------------------------
    async def list_events(
        self,
        *,
        user: User,
        unread_only: bool = False,
    ) -> list[AlertEventResponse]:
        rule_ids_subq = select(AlertRule.id).where(AlertRule.user_id == user.id)

        conditions = [AlertEvent.rule_id.in_(rule_ids_subq)]
        if unread_only:
            conditions.append(AlertEvent.is_read == False)

        result = await self.db.execute(
            select(AlertEvent)
            .where(and_(*conditions))
            .order_by(AlertEvent.triggered_at.desc())
        )
        events = result.scalars().all()

        return [
            AlertEventResponse(
                id=str(e.id),
                rule_id=str(e.rule_id),
                triggered_at=e.triggered_at,
                message=e.message,
                is_read=e.is_read,
                email_sent=e.email_sent,
            )
            for e in events
        ]

    async def mark_event_read(
        self, *, user: User, event_id: uuid.UUID
    ) -> AlertEventResponse:
        result = await self.db.execute(
            select(AlertEvent).where(AlertEvent.id == event_id)
        )
        event = result.scalar_one_or_none()
        if event is None:
            raise HTTPException(status_code=404, detail="Alert event not found")

        rule_result = await self.db.execute(
            select(AlertRule).where(AlertRule.id == event.rule_id)
        )
        rule = rule_result.scalar_one_or_none()
        if rule is None or rule.user_id != user.id:
            raise HTTPException(status_code=404, detail="Alert event not found")

        event.is_read = True
        await self.db.flush()

        return AlertEventResponse(
            id=str(event.id),
            rule_id=str(event.rule_id),
            triggered_at=event.triggered_at,
            message=event.message,
            is_read=event.is_read,
            email_sent=event.email_sent,
        )

    async def _get_owned_rule(self, user: User, rule_id: uuid.UUID) -> AlertRule:
        result = await self.db.execute(
            select(AlertRule).where(
                and_(AlertRule.id == rule_id, AlertRule.user_id == user.id)
            )
        )
        rule = result.scalar_one_or_none()
        if rule is None:
            raise HTTPException(status_code=404, detail="Alert rule not found")
        return rule
