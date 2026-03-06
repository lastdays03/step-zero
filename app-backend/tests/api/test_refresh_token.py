"""E2E tests for refresh token flow."""

from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import func
from sqlmodel import select

from app.core import security
from app.core import db
from app.models.refresh_token import RefreshToken
from app.models.user import User


async def _get_test_user_id() -> int:
    async with db.async_session() as session:
        result = await session.execute(select(User).where(User.email == "test@example.com"))
        user = result.scalar_one()
        return user.id


async def _count_refresh_tokens(user_id: int) -> int:
    async with db.async_session() as session:
        result = await session.execute(
            select(func.count()).select_from(RefreshToken).where(RefreshToken.user_id == user_id)
        )
        return int(result.scalar_one())


@pytest.mark.asyncio
async def test_login_returns_refresh_token(client: AsyncClient):
    """3-2 prerequisite: Login should return a refresh_token."""
    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "refresh_token" in data
    assert len(data["refresh_token"]) > 20
    assert "access_token" in data


@pytest.mark.asyncio
async def test_refresh_token_returns_new_tokens(client: AsyncClient):
    """3-2: Refresh token should return new access + refresh tokens."""
    # Login first
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    old_refresh = login_data["refresh_token"]
    old_access = login_data["access_token"]

    # Refresh
    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert refresh_resp.status_code == 200
    refresh_data = refresh_resp.json()
    assert "access_token" in refresh_data
    assert "refresh_token" in refresh_data
    # Refresh token must be rotated (new token issued)
    assert refresh_data["refresh_token"] != old_refresh
    # Should include user data
    assert refresh_data["user"]["email"] == "test@example.com"


@pytest.mark.asyncio
async def test_refresh_token_rotation_old_token_revoked(client: AsyncClient):
    """3-2: After rotation, old refresh token should be revoked."""
    # Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    old_refresh = login_resp.json()["refresh_token"]

    # Refresh once (rotates token)
    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert refresh_resp.status_code == 200

    # Try to use old refresh token again (should fail — reuse detection)
    reuse_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert reuse_resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_rotation_creates_single_replacement_row(
    client: AsyncClient,
):
    """Refresh rotation should create exactly one new DB row and link replaced_by."""
    user_id = await _get_test_user_id()
    count_before = await _count_refresh_tokens(user_id)

    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_resp.status_code == 200
    old_refresh = login_resp.json()["refresh_token"]
    old_hash = security.hash_refresh_token(old_refresh)
    assert await _count_refresh_tokens(user_id) == count_before + 1

    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh},
    )
    assert refresh_resp.status_code == 200
    new_refresh = refresh_resp.json()["refresh_token"]
    new_hash = security.hash_refresh_token(new_refresh)

    assert await _count_refresh_tokens(user_id) == count_before + 2

    async with db.async_session() as session:
        result = await session.execute(
            select(RefreshToken).where(RefreshToken.token_hash.in_([old_hash, new_hash]))
        )
        tokens = {token.token_hash: token for token in result.scalars().all()}

    old_token = tokens[old_hash]
    new_token = tokens[new_hash]
    assert old_token.revoked is True
    assert old_token.replaced_by == new_token.id
    assert new_token.revoked is False


@pytest.mark.asyncio
async def test_refresh_with_invalid_token_returns_401(client: AsyncClient):
    """3-2: Invalid refresh token should return 401."""
    resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "completely-invalid-token-xyz"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_dashboard_guest_no_token(client: AsyncClient):
    """3-4: Guest mode (no token) should return 200 with guest data."""
    resp = await client.get("/api/v1/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert data["user_name"] == "Guest"


@pytest.mark.asyncio
async def test_dashboard_expired_token_returns_401(client: AsyncClient):
    """3-2: Expired token on dashboard should return 401 (not guest)."""
    # Create a token that's already expired
    expired_token = security.create_access_token(
        subject="1",
        expires_delta=timedelta(seconds=-10),
    )
    resp = await client.get(
        "/api/v1/dashboard",
        headers={"Authorization": f"Bearer {expired_token}"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_refresh_token(client: AsyncClient):
    """3-5: Explicit logout should revoke refresh token."""
    # Login
    login_resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    refresh_token = login_resp.json()["refresh_token"]

    # Logout
    logout_resp = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token},
    )
    assert logout_resp.status_code == 204

    # Try to use revoked refresh token
    refresh_resp = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 401
