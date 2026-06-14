"""ARQ background task — evaluate_alerts (key health monitoring).

Tests all active keys against their providers. If a previously-working key
fails the connection test, triggers an alert event and notifies the user.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, and_

from app.database import async_session
from app.models.alert_rule import AlertRule
from app.models.alert_event import AlertEvent
from app.models.api_key import ApiKey
from app.providers.registry import ProviderRegistry
from app.services.encryption_service import EncryptionService
from app.utils.email import send_email
import hashlib
from app.config import settings


def _decrypt_key(encrypted_value: str) -> str:
    key_bytes = hashlib.sha256(settings.KEY_ENCRYPTION_KEY.encode()).digest()
    return EncryptionService(key_bytes=key_bytes).decrypt(encrypted_value)


async def _was_triggered_recently(db, rule_id: uuid.UUID, hours: int = 24) -> bool:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    result = await db.execute(
        select(AlertEvent.id).where(
            and_(AlertEvent.rule_id == rule_id, AlertEvent.triggered_at >= cutoff)
        ).limit(1)
    )
    return result.scalar_one_or_none() is not None


async def evaluate_alerts(ctx: dict) -> dict:
    """Check all active keys: if broken, trigger alert for each active rule on it."""
    triggered = 0

    async with async_session() as db:
        # Get all active keys
        result = await db.execute(
            select(ApiKey).where(ApiKey.is_active == True)
        )
        keys = result.scalars().all()

        for key in keys:
            # Test connection
            try:
                decrypted = _decrypt_key(key.key_encrypted)
                provider = ProviderRegistry.get(key.provider)
                test_result = await provider.test_connection(decrypted)
            except Exception:
                test_result = {"status": "error", "message": "Connection test failed"}

            was_ok = key.status == "ok"
            is_ok = test_result.get("status") == "ok"

            # State transition: ok → error triggers alert
            if was_ok and not is_ok:
                # Update key status
                key.status = "error"

                # Find all active alert rules for this key
                rules_result = await db.execute(
                    select(AlertRule).where(
                        and_(AlertRule.key_id == key.id, AlertRule.is_active == True)
                    )
                )
                rules = rules_result.scalars().all()

                for rule in rules:
                    if await _was_triggered_recently(db, rule.id):
                        continue

                    message = (
                        f"Key '{key.label}' ({key.provider}) is no longer valid. "
                        f"Test result: {test_result.get('message', 'Unknown error')}"
                    )

                    event = AlertEvent(
                        id=uuid.uuid4(),
                        rule_id=rule.id,
                        message=message,
                        is_read=False,
                        email_sent=False,
                    )
                    db.add(event)

                    email_ok = await send_email(
                        to=rule.notify_email,
                        subject=f"API Vault Alert: Key '{key.label}' is down",
                        body=message,
                    )
                    if email_ok:
                        event.email_sent = True

                    triggered += 1

            # State transition: error → ok (key recovered)
            elif not was_ok and is_ok:
                key.status = "ok"

        await db.commit()

    return {"triggered": triggered}
