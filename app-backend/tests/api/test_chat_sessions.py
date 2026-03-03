"""통합 챗봇 세션 CRUD API 테스트.

POST /api/v1/chat/sessions — 세션 생성
GET  /api/v1/chat/sessions — 세션 목록
PATCH /api/v1/chat/sessions/{id} — 제목 변경
DELETE /api/v1/chat/sessions/{id} — 소프트 삭제
GET /api/v1/chat/sessions/{id}/messages — 메시지 목록

라우터(A-6)가 등록된 후 활성화된다.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from httpx import AsyncClient

from app.core import db
from app.models.team import Team, TeamMember
from app.models.user import User
from sqlmodel import select

# 라우터 등록 전이면 전체 skip
_CHAT_ROUTER_PATH = (
    Path(__file__).parents[2] / "app" / "api" / "v1" / "chat"
)
pytestmark = pytest.mark.skipif(
    not _CHAT_ROUTER_PATH.exists(),
    reason="chat router not yet created (A-6 pending)",
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_BASE = "/api/v1/chat"


async def _login_headers(client: AsyncClient) -> dict[str, str]:
    resp = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert resp.status_code == 200
    data = resp.json()
    return {
        "Authorization": f"Bearer {data['access_token']}",
        "X-Team-Id": data["current_team_id"],
    }


async def _create_session(client: AsyncClient, headers: dict) -> str:
    """세션 생성 후 ID 반환."""
    resp = await client.post(
        f"{_BASE}/sessions", json={}, headers=headers
    )
    assert resp.status_code == 201
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# 비인증 요청 → 401
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sessions_list_unauthenticated(client: AsyncClient) -> None:
    resp = await client.get(f"{_BASE}/sessions")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_sessions_create_unauthenticated(client: AsyncClient) -> None:
    resp = await client.post(f"{_BASE}/sessions", json={})
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# 세션 생성
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_session(client: AsyncClient) -> None:
    headers = await _login_headers(client)
    resp = await client.post(f"{_BASE}/sessions", json={}, headers=headers)

    assert resp.status_code == 201
    data = resp.json()
    assert "id" in data
    assert data["message_count"] == 0
    assert data["title"] is None


# ---------------------------------------------------------------------------
# 세션 목록
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_sessions(client: AsyncClient) -> None:
    headers = await _login_headers(client)

    # 세션 생성 후 목록 조회
    await _create_session(client, headers)

    resp = await client.get(f"{_BASE}/sessions", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "sessions" in data
    assert isinstance(data["sessions"], list)
    assert len(data["sessions"]) >= 1
    assert "total" in data


# ---------------------------------------------------------------------------
# 세션 제목 수정
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_session_title(client: AsyncClient) -> None:
    headers = await _login_headers(client)
    session_id = await _create_session(client, headers)

    resp = await client.patch(
        f"{_BASE}/sessions/{session_id}",
        json={"title": "새 제목"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["title"] == "새 제목"


@pytest.mark.asyncio
async def test_update_session_title_empty_rejected(
    client: AsyncClient,
) -> None:
    headers = await _login_headers(client)
    session_id = await _create_session(client, headers)

    resp = await client.patch(
        f"{_BASE}/sessions/{session_id}",
        json={"title": ""},
        headers=headers,
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# 세션 삭제
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_session(client: AsyncClient) -> None:
    headers = await _login_headers(client)
    session_id = await _create_session(client, headers)

    resp = await client.delete(
        f"{_BASE}/sessions/{session_id}", headers=headers
    )
    assert resp.status_code == 204

    # 삭제된 세션의 메시지 조회 시 404
    msg_resp = await client.get(
        f"{_BASE}/sessions/{session_id}/messages", headers=headers
    )
    assert msg_resp.status_code == 404


@pytest.mark.asyncio
async def test_delete_nonexistent_session(client: AsyncClient) -> None:
    headers = await _login_headers(client)
    fake_id = "00000000-0000-0000-0000-000000000000"

    resp = await client.delete(
        f"{_BASE}/sessions/{fake_id}", headers=headers
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# 메시지 조회 (빈 세션)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_messages_empty(client: AsyncClient) -> None:
    headers = await _login_headers(client)
    session_id = await _create_session(client, headers)

    resp = await client.get(
        f"{_BASE}/sessions/{session_id}/messages", headers=headers
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["messages"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_get_messages_nonexistent_session(
    client: AsyncClient,
) -> None:
    headers = await _login_headers(client)
    fake_id = "00000000-0000-0000-0000-000000000000"

    resp = await client.get(
        f"{_BASE}/sessions/{fake_id}/messages", headers=headers
    )
    assert resp.status_code == 404
