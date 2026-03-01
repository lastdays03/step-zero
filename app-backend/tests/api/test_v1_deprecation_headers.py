import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_v1_endpoints_do_not_include_deprecation_headers(client: AsyncClient):
    response = await client.get("/api/v1/dashboard")

    assert response.status_code == 200
    assert response.headers.get("Deprecation") is None
    assert response.headers.get("Sunset") is None
    assert response.headers.get("Link") is None
    assert response.headers.get("Warning") is None
