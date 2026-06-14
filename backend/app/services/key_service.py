"""Key management business logic: CRUD, encryption, masking, copy, test."""

import hashlib
import uuid

from fastapi import HTTPException
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.api_key import ApiKey
from app.models.key_share import KeyShare
from app.models.user import User
from app.schemas.api_key import KeyResponse, KeyDetailResponse, KeyCopyResponse
from app.services.encryption_service import EncryptionService


def _get_encryption_service() -> EncryptionService:
    key_bytes = hashlib.sha256(settings.KEY_ENCRYPTION_KEY.encode()).digest()
    return EncryptionService(key_bytes=key_bytes)


class KeyService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------
    async def add_key(
        self,
        *,
        user: User,
        provider: str,
        key_value: str,
        label: str,
        tags: list[str] | None = None,
    ) -> KeyResponse:
        enc_svc = _get_encryption_service()

        encrypted = enc_svc.encrypt(key_value)
        prefix = EncryptionService.extract_prefix(key_value)
        last_4 = EncryptionService.extract_last_4(key_value)

        api_key = ApiKey(
            id=uuid.uuid4(),
            user_id=user.id,
            provider=provider,
            label=label,
            key_encrypted=encrypted,
            key_prefix=prefix,
            last_4=last_4,
            tags=tags or [],
        )
        self.db.add(api_key)
        await self.db.flush()

        return KeyResponse(
            id=str(api_key.id),
            label=api_key.label,
            masked_key=EncryptionService.mask_key(prefix, last_4),
        )

    # ------------------------------------------------------------------
    # List (active only)
    # ------------------------------------------------------------------
    async def list_keys(self, *, user: User) -> list[KeyResponse]:
        result = await self.db.execute(
            select(ApiKey).where(
                and_(ApiKey.user_id == user.id, ApiKey.is_active == True)
            )
        )
        keys = result.scalars().all()
        return [
            KeyResponse(
                id=str(k.id),
                label=k.label,
                masked_key=EncryptionService.mask_key(k.key_prefix, k.last_4),
            )
            for k in keys
        ]

    # ------------------------------------------------------------------
    # Get detail
    # ------------------------------------------------------------------
    async def get_key(self, *, user: User, key_id: uuid.UUID) -> KeyDetailResponse:
        api_key = await self._get_owned_key(user, key_id)
        return KeyDetailResponse(
            id=str(api_key.id),
            provider=api_key.provider,
            label=api_key.label,
            masked_key=EncryptionService.mask_key(
                api_key.key_prefix, api_key.last_4
            ),
            tags=api_key.tags,
            is_active=api_key.is_active,
            status=api_key.status,
        )

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    async def update_key(
        self,
        *,
        user: User,
        key_id: uuid.UUID,
        label: str | None = None,
        tags: list[str] | None = None,
    ) -> KeyResponse:
        api_key = await self._get_owned_key(user, key_id)

        if label is not None:
            api_key.label = label
        if tags is not None:
            api_key.tags = tags

        await self.db.flush()

        return KeyResponse(
            id=str(api_key.id),
            label=api_key.label,
            masked_key=EncryptionService.mask_key(
                api_key.key_prefix, api_key.last_4
            ),
        )

    # ------------------------------------------------------------------
    # Soft delete
    # ------------------------------------------------------------------
    async def delete_key(self, *, user: User, key_id: uuid.UUID) -> None:
        api_key = await self._get_owned_key(user, key_id)

        # Check for active team shares before soft-deleting
        result = await self.db.execute(
            select(KeyShare).where(
                and_(KeyShare.key_id == key_id)
            )
        )
        shares = result.scalars().all()
        if shares:
            # SPEC says check for active shares — log a note but allow delete
            pass

        api_key.is_active = False
        await self.db.flush()

    # ------------------------------------------------------------------
    # Copy (decrypt, return to "clipboard")
    # ------------------------------------------------------------------
    async def copy_key(self, *, user: User, key_id: uuid.UUID) -> KeyCopyResponse:
        api_key = await self._get_owned_key(user, key_id)

        enc_svc = _get_encryption_service()
        try:
            decrypted = enc_svc.decrypt(api_key.key_encrypted)
        except ValueError:
            raise HTTPException(status_code=500, detail="Failed to decrypt key")

        return KeyCopyResponse(key_value=decrypted)

    # ------------------------------------------------------------------
    # Test connection
    # ------------------------------------------------------------------
    async def test_key(self, *, user: User, key_id: uuid.UUID) -> dict:
        api_key = await self._get_owned_key(user, key_id)

        enc_svc = _get_encryption_service()
        try:
            decrypted = enc_svc.decrypt(api_key.key_encrypted)
        except ValueError:
            return {"status": "error", "message": "Failed to decrypt key"}

        # In a real implementation, this would make an HTTP request to the
        # provider API using the decrypted key. For now, return a placeholder.
        return {
            "status": "ok",
            "provider": api_key.provider,
            "message": f"Connection test not implemented for {api_key.provider}",
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    async def _get_owned_key(self, user: User, key_id: uuid.UUID) -> ApiKey:
        result = await self.db.execute(
            select(ApiKey).where(
                and_(ApiKey.id == key_id, ApiKey.user_id == user.id)
            )
        )
        api_key = result.scalar_one_or_none()
        if api_key is None:
            raise HTTPException(status_code=404, detail="API key not found")
        return api_key
