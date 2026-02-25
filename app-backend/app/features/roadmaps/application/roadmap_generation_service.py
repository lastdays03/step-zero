import asyncio
import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.features.rag.application.deps import get_rag_service
from app.features.roadmaps.application.actionkit_matcher import ActionKitMatcher, MatchedActionKit
from app.features.roadmaps.application.llm_personalizer import LLMPersonalizer, PersonalizedStepDetail
from app.repositories.roadmap_job_repository import RoadmapJobRepository
from app.repositories.roadmap_repository import RoadmapRepository

logger = get_logger(__name__)

# Minimum number of ActionKit matches required to use the direct mapping path.
# Below this threshold, the service falls back to legacy LLM generation.
_MIN_ACTIONKIT_MATCHES = 3


class LegalBasisItem(BaseModel):
    title: str
    snippet: str = ""
    source_url: str | None = None


class DocumentItem(BaseModel):
    name: str
    type: str = "FORM"
    source_url: str | None = None
    download_url: str | None = None
    template_url: str | None = None
    file_url: str | None = None


class StepDetail(BaseModel):
    phase: str
    title: str
    objective: str
    checklist: list[str] = Field(default_factory=list, min_length=1)
    legal_basis: list[LegalBasisItem] = Field(default_factory=list, min_length=1)
    documents: list[DocumentItem] = Field(default_factory=list)
    estimated_days: int = 0
    risk_notes: list[str] = Field(default_factory=list)


class MasterRoadmap(BaseModel):
    title: str
    summary: str = ""
    phases: list[str] = Field(min_length=1)


class InputValidationResult(BaseModel):
    valid: bool
    normalized_business_type: str | None = None
    normalized_location: str | None = None
    reason: str | None = None
    confidence: float = 0.0


@dataclass
class GenerationPayload:
    business_type: str
    location: str
    description: str
    startup_type: str | None = None
    open_timeline: str | None = None
    budget_range: str | None = None
    additional_notes: str = ""
    goal_horizon_days: int = 30
    experience_level: str = "BEGINNER"


class RoadmapGenerationService:
    def __init__(
        self,
        session: AsyncSession,
        *,
        actionkit_matcher: ActionKitMatcher | None = None,
        llm_personalizer: LLMPersonalizer | None = None,
    ):
        self.session = session
        self.job_repo = RoadmapJobRepository(session)
        self.roadmap_repo = RoadmapRepository(session)
        self.rag_service = get_rag_service()

        # Lazy-import deps to avoid circular imports at module level
        if actionkit_matcher is None or llm_personalizer is None:
            from app.features.roadmaps.application.deps import (
                get_actionkit_matcher,
                get_llm_personalizer,
            )
            self.actionkit_matcher = actionkit_matcher or get_actionkit_matcher()
            self.llm_personalizer = llm_personalizer or get_llm_personalizer()
        else:
            self.actionkit_matcher = actionkit_matcher
            self.llm_personalizer = llm_personalizer

    async def submit_job(self, *, team_id: UUID, user_id: int, payload: dict) -> UUID:
        job = await self.job_repo.create_job(team_id=team_id, user_id=user_id, payload=payload)
        return job.id

    async def validate_generation_input(
        self,
        *,
        business_type: str,
        location: str,
        description: str = "",
    ) -> InputValidationResult:
        prompt = (
            "다음 창업 입력값을 검증하고 JSON만 반환해 주세요.\n"
            "필수 키: valid(boolean), normalized_business_type(string|null), normalized_location(string|null),"
            " reason(string|null), confidence(number:0~1).\n"
            "규칙:\n"
            "1) 업종이 일상 표현이면 행정/인허가 기준 업종으로 정규화합니다. 예: 카페 -> 휴게음식점.\n"
            "2) 지역은 대한민국 행정구역 기준으로 해석 가능한 경우만 valid=true.\n"
            "3) 모호하거나 해석 불가하면 valid=false와 reason을 반환합니다.\n"
            f"입력 업종: {business_type}\n입력 지역: {location}\n추가 설명: {description}"
        )
        for _ in range(2):
            raw = await self.rag_service.query(prompt)
            parsed = self._parse_json(raw)
            if not parsed:
                continue
            try:
                result = InputValidationResult(**parsed)
                if result.valid:
                    result.normalized_business_type = (result.normalized_business_type or business_type).strip()
                    result.normalized_location = (result.normalized_location or location).strip()
                return result
            except ValidationError:
                continue
        return self._fallback_validation(business_type=business_type, location=location)

    async def process_job(self, job_id: UUID) -> None:
        job = await self.job_repo.get_by_id(job_id=job_id)
        if not job:
            return
        await self.job_repo.mark_running(job)
        try:
            payload = GenerationPayload(**job.input_payload)

            # --- Step 1: ActionKit matching (fact layer) ---
            matched_items = await self.actionkit_matcher.match(
                business_type=payload.business_type,
                location=payload.location,
                session=self.session,
            )
            await self.job_repo.set_progress(job, stage="MATCHING_COMPLETE", progress=20)

            if len(matched_items) >= _MIN_ACTIONKIT_MATCHES:
                # --- Step 2a: Sufficient matches -> LLM personalization ---
                logger.info(
                    "ActionKit matched %d items; using personalized generation",
                    len(matched_items),
                )
                await self.job_repo.set_progress(job, stage="PERSONALIZING", progress=35)

                payload_dict = self._payload_to_dict(payload)
                personalized = await self.llm_personalizer.personalize(
                    matched_items=matched_items,
                    payload=payload_dict,
                )
                await self.job_repo.set_progress(job, stage="PERSISTING", progress=80)

                # Convert personalized details to step payload format
                steps_payload = self._personalized_to_steps_payload(personalized)
                generation_mode = "ACTIONKIT_RAG"
                title = f"{payload.business_type} 창업 로드맵"

            else:
                # --- Step 2b: Insufficient matches -> fallback to legacy ---
                logger.info(
                    "ActionKit matched only %d items (< %d); falling back to LLM generation",
                    len(matched_items),
                    _MIN_ACTIONKIT_MATCHES,
                )
                master = await self._generate_master_with_retry(payload)
                await self.job_repo.set_progress(job, stage="DETAIL_GENERATING", progress=35)
                details = await self._generate_details_parallel(master, payload)
                await self.job_repo.set_progress(job, stage="PERSISTING", progress=80)

                steps_payload = [item.model_dump() for item in details]
                generation_mode = "RAG"
                title = master.title

            # --- Step 3: Persist ---
            roadmap = await self.roadmap_repo.create_roadmap(
                team_id=job.team_id,
                title=title,
                business_type=payload.business_type,
                location=payload.location,
                description=payload.description,
                startup_type=payload.startup_type,
                open_timeline=payload.open_timeline,
                budget_range=payload.budget_range,
                additional_notes=payload.additional_notes,
                created_by=job.user_id,
            )
            await self.roadmap_repo.create_steps_with_details(
                roadmap_id=roadmap.id,
                steps_payload=steps_payload,
                generation_mode=generation_mode,
            )
            await self.roadmap_repo.commit()
            await self.job_repo.mark_succeeded(job, roadmap_id=roadmap.id)
        except Exception as exc:
            logger.exception("Roadmap generation failed for job=%s", job_id)
            await self.job_repo.mark_failed(
                job,
                code="GENERATION_FAILED",
                message=str(exc),
            )

    @staticmethod
    def _payload_to_dict(payload: GenerationPayload) -> dict:
        """Convert GenerationPayload dataclass to dict."""
        return {
            "business_type": payload.business_type,
            "location": payload.location,
            "description": payload.description,
            "startup_type": payload.startup_type,
            "open_timeline": payload.open_timeline,
            "budget_range": payload.budget_range,
            "additional_notes": payload.additional_notes,
            "goal_horizon_days": payload.goal_horizon_days,
            "experience_level": payload.experience_level,
        }

    @staticmethod
    def _personalized_to_steps_payload(
        personalized: list[PersonalizedStepDetail],
    ) -> list[dict]:
        """Convert PersonalizedStepDetail list to the dict format expected by
        ``RoadmapRepository.create_steps_with_details()``.

        The repository expects each dict to contain:
          phase, title, objective, estimated_days, risk_notes,
          checklist (list[str]),
          legal_basis (list[dict] with title, snippet, source_url, ...),
          documents (list[dict] with name, type, source_url, ...)
        """
        results: list[dict] = []
        for detail in personalized:
            # Build legal_basis entries compatible with LegalBasisItem / repository
            legal_basis_items: list[dict] = []
            for lb in detail.legal_basis:
                legal_basis_items.append({
                    "title": lb.get("title", ""),
                    "snippet": lb.get("snippet", ""),
                    "source_url": lb.get("source_url"),
                    "actionkit_item_id": lb.get("actionkit_item_id"),
                    "mapping_source": detail.mapping_source,
                })

            # Build document entries compatible with DocumentItem / repository
            document_items: list[dict] = []
            for doc in detail.documents:
                document_items.append({
                    "name": doc.get("name", "서류"),
                    "type": doc.get("type", "FORM"),
                    "file_url": doc.get("file_url"),
                    "source_url": doc.get("file_url"),
                    "actionkit_item_id": doc.get("actionkit_item_id"),
                    "actionkit_file_id": doc.get("actionkit_file_id"),
                    "mapping_source": detail.mapping_source,
                })

            # Build checklist with metadata
            checklist_items: list[str] = detail.checklist or ["필수 요건 확인"]

            results.append({
                "phase": detail.phase,
                "title": detail.title or f"{detail.phase} 단계",
                "objective": detail.objective,
                "estimated_days": detail.estimated_days,
                "risk_notes": detail.risk_notes,
                "checklist": checklist_items,
                "legal_basis": legal_basis_items,
                "documents": document_items,
                "mapping_source": detail.mapping_source,
                "actionkit_items": detail.actionkit_items,
            })
        return results

    async def _generate_master_with_retry(self, payload: GenerationPayload) -> MasterRoadmap:
        prompt = (
            "업종/지역 기반 창업 로드맵 상위 단계를 JSON만으로 생성해 주세요.\n"
            "필수 키: title, summary, phases(list of phase string).\n"
            f"업종: {payload.business_type}\n지역: {payload.location}\n"
            f"창업 형태: {payload.startup_type or '미입력'}\n"
            f"오픈 목표: {payload.open_timeline or '미입력'}\n"
            f"예산 범위: {payload.budget_range or '미입력'}\n"
            f"추가 설명: {payload.description}\n"
            f"추가 메모: {payload.additional_notes}"
        )
        for _ in range(2):
            raw = await self.rag_service.query(prompt)
            parsed = self._parse_json(raw)
            if not parsed:
                continue
            try:
                return MasterRoadmap(**parsed)
            except ValidationError:
                continue
        return self._fallback_master(payload)

    async def _generate_details_parallel(
        self,
        master: MasterRoadmap,
        payload: GenerationPayload,
    ) -> list[StepDetail]:
        semaphore = asyncio.Semaphore(3)

        async def _run(phase_name: str) -> StepDetail:
            async with semaphore:
                return await self._generate_phase_detail_with_retry(phase_name, payload)

        tasks = [asyncio.create_task(_run(phase)) for phase in master.phases]
        return list(await asyncio.gather(*tasks))

    async def _generate_phase_detail_with_retry(
        self,
        phase_name: str,
        payload: GenerationPayload,
    ) -> StepDetail:
        prompt = (
            "다음 phase의 상세 실행 단계를 JSON으로 생성해 주세요.\n"
            "필수 키: phase, title, objective, checklist(array), legal_basis(array[{title,snippet,source_url}]),"
            " documents(array[{name,type,source_url,download_url,template_url,file_url}]), estimated_days, risk_notes(array)\n"
            f"phase: {phase_name}\n업종: {payload.business_type}\n지역: {payload.location}\n"
            f"창업 형태: {payload.startup_type or '미입력'}\n"
            f"오픈 목표: {payload.open_timeline or '미입력'}\n"
            f"예산 범위: {payload.budget_range or '미입력'}\n"
            f"추가 설명: {payload.description}\n"
            f"추가 메모: {payload.additional_notes}"
        )
        for _ in range(2):
            raw = await self.rag_service.query(prompt)
            parsed = self._parse_json(raw)
            if not parsed:
                continue
            try:
                detail = StepDetail(**parsed)
                return self._normalize_document_urls(detail)
            except ValidationError:
                continue
        return self._fallback_detail(phase_name)

    @staticmethod
    def _normalize_document_urls(detail: StepDetail) -> StepDetail:
        for doc in detail.documents:
            preferred = doc.source_url or doc.download_url or doc.template_url or doc.file_url
            if preferred:
                doc.source_url = preferred
        return detail

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any] | None:
        text = raw.strip()
        if "```json" in text:
            text = text.split("```json", 1)[1].split("```", 1)[0].strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            try:
                start = text.find("{")
                end = text.rfind("}")
                if start >= 0 and end > start:
                    return json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                return None
        return None

    @staticmethod
    def _fallback_master(payload: GenerationPayload) -> MasterRoadmap:
        return MasterRoadmap(
            title=f"{payload.business_type} 창업 로드맵",
            summary="기본 템플릿 기반으로 생성됨",
            phases=["준비", "인허가", "운영준비"],
        )

    @staticmethod
    def _fallback_detail(phase_name: str) -> StepDetail:
        return StepDetail(
            phase=phase_name,
            title=f"{phase_name} 단계 진행",
            objective="핵심 절차를 확인하고 준비합니다.",
            checklist=["필수 요건 확인", "제출 항목 준비"],
            legal_basis=[
                LegalBasisItem(
                    title="근거 보강 필요",
                    snippet="RAG 근거를 확인하지 못해 기본 단계로 생성되었습니다.",
                    source_url=None,
                )
            ],
            documents=[],
            estimated_days=3,
            risk_notes=["세부 근거 확인 전 진행 시 재작업 가능성"],
        )

    @staticmethod
    def _fallback_validation(*, business_type: str, location: str) -> InputValidationResult:
        business = business_type.strip()
        loc = location.strip()
        if len(business) < 2 or len(loc) < 2:
            return InputValidationResult(
                valid=False,
                reason="업종과 지역은 최소 2자 이상 입력해 주세요.",
                confidence=0.0,
            )
        has_region_hint = any(token in loc for token in ("특별시", "광역시", "특별자치시", "특별자치도", "도", "시", "군", "구"))
        if not has_region_hint:
            return InputValidationResult(
                valid=False,
                reason="지역은 시/도/군/구 단위까지 포함해 입력해 주세요.",
                confidence=0.0,
            )
        normalized_business = "휴게음식점" if business in {"카페", "커피숍", "커피숖"} else business
        return InputValidationResult(
            valid=True,
            normalized_business_type=normalized_business,
            normalized_location=loc,
            reason=None,
            confidence=0.6,
        )
