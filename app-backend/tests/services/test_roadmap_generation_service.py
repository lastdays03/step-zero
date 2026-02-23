import pytest

from app.core import db
from app.features.roadmaps.application.roadmap_generation_service import (
    GenerationPayload,
    RoadmapGenerationService,
)


@pytest.mark.asyncio
async def test_generate_phase_detail_normalizes_document_source_url():
    async with db.async_session() as session:
        service = RoadmapGenerationService(session)

        async def _mock_query(_question: str) -> str:
            return (
                '{"phase":"인허가","title":"인허가 준비","objective":"필수 인허가 문서 준비",'
                '"checklist":["요건 확인"],'
                '"legal_basis":[{"title":"식품위생법","snippet":"영업신고 필요","source_url":"https://law.go.kr"}],'
                '"documents":[{"name":"영업신고서","type":"FORM","template_url":"https://gov.kr/form.pdf"}],'
                '"estimated_days":5,"risk_notes":["누락 주의"]}'
            )

        service.rag_service.query = _mock_query  # type: ignore[method-assign]

        detail = await service._generate_phase_detail_with_retry(
            "인허가",
            GenerationPayload(
                business_type="휴게음식점",
                location="서울특별시 강남구",
                description="",
            ),
        )

        assert detail.documents
        assert detail.documents[0].template_url == "https://gov.kr/form.pdf"
        assert detail.documents[0].source_url == "https://gov.kr/form.pdf"
