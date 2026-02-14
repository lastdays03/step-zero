from unittest.mock import Mock

import pytest

from app.services.rag.service import RagService


@pytest.mark.asyncio
async def test_rag_service_query_uses_chain_invoke() -> None:
    service = RagService.__new__(RagService)
    service.ready = True
    service.chain = Mock()
    service.chain.invoke.return_value = "테스트 답변"

    response = await service.query("질문")

    assert response == "테스트 답변"
    service.chain.invoke.assert_called_once_with("질문")


@pytest.mark.asyncio
async def test_rag_service_query_returns_fallback_on_error() -> None:
    service = RagService.__new__(RagService)
    service.ready = True
    service.chain = Mock()
    service.chain.invoke.side_effect = RuntimeError("rag failed")

    response = await service.query("질문")
    assert response == "법령 검색 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."
