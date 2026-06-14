"""Team sharing business logic: share, list, update permission, revoke."""

import uuid

from fastapi import HTTPException
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.api_key import ApiKey
from app.models.key_share import KeyShare
from app.models.user import User
from app.schemas.team import ShareResponse


class TeamService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ------------------------------------------------------------------
    # Share a key
    # ------------------------------------------------------------------
    async def share_key(
        self,
        *,
        user: User,
        key_id: uuid.UUID,
        shared_with_email: str,
        permission: str,
    ) -> ShareResponse:
        # 1. Find target user by email
        result = await self.db.execute(
            select(User).where(User.email == shared_with_email)
        )
        target_user = result.scalar_one_or_none()
        if target_user is None:
            raise HTTPException(status_code=404, detail="Target user not found")

        # 2. Cannot share with yourself
        if target_user.id == user.id:
            raise HTTPException(status_code=400, detail="Cannot share a key with yourself")

        # 3. Verify key exists, is active, and is owned by the current user
        result = await self.db.execute(
            select(ApiKey).where(ApiKey.id == key_id)
        )
        api_key = result.scalar_one_or_none()
        if api_key is None:
            raise HTTPException(status_code=404, detail="API key not found")

        if api_key.user_id != user.id:
            raise HTTPException(status_code=404, detail="API key not found")

        if not api_key.is_active:
            raise HTTPException(status_code=400, detail="Cannot share an inactive key")

        # 4. Check for existing share (no duplicates)
        result = await self.db.execute(
            select(KeyShare).where(
                and_(
                    KeyShare.key_id == key_id,
                    KeyShare.shared_with == target_user.id,
                )
            )
        )
        existing = result.scalar_one_or_none()
        if existing is not None:
            raise HTTPException(
                status_code=409,
                detail="This key is already shared with this user",
            )

        # 5. Look up key info for the response
        result = await self.db.execute(select(ApiKey).where(ApiKey.id == key_id))
        api_key = result.scalar_one_or_none()

        # 6. Create the share
        share = KeyShare(
            id=uuid.uuid4(),
            key_id=key_id,
            shared_by=user.id,
            shared_with=target_user.id,
            permission=permission,
        )
        self.db.add(share)
        await self.db.flush()

        return ShareResponse(
            id=str(share.id),
            key_id=str(share.key_id),
            key_label=api_key.label if api_key else "unknown",
            key_provider=api_key.provider if api_key else "unknown",
            masked_key=f"{api_key.key_prefix}...****{api_key.last_4}" if api_key else "unknown",
            shared_by_email=user.email,
            shared_with_email=target_user.email,
            permission=share.permission,
        )

    # ------------------------------------------------------------------
    # List shares
    # ------------------------------------------------------------------
    async def list_shares(
        self,
        *,
        user: User,
        direction: str = "sent",
    ) -> list[ShareResponse]:
        if direction == "sent":
            # Keys I shared with others
            result = await self.db.execute(
                select(KeyShare).where(KeyShare.shared_by == user.id)
            )
            shares = result.scalars().all()
        elif direction == "received":
            # Keys shared with me
            result = await self.db.execute(
                select(KeyShare).where(KeyShare.shared_with == user.id)
            )
            shares = result.scalars().all()
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid direction. Use 'sent' or 'received'.",
            )

        return [
            await self._to_share_response(share) for share in shares
        ]

    # ------------------------------------------------------------------
    # Update share permission
    # ------------------------------------------------------------------
    async def update_permission(
        self,
        *,
        user: User,
        share_id: uuid.UUID,
        permission: str,
    ) -> ShareResponse:
        share = await self._get_share_for_owner(user, share_id)
        share.permission = permission
        await self.db.flush()

        return await self._to_share_response(share)

    # ------------------------------------------------------------------
    # Revoke a share
    # ------------------------------------------------------------------
    async def revoke_share(
        self,
        *,
        user: User,
        share_id: uuid.UUID,
    ) -> None:
        share = await self._get_share_for_owner(user, share_id)
        await self.db.delete(share)
        await self.db.flush()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    async def _get_share_for_owner(
        self, user: User, share_id: uuid.UUID
    ) -> KeyShare:
        result = await self.db.execute(
            select(KeyShare).where(KeyShare.id == share_id)
        )
        share = result.scalar_one_or_none()
        if share is None:
            raise HTTPException(status_code=404, detail="Share not found")

        if share.shared_by != user.id:
            raise HTTPException(
                status_code=403,
                detail="Only the user who created the share can modify it",
            )

        return share

    async def _to_share_response(self, share: KeyShare) -> ShareResponse:
        # Resolve user emails
        result = await self.db.execute(
            select(User).where(User.id == share.shared_by)
        )
        shared_by_user = result.scalar_one_or_none()

        result = await self.db.execute(
            select(User).where(User.id == share.shared_with)
        )
        shared_with_user = result.scalar_one_or_none()

        # Resolve key info
        result = await self.db.execute(
            select(ApiKey).where(ApiKey.id == share.key_id)
        )
        api_key = result.scalar_one_or_none()

        return ShareResponse(
            id=str(share.id),
            key_id=str(share.key_id),
            key_label=api_key.label if api_key else "unknown",
            key_provider=api_key.provider if api_key else "unknown",
            masked_key=f"{api_key.key_prefix}...****{api_key.last_4}" if api_key else "unknown",
            shared_by_email=shared_by_user.email if shared_by_user else "unknown",
            shared_with_email=shared_with_user.email if shared_with_user else "unknown",
            permission=share.permission,
        )
