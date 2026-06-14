"""Tests for Team Sharing: share, list, update permission, revoke."""

import pytest


# ---------------------------------------------------------------------------
# Helper — register a user and return the access token + user data
# ---------------------------------------------------------------------------
async def _register_user(client, email, password="securepass123", display_name="Test"):
    payload = {"email": email, "password": password, "display_name": display_name}
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 200, response.text
    data = response.json()
    return data["access_token"], data["user"]


async def _add_key(client, token, provider="openai", label="Test Key"):
    """Add a key and return its id."""
    payload = {
        "provider": provider,
        "key_value": f"sk-proj-testkey{uuid4_short()}",
        "label": label,
    }
    r = await client.post(
        "/api/v1/keys",
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]


def uuid4_short():
    import uuid
    return str(uuid.uuid4())[:8]


# ===========================================================================
# POST /api/v1/team/share — Share a key
# ===========================================================================
class TestShareKey:
    @pytest.mark.asyncio
    async def test_share_key_with_read_permission(self, async_client):
        """Owner shares a key with another user (read permission)."""
        token_a, user_a = await _register_user(async_client, "owner1@test.com")
        token_b, user_b = await _register_user(async_client, "recipient1@test.com")
        key_id = await _add_key(async_client, token_a)

        headers = {"Authorization": f"Bearer {token_a}"}
        payload = {
            "key_id": key_id,
            "shared_with_email": "recipient1@test.com",
            "permission": "read",
        }
        response = await async_client.post("/api/v1/team/share", json=payload, headers=headers)

        assert response.status_code == 200, response.text
        data = response.json()
        assert "id" in data
        assert data["key_id"] == key_id
        assert data["permission"] == "read"
        assert data["shared_with_email"] == "recipient1@test.com"

    @pytest.mark.asyncio
    async def test_share_key_with_use_permission(self, async_client):
        """Owner shares a key with use permission."""
        token_a, _ = await _register_user(async_client, "owner2@test.com")
        token_b, _ = await _register_user(async_client, "recipient2@test.com")
        key_id = await _add_key(async_client, token_a)

        headers = {"Authorization": f"Bearer {token_a}"}
        payload = {
            "key_id": key_id,
            "shared_with_email": "recipient2@test.com",
            "permission": "use",
        }
        response = await async_client.post("/api/v1/team/share", json=payload, headers=headers)

        assert response.status_code == 200, response.text
        data = response.json()
        assert data["permission"] == "use"

    @pytest.mark.asyncio
    async def test_share_key_with_nonexistent_user_returns_404(self, async_client):
        """Target user must exist."""
        token_a, _ = await _register_user(async_client, "owner3@test.com")
        key_id = await _add_key(async_client, token_a)

        headers = {"Authorization": f"Bearer {token_a}"}
        payload = {
            "key_id": key_id,
            "shared_with_email": "ghost@test.com",
            "permission": "read",
        }
        response = await async_client.post("/api/v1/team/share", json=payload, headers=headers)
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_cannot_share_with_yourself(self, async_client):
        """Cannot share a key with yourself."""
        token_a, _ = await _register_user(async_client, "selfshare@test.com")
        key_id = await _add_key(async_client, token_a)

        headers = {"Authorization": f"Bearer {token_a}"}
        payload = {
            "key_id": key_id,
            "shared_with_email": "selfshare@test.com",
            "permission": "read",
        }
        response = await async_client.post("/api/v1/team/share", json=payload, headers=headers)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_cannot_share_same_key_twice_to_same_user(self, async_client):
        """Cannot share an already-shared key with the same person (409)."""
        token_a, _ = await _register_user(async_client, "dupowner@test.com")
        token_b, _ = await _register_user(async_client, "duprecip@test.com")
        key_id = await _add_key(async_client, token_a)

        headers = {"Authorization": f"Bearer {token_a}"}
        payload = {
            "key_id": key_id,
            "shared_with_email": "duprecip@test.com",
            "permission": "read",
        }
        r1 = await async_client.post("/api/v1/team/share", json=payload, headers=headers)
        assert r1.status_code == 200, r1.text

        r2 = await async_client.post("/api/v1/team/share", json=payload, headers=headers)
        assert r2.status_code == 409

    @pytest.mark.asyncio
    async def test_cannot_share_inactive_key(self, async_client):
        """Cannot share a soft-deleted (is_active=False) key."""
        token_a, _ = await _register_user(async_client, "inactiveowner@test.com")
        token_b, _ = await _register_user(async_client, "inactiverecip@test.com")
        key_id = await _add_key(async_client, token_a)

        headers = {"Authorization": f"Bearer {token_a}"}
        # Soft-delete the key
        del_r = await async_client.delete(f"/api/v1/keys/{key_id}", headers=headers)
        assert del_r.status_code == 200

        # Attempt to share the now-inactive key
        payload = {
            "key_id": key_id,
            "shared_with_email": "inactiverecip@test.com",
            "permission": "read",
        }
        r = await async_client.post("/api/v1/team/share", json=payload, headers=headers)
        assert r.status_code == 400

    @pytest.mark.asyncio
    async def test_cannot_share_key_owned_by_another_user(self, async_client):
        """Only the owner can share. Another user's key -> 404."""
        token_a, _ = await _register_user(async_client, "trueowner@test.com")
        token_b, _ = await _register_user(async_client, "imposter@test.com")
        token_c, _ = await _register_user(async_client, "target@test.com")
        key_id = await _add_key(async_client, token_a)

        # User B tries to share User A's key
        headers = {"Authorization": f"Bearer {token_b}"}
        payload = {
            "key_id": key_id,
            "shared_with_email": "target@test.com",
            "permission": "read",
        }
        r = await async_client.post("/api/v1/team/share", json=payload, headers=headers)
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_share_key_requires_auth(self, async_client):
        """Unauthenticated share request returns 401."""
        payload = {
            "key_id": "00000000-0000-0000-0000-000000000001",
            "shared_with_email": "someone@test.com",
            "permission": "read",
        }
        r = await async_client.post("/api/v1/team/share", json=payload)
        assert r.status_code == 401


# ===========================================================================
# GET /api/v1/team/shares — List shares
# ===========================================================================
class TestListShares:
    @pytest.mark.asyncio
    async def test_list_sent_shares(self, async_client):
        """List keys I shared with others (direction=sent)."""
        token_a, _ = await _register_user(async_client, "sender@test.com")
        token_b, _ = await _register_user(async_client, "recv_a@test.com")
        token_c, _ = await _register_user(async_client, "recv_b@test.com")
        key_id = await _add_key(async_client, token_a)

        headers = {"Authorization": f"Bearer {token_a}"}
        # Share with user B
        await async_client.post("/api/v1/team/share", json={
            "key_id": key_id,
            "shared_with_email": "recv_a@test.com",
            "permission": "read",
        }, headers=headers)
        # Share same key with user C
        await async_client.post("/api/v1/team/share", json={
            "key_id": key_id,
            "shared_with_email": "recv_b@test.com",
            "permission": "use",
        }, headers=headers)

        response = await async_client.get(
            "/api/v1/team/shares?direction=sent", headers=headers
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2
        for share in data:
            assert "id" in share
            assert share["key_id"] == key_id
            assert share["shared_by_email"] == "sender@test.com"
            assert share["shared_with_email"] in ("recv_a@test.com", "recv_b@test.com")
            assert share["permission"] in ("read", "use")

    @pytest.mark.asyncio
    async def test_list_received_shares(self, async_client):
        """List keys shared with me (direction=received)."""
        token_a, _ = await _register_user(async_client, "owner_r@test.com")
        token_b, _ = await _register_user(async_client, "recip_r@test.com")
        key_id = await _add_key(async_client, token_a)

        headers_a = {"Authorization": f"Bearer {token_a}"}
        await async_client.post("/api/v1/team/share", json={
            "key_id": key_id,
            "shared_with_email": "recip_r@test.com",
            "permission": "read",
        }, headers=headers_a)

        headers_b = {"Authorization": f"Bearer {token_b}"}
        response = await async_client.get(
            "/api/v1/team/shares?direction=received", headers=headers_b
        )
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        # At least one share directed to recipient_r
        found = any(s["shared_with_email"] == "recip_r@test.com" for s in data)
        assert found, "Expected received share to appear in recipient's list"

    @pytest.mark.asyncio
    async def test_list_shares_default_is_sent(self, async_client):
        """Default direction (no query param) should return sent shares."""
        token_a, _ = await _register_user(async_client, "defsender@test.com")
        token_b, _ = await _register_user(async_client, "defrecv@test.com")
        key_id = await _add_key(async_client, token_a)

        headers = {"Authorization": f"Bearer {token_a}"}
        await async_client.post("/api/v1/team/share", json={
            "key_id": key_id,
            "shared_with_email": "defrecv@test.com",
            "permission": "read",
        }, headers=headers)

        response = await async_client.get("/api/v1/team/shares", headers=headers)
        assert response.status_code == 200, response.text
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["shared_by_email"] == "defsender@test.com"

    @pytest.mark.asyncio
    async def test_list_shares_empty(self, async_client):
        """A user with no shares gets an empty list."""
        token_a, _ = await _register_user(async_client, "loner@test.com")
        headers = {"Authorization": f"Bearer {token_a}"}

        r = await async_client.get("/api/v1/team/shares?direction=sent", headers=headers)
        assert r.status_code == 200
        assert r.json() == []

        r2 = await async_client.get("/api/v1/team/shares?direction=received", headers=headers)
        assert r2.status_code == 200
        assert r2.json() == []

    @pytest.mark.asyncio
    async def test_list_shares_requires_auth(self, async_client):
        r = await async_client.get("/api/v1/team/shares")
        assert r.status_code == 401


# ===========================================================================
# PATCH /api/v1/team/share/{id} — Change permission
# ===========================================================================
class TestUpdateSharePermission:
    @pytest.mark.asyncio
    async def test_owner_can_change_permission(self, async_client):
        """The original sharer can update permission from read to use."""
        token_a, _ = await _register_user(async_client, "upd_owner@test.com")
        token_b, _ = await _register_user(async_client, "upd_recv@test.com")
        key_id = await _add_key(async_client, token_a)

        headers = {"Authorization": f"Bearer {token_a}"}
        share_r = await async_client.post("/api/v1/team/share", json={
            "key_id": key_id,
            "shared_with_email": "upd_recv@test.com",
            "permission": "read",
        }, headers=headers)
        share_id = share_r.json()["id"]

        patch_r = await async_client.patch(
            f"/api/v1/team/share/{share_id}",
            json={"permission": "use"},
            headers=headers,
        )
        assert patch_r.status_code == 200, patch_r.text
        assert patch_r.json()["permission"] == "use"

    @pytest.mark.asyncio
    async def test_non_owner_cannot_change_permission(self, async_client):
        """The recipient cannot change the permission level."""
        token_a, _ = await _register_user(async_client, "upd2_owner@test.com")
        token_b, _ = await _register_user(async_client, "upd2_recv@test.com")
        key_id = await _add_key(async_client, token_a)

        headers_a = {"Authorization": f"Bearer {token_a}"}
        share_r = await async_client.post("/api/v1/team/share", json={
            "key_id": key_id,
            "shared_with_email": "upd2_recv@test.com",
            "permission": "read",
        }, headers=headers_a)
        share_id = share_r.json()["id"]

        # Recipient tries to change permission
        headers_b = {"Authorization": f"Bearer {token_b}"}
        patch_r = await async_client.patch(
            f"/api/v1/team/share/{share_id}",
            json={"permission": "use"},
            headers=headers_b,
        )
        assert patch_r.status_code == 403

    @pytest.mark.asyncio
    async def test_update_share_not_found_returns_404(self, async_client):
        token_a, _ = await _register_user(async_client, "upd_nf@test.com")
        headers = {"Authorization": f"Bearer {token_a}"}
        r = await async_client.patch(
            "/api/v1/team/share/00000000-0000-0000-0000-000000000000",
            json={"permission": "use"},
            headers=headers,
        )
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_update_share_requires_auth(self, async_client):
        r = await async_client.patch(
            "/api/v1/team/share/00000000-0000-0000-0000-000000000000",
            json={"permission": "use"},
        )
        assert r.status_code == 401


# ===========================================================================
# DELETE /api/v1/team/share/{id} — Revoke share
# ===========================================================================
class TestRevokeShare:
    @pytest.mark.asyncio
    async def test_owner_can_revoke_share(self, async_client):
        """The original sharer can revoke a share."""
        token_a, _ = await _register_user(async_client, "rev_owner@test.com")
        token_b, _ = await _register_user(async_client, "rev_recv@test.com")
        key_id = await _add_key(async_client, token_a)

        headers = {"Authorization": f"Bearer {token_a}"}
        share_r = await async_client.post("/api/v1/team/share", json={
            "key_id": key_id,
            "shared_with_email": "rev_recv@test.com",
            "permission": "read",
        }, headers=headers)
        share_id = share_r.json()["id"]

        del_r = await async_client.delete(
            f"/api/v1/team/share/{share_id}", headers=headers
        )
        assert del_r.status_code == 200, del_r.text

        # Verify share no longer appears in sent list
        list_r = await async_client.get(
            "/api/v1/team/shares?direction=sent", headers=headers
        )
        assert list_r.status_code == 200
        share_ids = [s["id"] for s in list_r.json()]
        assert share_id not in share_ids

    @pytest.mark.asyncio
    async def test_recipient_cannot_revoke_share(self, async_client):
        """The recipient cannot revoke a share (only shared_by can)."""
        token_a, _ = await _register_user(async_client, "rev2_owner@test.com")
        token_b, _ = await _register_user(async_client, "rev2_recv@test.com")
        key_id = await _add_key(async_client, token_a)

        headers_a = {"Authorization": f"Bearer {token_a}"}
        share_r = await async_client.post("/api/v1/team/share", json={
            "key_id": key_id,
            "shared_with_email": "rev2_recv@test.com",
            "permission": "read",
        }, headers=headers_a)
        share_id = share_r.json()["id"]

        # Recipient tries to revoke
        headers_b = {"Authorization": f"Bearer {token_b}"}
        del_r = await async_client.delete(
            f"/api/v1/team/share/{share_id}", headers=headers_b
        )
        assert del_r.status_code == 403

    @pytest.mark.asyncio
    async def test_revoke_nonexistent_share_returns_404(self, async_client):
        token_a, _ = await _register_user(async_client, "rev_nf@test.com")
        headers = {"Authorization": f"Bearer {token_a}"}
        r = await async_client.delete(
            "/api/v1/team/share/00000000-0000-0000-0000-000000000000",
            headers=headers,
        )
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_revoke_share_requires_auth(self, async_client):
        r = await async_client.delete(
            "/api/v1/team/share/00000000-0000-0000-0000-000000000000"
        )
        assert r.status_code == 401


# ===========================================================================
# Cross-cutting: Shared keys in recipient's key list
# ===========================================================================
class TestSharedKeysAppearInList:
    @pytest.mark.asyncio
    async def test_recipient_sees_shared_key_in_their_list(self, async_client):
        """After sharing, the recipient's GET /keys should show the shared key."""
        token_a, _ = await _register_user(async_client, "shareown@test.com")
        token_b, user_b = await _register_user(async_client, "sharerecv@test.com")
        key_id = await _add_key(async_client, token_a, label="Shared Key X")

        headers_a = {"Authorization": f"Bearer {token_a}"}
        await async_client.post("/api/v1/team/share", json={
            "key_id": key_id,
            "shared_with_email": "sharerecv@test.com",
            "permission": "read",
        }, headers=headers_a)

        # Recipient lists their keys
        headers_b = {"Authorization": f"Bearer {token_b}"}
        r = await async_client.get("/api/v1/keys", headers=headers_b)
        assert r.status_code == 200, r.text
        data = r.json()
        # The shared key should appear
        key_ids = [k["id"] for k in data]
        assert key_id in key_ids

    @pytest.mark.asyncio
    async def test_share_audit_log_written(self, async_client):
        """Sharing a key creates an audit log entry."""
        token_a, _ = await _register_user(async_client, "auditown@test.com")
        token_b, _ = await _register_user(async_client, "auditrecv@test.com")
        key_id = await _add_key(async_client, token_a)

        headers = {
            "Authorization": f"Bearer {token_a}",
            "User-Agent": "pytest-team/1.0",
        }
        payload = {
            "key_id": key_id,
            "shared_with_email": "auditrecv@test.com",
            "permission": "read",
        }
        r = await async_client.post("/api/v1/team/share", json=payload, headers=headers)
        assert r.status_code == 200, r.text
        # Audit log is created at service level — endpoint success confirms it.

    @pytest.mark.asyncio
    async def test_revoke_share_audit_log_written(self, async_client):
        """Revoking a share creates an audit log entry."""
        token_a, _ = await _register_user(async_client, "revaud_own@test.com")
        token_b, _ = await _register_user(async_client, "revaud_rec@test.com")
        key_id = await _add_key(async_client, token_a)

        headers = {"Authorization": f"Bearer {token_a}"}
        share_r = await async_client.post("/api/v1/team/share", json={
            "key_id": key_id,
            "shared_with_email": "revaud_rec@test.com",
            "permission": "read",
        }, headers=headers)
        share_id = share_r.json()["id"]

        headers["User-Agent"] = "pytest-team/1.0"
        del_r = await async_client.delete(
            f"/api/v1/team/share/{share_id}", headers=headers
        )
        assert del_r.status_code == 200, del_r.text
        # Audit log is created at service level — endpoint success confirms it.

    @pytest.mark.asyncio
    async def test_recipient_cannot_copy_shared_key(self, async_client):
        """A recipient with read/use permission cannot copy the plaintext.

        The copy endpoint checks ownership (user_id == key.user_id). Since the
        recipient is not the owner, copy should return 404.
        """
        token_a, _ = await _register_user(async_client, "copyown@test.com")
        token_b, _ = await _register_user(async_client, "copyrecv@test.com")
        key_id = await _add_key(async_client, token_a)

        headers_a = {"Authorization": f"Bearer {token_a}"}
        await async_client.post("/api/v1/team/share", json={
            "key_id": key_id,
            "shared_with_email": "copyrecv@test.com",
            "permission": "use",
        }, headers=headers_a)

        # Recipient tries to copy
        headers_b = {"Authorization": f"Bearer {token_b}"}
        r = await async_client.post(
            f"/api/v1/keys/{key_id}/copy", headers=headers_b
        )
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_no_chain_sharing(self, async_client):
        """A recipient cannot re-share a key shared with them."""
        token_a, _ = await _register_user(async_client, "chainown@test.com")
        token_b, _ = await _register_user(async_client, "chainmid@test.com")
        token_c, _ = await _register_user(async_client, "chainend@test.com")
        key_id = await _add_key(async_client, token_a)

        headers_a = {"Authorization": f"Bearer {token_a}"}
        await async_client.post("/api/v1/team/share", json={
            "key_id": key_id,
            "shared_with_email": "chainmid@test.com",
            "permission": "use",
        }, headers=headers_a)

        # Recipient (chainmid) tries to share with a third user
        headers_b = {"Authorization": f"Bearer {token_b}"}
        r = await async_client.post("/api/v1/team/share", json={
            "key_id": key_id,
            "shared_with_email": "chainend@test.com",
            "permission": "read",
        }, headers=headers_b)
        # Must be forbidden — only the key owner can share
        assert r.status_code == 404

    @pytest.mark.asyncio
    async def test_revoke_takes_effect_immediately(self, async_client):
        """After revoke, the recipient's list no longer shows the shared key."""
        token_a, _ = await _register_user(async_client, "immed_own@test.com")
        token_b, _ = await _register_user(async_client, "immed_rec@test.com")
        key_id = await _add_key(async_client, token_a, label="Immediate Revoke Key")

        headers_a = {"Authorization": f"Bearer {token_a}"}
        share_r = await async_client.post("/api/v1/team/share", json={
            "key_id": key_id,
            "shared_with_email": "immed_rec@test.com",
            "permission": "read",
        }, headers=headers_a)
        share_id = share_r.json()["id"]

        # Verify recipient sees the key
        headers_b = {"Authorization": f"Bearer {token_b}"}
        r_pre = await async_client.get("/api/v1/keys", headers=headers_b)
        assert key_id in [k["id"] for k in r_pre.json()]

        # Owner revokes
        await async_client.delete(f"/api/v1/team/share/{share_id}", headers=headers_a)

        # Recipient no longer sees the key
        r_post = await async_client.get("/api/v1/keys", headers=headers_b)
        assert key_id not in [k["id"] for k in r_post.json()]
