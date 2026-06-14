"""ARQ background task — evaluate_alerts.

Checks active AlertRules against current UsageRecords and triggers
AlertEvents when thresholds are exceeded (80% warning, 100% critical).
"""

from __future__ import annotations

from datetime import date, datetime, timedelta, timezone
import uuid

from sqlalchemy import select, func, and_, text

from app.database import async_session
from app.models.alert_rule import AlertRule
from app.models.alert_event import AlertEvent
from app.models.usage_record import UsageRecord
from app.models.api_key import ApiKey
from app.utils.email import send_email


async def _get_current_usage(db, rule: AlertRule) -> float:
    """Compute the current usage metric for a rule (cost or calls)."""
    conditions = [ApiKey.user_id == rule.user_id]
    if rule.key_id is not None:
        conditions.append(UsageRecord.key_id == rule.key_id)
    else:
        # Provider-level: filter by provider if specified
        if rule.provider is not None:
            conditions.append(UsageRecord.provider == rule.provider)

    if rule.type == "call_count":
        result = await db.execute(
            select(func.coalesce(func.sum(UsageRecord.calls), 0)).where(
                and_(
                    UsageRecord.key_id.in_(
                        select(ApiKey.id).where(and_(*conditions))
                    ),
                )
            )
        )
    else:  # budget
        result = await db.execute(
            select(func.coalesce(func.sum(UsageRecord.cost_estimate), 0.0)).where(
                and_(
                    UsageRecord.key_id.in_(
                        select(ApiKey.id).where(and_(*conditions))
                    ),
                )
            )
        )

    val = result.scalar_one()
    return float(val)


async def _was_triggered_recently(db, rule_id: uuid.UUID, hours: int = 24) -> bool:
    """Check if an alert was already triggered for this rule within the last N hours."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    result = await db.execute(
        select(AlertEvent.id).where(
            and_(
                AlertEvent.rule_id == rule_id,
                AlertEvent.triggered_at >= cutoff,
            )
        ).limit(1)
    )
    return result.scalar_one_or_none() is not None


async def evaluate_alerts(ctx: dict) -> dict:
    """Evaluate all active alert rules and trigger events where thresholds exceeded."""
    triggered = 0

    async with async_session() as db:
        result = await db.execute(
            select(AlertRule).where(AlertRule.is_active == True)
        )
        rules = result.scalars().all()

        for rule in rules:
            # Skip if already triggered within the last 24h
            if await _was_triggered_recently(db, rule.id):
                continue

            current = await _get_current_usage(db, rule)

            # Determine threshold percentage
            pct = (current / rule.threshold * 100) if rule.threshold > 0 else 0
            threshold_pct = round(pct, 2)

            # Only trigger at 80% (warning) or 100%+ (critical)
            if threshold_pct < 80:
                continue

            level = "critical" if threshold_pct >= 100 else "warning"
            metric_name = {
                "budget": "Cost",
                "call_count": "Call count",
            }.get(rule.type, rule.type)

            message = (
                f"[{level.upper()}] {metric_name} alert: "
                f"{current:.2f} / {rule.threshold:.2f} "
                f"({threshold_pct:.1f}% of threshold)"
            )

            # Create alert event (in-app notification)
            event = AlertEvent(
                id=uuid.uuid4(),
                rule_id=rule.id,
                threshold_pct=threshold_pct,
                message=message,
                is_read=False,
                email_sent=False,
            )
            db.add(event)

            # Try to send email
            email_ok = await send_email(
                to=rule.notify_email,
                subject=f"API Vault Alert: {metric_name} {level}",
                body=message,
            )
            if email_ok:
                event.email_sent = True

            triggered += 1

        await db.commit()

    return {"triggered": triggered}
