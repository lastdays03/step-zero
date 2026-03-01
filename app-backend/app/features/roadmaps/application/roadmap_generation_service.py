import asyncio
import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field, ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.features.rag.application.deps import get_rag_service
from app.features.roadmaps.application.actionkit_matcher import (
    ActionKitMatcher,
    MatchedActionKit,
)
from app.features.roadmaps.application.llm_personalizer import (
    LLMPersonalizer,
    PersonalizedStepDetail,
)
from app.features.roadmaps.application.template_resolver import TemplateResolver
from app.repositories.roadmap_job_repository import RoadmapJobRepository
from app.repositories.roadmap_repository import RoadmapRepository

logger = get_logger(__name__)

# Minimum number of ActionKit matches required to use the direct mapping path.
# Below this threshold, the service falls back to legacy LLM generation.
# Lowered from 3 to 1: even a single quality ActionKit match provides
# structured fact data (law names, files, highlights) that is superior
# to purely LLM-generated content.  The LLMPersonalizer already handles
# small match counts by grouping available facts into phases.
_MIN_ACTIONKIT_MATCHES = 1


def _actionkit_item_url(item_id: int) -> str:
    """Build a consistent item-based URL for ActionKit references."""
    return f"/api/v1/actionkits/items/{item_id}"


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
    startup_method: str | None = None  # 신규/양수양도/프랜차이즈
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
        job = await self.job_repo.create_job(
            team_id=team_id, user_id=user_id, payload=payload
        )
        return job.id

    async def validate_generation_input(
        self,
        *,
        business_type: str,
        location: str,
        description: str = "",
    ) -> InputValidationResult:
        """Validate and normalize business type / location using direct LLM call.

        Uses the LLM's general knowledge (NOT the RAG chain) so that
        business types absent from the vector store can still be normalized
        to standard administrative categories.
        """
        prompt = (
            "당신은 한국 창업 전문가입니다. 사용자가 창업하려는 업종과 지역을 입력했습니다.\n"
            "입력값을 검증하고 JSON만 반환해 주세요.\n\n"
            "필수 키: valid(boolean), normalized_business_type(string|null), "
            "normalized_location(string|null), reason(string|null), confidence(number:0~1).\n\n"
            "업종 정규화 규칙 (중요: 사용자는 창업을 원하므로 최대한 관련 업종을 찾아 정규화하세요):\n"
            "1) 아래 '우선 매칭 업종'으로 매핑 가능하면 해당 값을 사용하세요:\n"
            "   휴게음식점, 일반음식점, 식품제조가공업, 통신판매업, 미용업, 일반소매업, 학원업, 숙박업\n"
            "2) 정규화 예시:\n"
            "   카페/커피숍/베이커리/디저트가게 -> 휴게음식점\n"
            "   식당/음식점/레스토랑/치킨집/분식집 -> 일반음식점\n"
            "   온라인쇼핑몰/쇼핑몰/앱서비스/어플리케이션사업/플랫폼사업/이커머스 -> 통신판매업\n"
            "   네일샵/헤어샵/피부관리/에스테틱/왁싱 -> 미용업\n"
            "   편의점/마트/잡화점/의류매장/꽃집 -> 일반소매업\n"
            "   학원/교습소/코딩학원/영어학원/피아노학원 -> 학원업\n"
            "   펜션/게스트하우스/민박/호텔/모텔 -> 숙박업\n"
            "   식품공장/제과공장/음료제조/건강식품 -> 식품제조가공업\n"
            "3) 위 목록에 해당하지 않아도 사업 활동이면 valid=true + 한국 행정 기준 업종명으로 정규화하세요.\n"
            "   예: 여행업/여행플래너 -> 관광사업, 물류 -> 화물운송업, 건축 -> 건설업\n"
            "4) 지역은 대한민국 행정구역으로 해석 가능해야 valid=true.\n"
            "5) 의미 없는 문자열이거나 사업과 무관한 입력만 valid=false로 처리.\n\n"
            f"입력 업종: {business_type}\n입력 지역: {location}\n추가 설명: {description}"
        )

        raw = await self._invoke_llm(prompt)
        if raw:
            parsed = self._parse_json(raw)
            if parsed:
                try:
                    result = InputValidationResult(**parsed)
                    if result.valid:
                        result.normalized_business_type = (
                            result.normalized_business_type or business_type
                        ).strip()
                        result.normalized_location = (
                            result.normalized_location or location
                        ).strip()
                    return result
                except ValidationError:
                    pass
        return self._fallback_validation(business_type=business_type, location=location)

    async def _invoke_llm(self, prompt: str) -> str | None:
        """Invoke the LLM directly without RAG retrieval context."""
        if not self.rag_service.ready:
            return None
        try:
            from fastapi.concurrency import run_in_threadpool

            result = await asyncio.wait_for(
                run_in_threadpool(self.rag_service.llm.invoke, prompt),
                timeout=15,
            )
            return result.content if hasattr(result, "content") else str(result)
        except Exception:
            logger.exception("Direct LLM invocation failed")
            return None

    async def process_job(self, job_id: UUID) -> None:
        job = await self.job_repo.get_by_id(job_id=job_id)
        if not job:
            return
        await self.job_repo.mark_running(job)
        try:
            payload = GenerationPayload(**job.input_payload)
            template_id: int | None = None
            should_draft = False

            # --- Step 0: Template resolution ---
            try:
                template = await TemplateResolver.resolve(
                    self.session,
                    business_type=payload.business_type,
                    startup_method=payload.startup_method,
                )
            except Exception:
                logger.debug("Template resolution skipped (table may not exist)")
                template = None

            if template:
                # --- TEMPLATE path: use approved template ---
                logger.info(
                    "Using template id=%d for business_type=%s",
                    template.id,
                    payload.business_type,
                )
                await self.job_repo.set_progress(
                    job, stage="TEMPLATE_RESOLVING", progress=20
                )
                steps_payload = await TemplateResolver.template_to_steps_payload(
                    self.session, template
                )
                await self.job_repo.set_progress(job, stage="PERSISTING", progress=80)
                generation_mode = "TEMPLATE"
                template_id = template.id
                title = f"{payload.business_type} 창업 로드맵"

            else:
                # --- Existing pipeline (no template) ---

                # --- Step 1: ActionKit matching (fact layer) ---
                matched_items = await self.actionkit_matcher.match(
                    business_type=payload.business_type,
                    location=payload.location,
                    session=self.session,
                )
                await self.job_repo.set_progress(
                    job, stage="MATCHING_COMPLETE", progress=20
                )

                # --- Decision point: ACTIONKIT_RAG vs RAG ---
                match_count = len(matched_items)
                top_scores = [f"{m.relevance_score:.3f}" for m in matched_items[:5]]
                logger.info(
                    "generation_mode decision: matched=%d, threshold=%d, "
                    "business_type=%s, top_scores=%s -> %s",
                    match_count,
                    _MIN_ACTIONKIT_MATCHES,
                    payload.business_type,
                    top_scores,
                    "ACTIONKIT_RAG" if match_count >= _MIN_ACTIONKIT_MATCHES else "RAG",
                )

                if match_count >= _MIN_ACTIONKIT_MATCHES:
                    # --- Step 2a: Sufficient matches -> LLM personalization ---
                    logger.info(
                        "ActionKit matched %d items; using personalized generation",
                        match_count,
                    )
                    await self.job_repo.set_progress(
                        job, stage="PERSONALIZING", progress=35
                    )

                    payload_dict = self._payload_to_dict(payload)
                    personalized = await self.llm_personalizer.personalize(
                        matched_items=matched_items,
                        payload=payload_dict,
                    )
                    await self.job_repo.set_progress(job, stage="PERSISTING", progress=80)

                    # Convert personalized details to step payload format
                    steps_payload = self._personalized_to_steps_payload(
                        personalized,
                        matched_items=matched_items,
                    )
                    generation_mode = "ACTIONKIT_RAG"
                    title = f"{payload.business_type} 창업 로드맵"

                else:
                    # --- Step 2b: Insufficient matches -> fallback to legacy ---
                    logger.info(
                        "ActionKit matched only %d items (< %d); falling back to LLM generation",
                        match_count,
                        _MIN_ACTIONKIT_MATCHES,
                    )
                    master = await self._generate_master_with_retry(payload)
                    await self.job_repo.set_progress(
                        job, stage="DETAIL_GENERATING", progress=35
                    )
                    details, fallback_phases = await self._generate_details_parallel(
                        master, payload
                    )
                    await self.job_repo.set_progress(job, stage="PERSISTING", progress=80)

                    steps_payload = [item.model_dump() for item in details]
                    # Attach quality metadata to each legacy RAG step
                    for sp in steps_payload:
                        phase = sp.get("phase", "")
                        is_fb = phase in fallback_phases
                        sp["mapping_source"] = "fallback" if is_fb else "rag"
                        sp["source_count"] = 0
                        sp["has_fallback"] = is_fb
                    generation_mode = "RAG"
                    title = master.title

                # --- Auto-DRAFT: register template for new business types ---
                try:
                    should_draft = await TemplateResolver.should_create_auto_draft(
                        self.session, business_type=payload.business_type
                    )
                    if should_draft:
                        logger.info(
                            "Auto-DRAFT: will create template for btype=%s after roadmap persist",
                            payload.business_type,
                        )
                except Exception:
                    logger.warning("Auto-DRAFT check failed", exc_info=True)
                    should_draft = False

            # --- Step 3: Persist ---
            roadmap = await self.roadmap_repo.create_roadmap(
                team_id=job.team_id,
                title=title,
                business_type=payload.business_type,
                location=payload.location,
                description=payload.description,
                startup_type=payload.startup_type,
                startup_method=payload.startup_method,
                open_timeline=payload.open_timeline,
                budget_range=payload.budget_range,
                additional_notes=payload.additional_notes,
                created_by=job.user_id,
            )

            # Set template_id if using template
            if template_id is not None:
                roadmap.template_id = template_id

            await self.roadmap_repo.create_steps_with_details(
                roadmap_id=roadmap.id,
                steps_payload=steps_payload,
                generation_mode=generation_mode,
            )
            await self.roadmap_repo.commit()

            # --- Auto-DRAFT creation (after commit) ---
            if not template and should_draft:
                try:
                    from app.features.ops.application.roadmap_templates.service import (
                        create_template_from_roadmap,
                    )

                    await create_template_from_roadmap(
                        self.session,
                        roadmap_id=roadmap.id,
                        user_id=job.user_id,
                    )
                    logger.info(
                        "Auto-DRAFT template created for btype=%s from roadmap=%s",
                        payload.business_type,
                        roadmap.id,
                    )
                except Exception:
                    logger.warning(
                        "Auto-DRAFT template creation failed for roadmap=%s",
                        roadmap.id,
                        exc_info=True,
                    )

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
            "startup_method": payload.startup_method,
            "open_timeline": payload.open_timeline,
            "budget_range": payload.budget_range,
            "additional_notes": payload.additional_notes,
            "goal_horizon_days": payload.goal_horizon_days,
            "experience_level": payload.experience_level,
        }

    @staticmethod
    def _personalized_to_steps_payload(
        personalized: list[PersonalizedStepDetail],
        matched_items: list[MatchedActionKit] | None = None,
    ) -> list[dict]:
        """Convert PersonalizedStepDetail list to the dict format expected by
        ``RoadmapRepository.create_steps_with_details()``.

        The repository expects each dict to contain:
          phase, title, objective, estimated_days, risk_notes,
          checklist (list[str]),
          legal_basis (list[dict] with title, snippet, source_url, ...),
          documents (list[dict] with name, type, source_url, ...)
        """
        # Build item_id -> file_urls map for source_url enrichment
        item_file_urls: dict[int, list[str]] = {}
        if matched_items:
            for m in matched_items:
                if m.item.id is not None and m.files:
                    item_file_urls[m.item.id] = [
                        f"/api/v1/actionkits/files/{f.object_key}" for f in m.files
                    ]

        results: list[dict] = []
        for detail in personalized:
            # Build legal_basis entries compatible with LegalBasisItem / repository
            legal_basis_items: list[dict] = []
            for lb in detail.legal_basis:
                item_id = lb.get("actionkit_item_id")
                # Use item_id-based URL for consistent linking
                source_url = (
                    _actionkit_item_url(item_id) if item_id else lb.get("source_url")
                )

                legal_basis_items.append(
                    {
                        "title": lb.get("title", ""),
                        "snippet": lb.get("snippet", ""),
                        "source_url": source_url,
                        "actionkit_item_id": item_id,
                        "mapping_source": detail.mapping_source,
                    }
                )

            # Build document entries compatible with DocumentItem / repository
            document_items: list[dict] = []
            for doc in detail.documents:
                item_id = doc.get("actionkit_item_id")
                file_url = doc.get("file_url") or ""
                # Enrich file_url to full API path if it's an object_key
                if file_url and not file_url.startswith("/"):
                    file_url = f"/api/v1/actionkits/files/{file_url}"
                # Fallback: derive from actionkit_item_id
                if not file_url and item_id and item_id in item_file_urls:
                    file_url = item_file_urls[item_id][0]
                # Use item_id-based URL for source_url, file_url for download
                source_url = (
                    _actionkit_item_url(item_id) if item_id else (file_url or None)
                )

                document_items.append(
                    {
                        "name": doc.get("name", "서류"),
                        "type": doc.get("type", "FORM"),
                        "file_url": file_url or None,
                        "source_url": source_url,
                        "actionkit_item_id": item_id,
                        "actionkit_file_id": doc.get("actionkit_file_id"),
                        "all_file_urls": item_file_urls.get(item_id, []),
                        "mapping_source": detail.mapping_source,
                    }
                )

            # Build checklist with metadata
            checklist_items: list[str] = detail.checklist or ["필수 요건 확인"]

            # Quality metadata
            source_count = len(detail.actionkit_items) if detail.actionkit_items else 0
            is_fallback = detail.mapping_source == "fallback"

            results.append(
                {
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
                    "source_count": source_count,
                    "has_fallback": is_fallback,
                }
            )
        return results

    async def _generate_master_with_retry(
        self, payload: GenerationPayload
    ) -> MasterRoadmap:
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
    ) -> tuple[list[StepDetail], set[str]]:
        """Generate details in parallel. Returns (details, fallback_phase_names)."""
        semaphore = asyncio.Semaphore(3)
        fallback_phases: set[str] = set()

        async def _run(phase_name: str) -> StepDetail:
            async with semaphore:
                detail, is_fallback = await self._generate_phase_detail_with_retry(
                    phase_name, payload
                )
                if is_fallback:
                    fallback_phases.add(phase_name)
                return detail

        tasks = [asyncio.create_task(_run(phase)) for phase in master.phases]
        return list(await asyncio.gather(*tasks)), fallback_phases

    async def _generate_phase_detail_with_retry(
        self,
        phase_name: str,
        payload: GenerationPayload,
    ) -> tuple[StepDetail, bool]:
        """Generate detail for a phase. Returns (detail, is_fallback)."""
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
                return self._normalize_document_urls(detail), False
            except ValidationError:
                continue
        logger.warning(
            "Phase detail generation failed for '%s'; using fallback template",
            phase_name,
        )
        return self._fallback_detail(phase_name), True

    @staticmethod
    def _normalize_document_urls(detail: StepDetail) -> StepDetail:
        for doc in detail.documents:
            preferred = (
                doc.source_url or doc.download_url or doc.template_url or doc.file_url
            )
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

    # Phase-specific fallback templates for non-law steps
    _PHASE_FALLBACK_TEMPLATES: dict[str, dict] = {
        "세무 설정": {
            "title": "세무·회계 기초 설정",
            "objective": "사업자등록 및 세무 신고 체계를 구축합니다.",
            "checklist": [
                "사업자등록 신청 (관할 세무서 또는 홈택스)",
                "업종별 부가가치세 과세/면세 여부 확인",
                "세금계산서 발행 체계 준비",
                "세무사/회계사 선임 검토",
                "간이과세 vs 일반과세 선택 판단",
            ],
            "legal_basis_title": "부가가치세법, 소득세법",
            "legal_basis_snippet": "사업자등록 의무 및 세금 신고 절차 관련 법령",
            "estimated_days": 7,
            "risk_notes": [
                "사업자등록 지연 시 매입세액 공제 불가",
                "간이과세 선택 오류 시 세금 부담 증가",
            ],
        },
        "인사·노무": {
            "title": "인사·노무 관리 체계 수립",
            "objective": "근로자 채용 및 노무 관리 기초를 마련합니다.",
            "checklist": [
                "근로계약서 표준 양식 준비",
                "4대보험 사업장 가입 신고",
                "취업규칙 작성 (10인 이상 사업장)",
                "최저임금 및 근로시간 기준 확인",
                "산업재해보상보험 가입",
            ],
            "legal_basis_title": "근로기준법, 고용보험법",
            "legal_basis_snippet": "근로계약, 임금, 4대보험 가입 의무 관련 법령",
            "estimated_days": 5,
            "risk_notes": [
                "근로계약서 미작성 시 과태료 부과",
                "4대보험 미가입 시 사업주 부담금 소급 징수",
            ],
        },
        "정책자금 신청": {
            "title": "정책자금·지원사업 신청",
            "objective": "소상공인 정책자금 및 창업 지원사업을 확인하고 신청합니다.",
            "checklist": [
                "소상공인진흥공단 정책자금 공고 확인",
                "지자체 창업지원사업 모집 확인",
                "신용보증재단 보증 신청 검토",
                "사업계획서 작성",
                "필요 구비서류 목록 확인 및 준비",
            ],
            "legal_basis_title": "소상공인 보호 및 지원에 관한 법률",
            "legal_basis_snippet": "소상공인 정책자금 지원 근거 및 신청 절차",
            "estimated_days": 14,
            "risk_notes": [
                "신청 기간 경과 시 다음 차수까지 대기 필요",
                "서류 미비 시 심사 탈락 가능",
            ],
        },
        "법률 준비": {
            "title": "법률·행정 기초 준비",
            "objective": "사업 형태 결정 및 법률적 기초를 준비합니다.",
            "checklist": [
                "사업 형태 결정 (개인/법인)",
                "법인 설립 시 정관 작성 및 등기",
                "사업장 임대차 계약 검토",
                "업종별 인허가 요건 사전 확인",
                "상호 및 상표 등록 검토",
            ],
            "legal_basis_title": "상법, 민법",
            "legal_basis_snippet": "법인 설립, 계약, 상호 관련 법률 기초",
            "estimated_days": 7,
            "risk_notes": [
                "법인 형태 선택 오류 시 세금·책임 구조 변경 곤란",
                "임대차 특약 미확인 시 분쟁 가능",
            ],
        },
        "준비": {
            "title": "창업 사전 준비",
            "objective": "창업에 필요한 기초 사항을 점검하고 준비합니다.",
            "checklist": [
                "사업 아이템 구체화 및 시장 조사",
                "사업계획서 초안 작성",
                "예상 비용 및 자금 계획 수립",
                "사업장 입지 선정 및 임대차 검토",
                "업종별 필요 자격·면허 확인",
            ],
            "legal_basis_title": "관련 업종별 개별법",
            "legal_basis_snippet": "업종에 따라 적용되는 개별 법령 확인 필요",
            "estimated_days": 14,
            "risk_notes": ["사전 조사 부족 시 인허가 단계에서 변경 비용 발생"],
        },
        "인허가": {
            "title": "영업 인허가 취득",
            "objective": "관할 관청에 영업 인허가를 신청하고 취득합니다.",
            "checklist": [
                "업종별 인허가 종류 확인 (허가/등록/신고)",
                "관할 관청 방문 또는 온라인 신청",
                "구비서류 목록 확인 및 준비",
                "현장 점검 일정 확인",
                "인허가증 수령 및 보관",
            ],
            "legal_basis_title": "업종별 개별법",
            "legal_basis_snippet": "업종에 따른 인허가 근거 법령 (식품위생법, 공중위생관리법 등)",
            "estimated_days": 10,
            "risk_notes": [
                "서류 미비 시 보완 명령으로 개업 지연",
                "시설 기준 미달 시 불허 가능",
            ],
        },
        "운영준비": {
            "title": "영업 운영 준비",
            "objective": "개업 전 운영 체계를 구축합니다.",
            "checklist": [
                "매장 인테리어 및 설비 설치",
                "POS/결제 시스템 설치",
                "원재료·상품 초도 물량 확보",
                "영업배상책임보험 가입",
                "위생교육 이수 확인",
            ],
            "legal_basis_title": "관련 업종별 개별법",
            "legal_basis_snippet": "영업장 시설 기준 및 위생 관리 의무",
            "estimated_days": 14,
            "risk_notes": [
                "시설 기준 미달 시 영업정지 가능",
                "보험 미가입 시 사고 발생 시 전액 배상 부담",
            ],
        },
    }

    @classmethod
    def _fallback_detail(cls, phase_name: str) -> StepDetail:
        template = cls._PHASE_FALLBACK_TEMPLATES.get(phase_name)
        if template:
            return StepDetail(
                phase=phase_name,
                title=template["title"],
                objective=template["objective"],
                checklist=template["checklist"],
                legal_basis=[
                    LegalBasisItem(
                        title=template["legal_basis_title"],
                        snippet=template["legal_basis_snippet"],
                        source_url=None,
                    )
                ],
                documents=[],
                estimated_days=template["estimated_days"],
                risk_notes=template["risk_notes"],
            )
        # Generic fallback for unknown phases
        return StepDetail(
            phase=phase_name,
            title=f"{phase_name} 단계 진행",
            objective=f"{phase_name} 관련 핵심 절차를 확인하고 준비합니다.",
            checklist=[
                f"{phase_name} 관련 필수 요건 확인",
                "관할 기관 문의 및 구비서류 목록 확인",
                "제출 서류 준비 및 접수",
            ],
            legal_basis=[
                LegalBasisItem(
                    title="근거 보강 필요",
                    snippet="RAG 근거를 확인하지 못해 기본 단계로 생성되었습니다. 관할 기관에 확인하세요.",
                    source_url=None,
                )
            ],
            documents=[],
            estimated_days=5,
            risk_notes=["세부 근거 미확인 상태이므로 관할 기관에 직접 확인 필요"],
        )

    @staticmethod
    def _fallback_validation(
        *, business_type: str, location: str
    ) -> InputValidationResult:
        business = business_type.strip()
        loc = location.strip()
        if len(business) < 2 or len(loc) < 2:
            return InputValidationResult(
                valid=False,
                reason="업종과 지역은 최소 2자 이상 입력해 주세요.",
                confidence=0.0,
            )
        has_region_hint = any(
            token in loc
            for token in (
                "특별시",
                "광역시",
                "특별자치시",
                "특별자치도",
                "도",
                "시",
                "군",
                "구",
            )
        )
        if not has_region_hint:
            return InputValidationResult(
                valid=False,
                reason="지역은 시/도/군/구 단위까지 포함해 입력해 주세요.",
                confidence=0.0,
            )
        normalized_business = (
            "휴게음식점" if business in {"카페", "커피숍", "커피숖"} else business
        )
        return InputValidationResult(
            valid=True,
            normalized_business_type=normalized_business,
            normalized_location=loc,
            reason=None,
            confidence=0.6,
        )
