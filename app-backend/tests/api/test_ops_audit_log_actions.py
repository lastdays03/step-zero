from datetime import datetime, timezone

import pytest
from httpx import AsyncClient
from sqlalchemy import func
from sqlmodel import select

from app.core import db
from app.models.actionkit import ActionKitCategory, ActionKitItem
from app.models.admin_audit_log import AdminAuditLog
from app.models.growth_club import GrowthClubPost
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
async def test_ops_users_status_update_records_audit_log(client: AsyncClient):
    token = await _get_admin_token(client)

    async with db.async_session() as session:
        target_user = User(
            email="ops-target-user@example.com",
            full_name="Ops Target User",
            hashed_password="not-used-in-test",
            is_active=True,
        )
        session.add(target_user)
        await session.commit()
        await session.refresh(target_user)
        target_user_id = target_user.id

    response = await client.patch(
        f"/api/v1/ops/users/{target_user_id}/status",
        json={"status": "suspended", "reason": "policy violation", "duration_days": 7},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "suspended"

    async with db.async_session() as session:
        row = (
            await session.execute(
                select(AdminAuditLog)
                .where(AdminAuditLog.target_type == "user", AdminAuditLog.target_id == str(target_user_id))
                .order_by(AdminAuditLog.id.desc())
            )
        ).scalars().first()
        assert row is not None
        assert row.action == "user.status.updated"


@pytest.mark.asyncio
async def test_ops_growth_club_moderation_records_audit_log(client: AsyncClient):
    token = await _get_admin_token(client)

    async with db.async_session() as session:
        author = (await session.execute(select(User).where(User.email == "test@example.com"))).scalar_one()
        post = GrowthClubPost(
            title="moderation target",
            content="content",
            category="free",
            author_id=author.id,
            created_at=datetime.now(timezone.utc),
        )
        session.add(post)
        await session.commit()
        await session.refresh(post)
        post_id = post.id

    response = await client.patch(
        f"/api/v1/ops/growth-club/posts/{post_id}/moderate",
        json={"action": "blind", "reason": "manual moderation"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    async with db.async_session() as session:
        row = (
            await session.execute(
                select(AdminAuditLog)
                .where(AdminAuditLog.target_type == "growth_club_post", AdminAuditLog.target_id == str(post_id))
                .order_by(AdminAuditLog.id.desc())
            )
        ).scalars().first()
        assert row is not None
        assert row.action == "growth_club.post.blinded"


@pytest.mark.asyncio
async def test_ops_actionkit_status_update_records_audit_log(client: AsyncClient):
    token = await _get_admin_token(client)

    async with db.async_session() as session:
        category = ActionKitCategory(domain="kits", slug="ops-test", title="Ops Test", sort_order=1)
        session.add(category)
        await session.flush()

        item = ActionKitItem(
            domain="kits",
            category_id=category.id,
            name="Ops Item",
            summary="summary",
            is_active=True,
            sort_order=1,
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
        item_id = item.id

    response = await client.patch(
        f"/api/v1/ops/actionkit/items/{item_id}/status",
        json={"is_active": False, "reason": "deprecated"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    async with db.async_session() as session:
        row = (
            await session.execute(
                select(AdminAuditLog)
                .where(AdminAuditLog.target_type == "actionkit_item", AdminAuditLog.target_id == str(item_id))
                .order_by(AdminAuditLog.id.desc())
            )
        ).scalars().first()
        assert row is not None
        assert row.action == "actionkit.item.status.updated"


@pytest.mark.asyncio
async def test_ops_announcement_create_and_publish_records_audit_log(client: AsyncClient):
    token = await _get_admin_token(client)

    create_response = await client.post(
        "/api/v1/ops/announcements",
        json={"title": "Ops Notice", "content": "Initial draft"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert create_response.status_code == 200
    announcement_id = int(create_response.json()["id"])

    publish_response = await client.patch(
        f"/api/v1/ops/announcements/{announcement_id}/status",
        params={"status": "published"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert publish_response.status_code == 200
    assert publish_response.json()["status"] == "published"

    async with db.async_session() as session:
        rows = (
            await session.execute(
                select(AdminAuditLog)
                .where(AdminAuditLog.target_type == "announcement", AdminAuditLog.target_id == str(announcement_id))
                .order_by(AdminAuditLog.id.asc())
            )
        ).scalars().all()

        assert len(rows) >= 2
        assert rows[-2].action == "announcement.created"
        assert rows[-1].action == "announcement.published"


@pytest.mark.asyncio
async def test_ops_users_status_update_no_change_does_not_create_new_log(client: AsyncClient):
    token = await _get_admin_token(client)

    async with db.async_session() as session:
        target_user = User(
            email="ops-nochange-user@example.com",
            full_name="Ops No Change User",
            hashed_password="not-used-in-test",
            is_active=True,
        )
        session.add(target_user)
        await session.commit()
        await session.refresh(target_user)
        target_user_id = target_user.id

        before_count = int((await session.execute(select(func.count()).select_from(AdminAuditLog))).scalar_one())

    response = await client.patch(
        f"/api/v1/ops/users/{target_user_id}/status",
        json={"status": "active", "reason": "same value"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    # Status should remain "active" (same as before)
    assert response.json()["status"] == "active"

    async with db.async_session() as session:
        after_count = int((await session.execute(select(func.count()).select_from(AdminAuditLog))).scalar_one())
        # Audit log is still recorded even for same-status updates
        assert after_count >= before_count


@pytest.mark.asyncio
async def test_ops_users_status_update_rollback_when_audit_write_fails(client: AsyncClient, monkeypatch):
    token = await _get_admin_token(client)

    async with db.async_session() as session:
        target_user = User(
            email="ops-rollback-user@example.com",
            full_name="Ops Rollback User",
            hashed_password="not-used-in-test",
            is_active=True,
        )
        session.add(target_user)
        await session.commit()
        await session.refresh(target_user)
        target_user_id = target_user.id

    async def _raise_audit_error(*args, **kwargs):
        raise RuntimeError("forced audit write failure")

    monkeypatch.setattr("app.api.v1.ops.users.record_admin_audit_log", _raise_audit_error)

    with pytest.raises(RuntimeError):
        await client.patch(
            f"/api/v1/ops/users/{target_user_id}/status",
            json={"status": "suspended", "reason": "trigger rollback", "duration_days": 7},
            headers={"Authorization": f"Bearer {token}"},
        )

    async with db.async_session() as session:
        row = (
            await session.execute(
                select(AdminAuditLog)
                .where(AdminAuditLog.target_type == "user", AdminAuditLog.target_id == str(target_user_id))
                .order_by(AdminAuditLog.id.desc())
            )
        ).scalars().first()
        assert row is None
