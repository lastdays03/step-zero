import pytest
from httpx import AsyncClient
from sqlmodel import select

from app.core import db
from app.features.ops.application.audit_logs import record_admin_audit_log
from app.models.user import User


async def _get_admin_token(client: AsyncClient) -> str:
    async with db.async_session() as session:
        user = (await session.execute(select(User).where(User.email == "test@example.com"))).scalar_one()
        user.is_superuser = True
        user.is_active = True
        session.add(user)
        await session.commit()

    response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.mark.asyncio
async def test_ops_audit_logs_list_with_filter(client: AsyncClient):
    token = await _get_admin_token(client)

    async with db.async_session() as session:
        admin = (await session.execute(select(User).where(User.email == "test@example.com"))).scalar_one()
        await record_admin_audit_log(
            session,
            admin_id=admin.id,
            action="user.status.updated",
            target_type="user",
            target_id="1",
            reason="manual review",
            meta={"before": {"is_active": True}, "after": {"is_active": False}},
        )
        await record_admin_audit_log(
            session,
            admin_id=admin.id,
            action="announcement.published",
            target_type="announcement",
            target_id="42",
            meta={"after": {"status": "published"}},
        )
        await session.commit()

    response = await client.get(
        "/api/v1/ops/audit-logs",
        params={"action": "user.status.updated", "page": 1, "size": 10},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 1
    assert payload["page"] == 1
    assert payload["size"] == 10
    assert len(payload["items"]) >= 1

    item = payload["items"][0]
    assert item["action"] == "user.status.updated"
    assert item["target_type"] == "user"
    assert "meta" in item


@pytest.mark.asyncio
async def test_ops_audit_logs_mask_sensitive_meta(client: AsyncClient):
    token = await _get_admin_token(client)

    async with db.async_session() as session:
        admin = (await session.execute(select(User).where(User.email == "test@example.com"))).scalar_one()
        await record_admin_audit_log(
            session,
            admin_id=admin.id,
            action="user.status.updated",
            target_type="user",
            target_id="1",
            reason="sensitive check",
            meta={
                "before": {"password": "raw-password"},
                "after": {"is_active": False},
                "access_token": "raw-token",
            },
        )
        await session.commit()

    response = await client.get(
        "/api/v1/ops/audit-logs",
        params={"action": "user.status.updated", "page": 1, "size": 10},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["meta"]["before"]["password"] == "[REDACTED]"
    assert item["meta"]["access_token"] == "[REDACTED]"


@pytest.mark.asyncio
async def test_ops_audit_logs_filter_accepts_naive_datetime_as_utc(client: AsyncClient):
    token = await _get_admin_token(client)

    response = await client.get(
        "/api/v1/ops/audit-logs",
        params={"from": "2026-02-23T00:00:00", "to": "2026-02-23T23:59:59", "page": 1, "size": 10},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
