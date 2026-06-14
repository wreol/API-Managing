"""Alert business logic: CRUD rules, evaluate, list/create events."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

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


VALID_ALERT_TYPES = {"budget", "call_count"}


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
        type: str,
        threshold: float,
        notify_email: str,
        provider: str | None = None,
        key_id: str | None = None,
    ) -> AlertRuleResponse:
        """Create a new alert rule for the user."""
        # Validate type
        if type not in VALID_ALERT_TYPES:
            raise HTTPException(
                status_code=422,
                detail=f"Invalid alert type: {type}. Must be one of: {', '.join(VALID_ALERT_TYPES)}",
            )

        # Require verified email
        if not user.email_verified:
            raise HTTPException(
                status_code=403,
                detail="Email must be verified before creating alert rules",
            )

        rule = AlertRule(
            id=uuid.uuid4(),
            user_id=user.id,
            key_id=uuid.UUID(key_id) if key_id else None,
            provider=provider,
            type=type,
            threshold=threshold,
            notify_email=notify_email,
            is_active=True,
        )
        self.db.add(rule)
        await self.db.flush()

        return AlertRuleResponse(
            id=str(rule.id),
            type=rule.type,
            threshold=float(rule.threshold),
            provider=rule.provider,
            key_id=str(rule.key_id) if rule.key_id else None,
            notify_email=rule.notify_email,
            is_active=rule.is_active,
        )

    async def list_rules(self, *, user: User) -> list[AlertRuleResponse]:
        """List all alert rules for the authenticated user."""
        result = await self.db.execute(
            select(AlertRule).where(AlertRule.user_id == user.id)
        )
        rules = result.scalars().all()
        return [
            AlertRuleResponse(
                id=str(r.id),
                type=r.type,
                threshold=float(r.threshold),
                provider=r.provider,
                key_id=str(r.key_id) if r.key_id else None,
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
        """Update an alert rule owned by the user."""
        rule = await self._get_owned_rule(user, rule_id)

        if data.type is not None:
            if data.type not in VALID_ALERT_TYPES:
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid alert type: {data.type}",
                )
            rule.type = data.type
        if data.threshold is not None:
            rule.threshold = data.threshold
        if data.is_active is not None:
            rule.is_active = data.is_active
        if data.notify_email is not None:
            rule.notify_email = data.notify_email

        await self.db.flush()

        return AlertRuleResponse(
            id=str(rule.id),
            type=rule.type,
            threshold=float(rule.threshold),
            provider=rule.provider,
            key_id=str(rule.key_id) if rule.key_id else None,
            notify_email=rule.notify_email,
            is_active=rule.is_active,
        )

    async def delete_rule(self, *, user: User, rule_id: uuid.UUID) -> None:
        """Delete an alert rule owned by the user."""
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
        """List alert events for the user's rules."""
        # Get user's rule IDs
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
                threshold_pct=float(e.threshold_pct),
                message=e.message,
                is_read=e.is_read,
                email_sent=e.email_sent,
            )
            for e in events
        ]

    async def mark_event_read(
        self, *, user: User, event_id: uuid.UUID
    ) -> AlertEventResponse:
        """Mark an alert event as read."""
        # Verify the event belongs to a rule owned by the user
        result = await self.db.execute(
            select(AlertEvent).where(AlertEvent.id == event_id)
        )
        event = result.scalar_one_or_none()
        if event is None:
            raise HTTPException(status_code=404, detail="Alert event not found")

        # Verify the event's rule belongs to the user
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
            threshold_pct=float(event.threshold_pct),
            message=event.message,
            is_read=event.is_read,
            email_sent=event.email_sent,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
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
