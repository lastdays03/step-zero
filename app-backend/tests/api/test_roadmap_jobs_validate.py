import os

import pytest
from httpx import AsyncClient

_skip_no_openai = pytest.mark.skipif(
    not os.environ.get("OPENAI_API_KEY"),
    reason="OPENAI_API_KEY not set",
)


class _MockLLM:
    """Mock LLM that returns a predefined response."""

    def __init__(self, response_text: str):
        self.response_text = response_text

    def invoke(self, _prompt: str) -> "_MockLLMResult":
        return _MockLLMResult(self.response_text)


class _MockLLMResult:
    def __init__(self, content: str):
        self.content = content


class _MockRagService:
    def __init__(self, response_text: str):
        self.response_text = response_text
        self.ready = True
        self.llm = _MockLLM(response_text)

    async def query(self, _question: str) -> str:
        return self.response_text


async def _login_headers(client: AsyncClient) -> dict[str, str]:
    login_response = await client.post(
        "/api/v1/auth/login",
        data={"username": "test@example.com", "password": "password123"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    return {
        "Authorization": f"Bearer {login_data['access_token']}",
        "X-Team-Id": login_data["current_team_id"],
    }


@_skip_no_openai
@pytest.mark.asyncio
async def test_validate_input_success(client: AsyncClient, monkeypatch: pytest.MonkeyPatch):
    mock_service = _MockRagService(
        '{"valid": true, "normalized_business_type": "휴게음식점", '
        '"normalized_location": "서울특별시 강남구", "reason": null, "confidence": 0.95}'
    )
    monkeypatch.setattr(
        "app.features.roadmaps.application.roadmap_generation_service.get_rag_service",
        lambda: mock_service,
    )
    headers = await _login_headers(client)
    response = await client.post(
        "/api/v1/roadmaps/jobs/validate",
        json={
            "business_type": "카페",
            "location": "강남",
            "description": "작은 규모 개인 창업",
        },
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["normalized_business_type"] == "휴게음식점"
    assert data["normalized_location"] == "서울특별시 강남구"


@_skip_no_openai
@pytest.mark.asyncio
async def test_validate_input_invalid(client: AsyncClient, monkeypatch: pytest.MonkeyPatch):
    mock_service = _MockRagService(
        '{"valid": false, "normalized_business_type": null, '
        '"normalized_location": null, "reason": "지역 정보가 모호합니다.", "confidence": 0.4}'
    )
    monkeypatch.setattr(
        "app.features.roadmaps.application.roadmap_generation_service.get_rag_service",
        lambda: mock_service,
    )
    headers = await _login_headers(client)
    response = await client.post(
        "/api/v1/roadmaps/jobs/validate",
        json={
            "business_type": "카페",
            "location": "우리동네",
            "description": "",
        },
        headers=headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert data["reason"] == "지역 정보가 모호합니다."


@_skip_no_openai
@pytest.mark.asyncio
async def test_create_job_blocks_invalid_input(client: AsyncClient, monkeypatch: pytest.MonkeyPatch):
    mock_service = _MockRagService(
        '{"valid": false, "normalized_business_type": null, '
        '"normalized_location": null, "reason": "입력값이 불명확합니다.", "confidence": 0.3}'
    )
    monkeypatch.setattr(
        "app.features.roadmaps.application.roadmap_generation_service.get_rag_service",
        lambda: mock_service,
    )
    headers = await _login_headers(client)
    response = await client.post(
        "/api/v1/roadmaps/jobs",
        json={
            "business_type": "x",
            "location": "y",
            "description": "",
            "goal_horizon_days": 30,
            "experience_level": "BEGINNER",
        },
        headers=headers,
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "입력값이 불명확합니다."
