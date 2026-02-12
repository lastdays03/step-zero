
import pytest
from unittest.mock import AsyncMock
from app.services.rag.service import RagService

@pytest.mark.asyncio
async def test_rag_service_initialization():
    service = RagService()
    assert service is not None

@pytest.mark.asyncio
async def test_rag_service_query():
    mock_chain = AsyncMock()
    mock_chain.ainvoke.return_value = {"answer": "테스트 답변"}
    
    # 의존성 주입 (Dependency Injection)을 통해 Mock Chain 사용
    service = RagService(chain=mock_chain)
    response = await service.query("질문")
    
    assert response == "테스트 답변"
    mock_chain.ainvoke.assert_called_once()
