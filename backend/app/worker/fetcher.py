"""ARQ background worker — fetch_all_usage task.

Run via: arq backend.app.worker.fetcher.WorkerSettings
"""

from __future__ import annotations

from datetime import date

from arq.connections import RedisSettings

from app.config import settings as app_settings
from app.database import async_session
from app.models.api_key import ApiKey
from app.models.usage_record import UsageRecord as UsageRecordModel
from app.providers import ProviderRegistry
from app.providers.openai import OpenAIProvider
from app.providers.anthropic import AnthropicProvider
from app.providers.deepseek import DeepSeekProvider
from app.providers.generic import GenericProvider
from app.services.encryption_service import EncryptionService
import hashlib
import uuid
from sqlalchemy import select


def _build_registry() -> ProviderRegistry:
    """Build the provider registry with all built-in and custom providers."""
    registry = ProviderRegistry()
    registry.register(OpenAIProvider())
    registry.register(AnthropicProvider())
    registry.register(DeepSeekProvider())

    # Register persisted custom providers from the global registry
    for name in ProviderRegistry.list_providers():
        if name not in ("openai", "anthropic", "deepseek"):
            try:
                provider = ProviderRegistry.get(name)
                registry.register(provider)
            except KeyError:
                pass

    return registry


def _decrypt_key(encrypted_value: str) -> str:
    """Decrypt an API key's encrypted value."""
    key_bytes = hashlib.sha256(
        app_settings.KEY_ENCRYPTION_KEY.encode()
    ).digest()
    enc_svc = EncryptionService(key_bytes=key_bytes)
    return enc_svc.decrypt(encrypted_value)


async def fetch_all_usage(ctx: dict) -> dict:
    """Fetch usage data from all active API keys across all providers.

    Called by ARQ on a schedule (e.g. every PROVIDER_FETCH_INTERVAL_MINUTES).
    """
    registry = _build_registry()
    keys_processed = 0

    async with async_session() as db:
        result = await db.execute(
            select(ApiKey).where(ApiKey.is_active == True)
        )
        api_keys = result.scalars().all()

        for api_key in api_keys:
            provider = registry.get(api_key.provider)
            if provider is None:
                continue

            try:
                decrypted_key = _decrypt_key(api_key.key_encrypted)
                usage = await provider.fetch_usage(decrypted_key)

                record = UsageRecordModel(
                    id=uuid.uuid4(),
                    key_id=api_key.id,
                    provider=usage.provider,
                    period_start=usage.period_start or date.today(),
                    period_end=usage.period_end or date.today(),
                    calls=usage.calls,
                    tokens_in=usage.tokens_in,
                    tokens_out=usage.tokens_out,
                    cost_estimate=usage.cost_estimate,
                    raw_response=usage.raw_response,
                )
                db.add(record)
                keys_processed += 1
            except Exception:
                # Log failure but continue processing other keys
                pass

        await db.commit()

    return {"status": "ok", "keys_processed": keys_processed}


from app.worker.alert_evaluator import evaluate_alerts

# ARQ settings — functions, cron, and Redis config
class WorkerSettings:
    functions = [fetch_all_usage, evaluate_alerts]
    cron = {
        fetch_all_usage: "*/30 * * * *",    # Fetch usage every 30 min
        evaluate_alerts: "*/15 * * * *",    # Check key health every 15 min
    }
    redis_settings = RedisSettings.from_dsn(app_settings.REDIS_URL)
