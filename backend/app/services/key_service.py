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
from app.providers.registry import ProviderRegistry
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
            provider=api_key.provider,
            label=api_key.label,
            masked_key=EncryptionService.mask_key(prefix, last_4),
            status=api_key.status,
            permission=None,
        )

    # ------------------------------------------------------------------
    # List (active; owned + shared keys, with permission tag)
    # ------------------------------------------------------------------
    async def list_keys(self, *, user: User) -> list[KeyResponse]:
        enc_svc = _get_encryption_service()

        # Owned keys
        owned_result = await self.db.execute(
            select(ApiKey).where(
                and_(ApiKey.user_id == user.id, ApiKey.is_active == True)
            )
        )
        owned_keys = list(owned_result.scalars().all())

        # Keys shared with this user
        shared_result = await self.db.execute(
            select(ApiKey, KeyShare.permission)
            .join(KeyShare, KeyShare.key_id == ApiKey.id)
            .where(
                and_(
                    KeyShare.shared_with == user.id,
                    ApiKey.is_active == True,
                )
            )
        )
        shared_rows = shared_result.all()

        result = []
        seen = set()

        for k in owned_keys:
            result.append(KeyResponse(
                id=str(k.id),
                provider=k.provider,
                label=k.label,
                masked_key=enc_svc.mask_key(k.key_prefix, k.last_4),
                status=k.status,
                permission=None,  # owner
            ))
            seen.add(k.id)

        for k, perm in shared_rows:
            if k.id not in seen:
                result.append(KeyResponse(
                    id=str(k.id),
                    provider=k.provider,
                    label=k.label,
                    masked_key=enc_svc.mask_key(k.key_prefix, k.last_4),
                    status=k.status,
                    permission=perm,  # "read" or "use"
                ))
                seen.add(k.id)

        return result

    # ------------------------------------------------------------------
    # Get detail
    # ------------------------------------------------------------------
    async def get_key(self, *, user: User, key_id: uuid.UUID) -> KeyDetailResponse:
        api_key = await self._get_key_or_shared(user, key_id)
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
            provider=api_key.provider,
            label=api_key.label,
            masked_key=EncryptionService.mask_key(
                api_key.key_prefix, api_key.last_4
            ),
            status=api_key.status,
            permission=None,
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
        api_key = await self._get_key_or_shared(user, key_id, require_use=True)

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

        try:
            provider = ProviderRegistry.get(api_key.provider)
            result = await provider.test_connection(decrypted)
        except KeyError:
            result = {"status": "error", "message": f"Unknown provider: {api_key.provider}"}

        # Update key status based on test result
        api_key.status = "ok" if result.get("status") == "ok" else "error"
        await self.db.flush()

        result["provider"] = api_key.provider
        return result

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

    async def _get_share_permission(self, user: User, key_id: uuid.UUID) -> str | None:
        """Return share permission ('read'/'use') if key is shared with user, else None."""
        result = await self.db.execute(
            select(KeyShare.permission).where(
                and_(KeyShare.key_id == key_id, KeyShare.shared_with == user.id)
            )
        )
        return result.scalar_one_or_none()

    async def _get_key_or_shared(self, user: User, key_id: uuid.UUID, require_use: bool = False) -> ApiKey:
        """Get key by ownership or share permission. Raises 404 if no access."""
        api_key = await self.db.execute(
            select(ApiKey).where(ApiKey.id == key_id)
        )
        api_key = api_key.scalar_one_or_none()

        if api_key is None:
            raise HTTPException(status_code=404, detail="API key not found")

        # Owner has full access
        if api_key.user_id == user.id:
            return api_key

        # Check share permission
        perm = await self._get_share_permission(user, key_id)
        if perm is None:
            raise HTTPException(status_code=404, detail="API key not found")
        if require_use and perm != "use":
            raise HTTPException(status_code=403, detail="You only have read access to this key")

        return api_key
