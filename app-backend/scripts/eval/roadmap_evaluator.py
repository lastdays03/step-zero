"""Roadmap generation quality evaluator with 5 metrics + personalization comparison.

Evaluates roadmap output quality across five dimensions:
  1. actionkit_mapping_rate    - How many LEGAL_BASIS actions reference ActionKit items
  2. legal_basis_accuracy      - Whether mapped laws are relevant to the business type
  3. document_validity         - Whether DOCUMENT actions have valid file references
  4. generation_success_rate   - Whether generation used actionkit_direct vs llm_generated
  5. personalization_score     - Whether user inputs are reflected in the roadmap output

Design goals:
  - Works WITHOUT database/API (heuristic mode)
  - Works WITH live data (db_mode)
  - Called from run_evaluation.py --tier 4
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

# ─── Result dataclasses ────────────────────────────────────────────


@dataclass
class RoadmapEvalResult:
    """Result of evaluating a single roadmap.

    Attributes:
        roadmap_id: UUID of the roadmap being evaluated (None for mock data).
        actionkit_mapping_rate: Fraction of LEGAL_BASIS actions that have a
            non-null ``actionkit_item_id`` in their metadata_json.
        legal_basis_accuracy: Fraction of mapped laws that appear relevant to
            the declared business type (heuristic keyword match).
        document_validity: Fraction of DOCUMENT actions that have a non-empty
            file reference (``file_url`` / ``actionkit_file_id``).
        generation_success_rate: Fraction of step actions whose
            ``mapping_source`` equals ``actionkit_direct``.
        personalization_score: Heuristic score (0-1) measuring how much the
            user inputs (startup_type, budget_range, experience_level) are
            reflected in the roadmap text.
        details: Diagnostic breakdown dict.
    """

    roadmap_id: UUID | None = None
    actionkit_mapping_rate: float = 0.0
    legal_basis_accuracy: float = 0.0
    document_validity: float = 0.0
    generation_success_rate: float = 0.0
    personalization_score: float = 0.0
    details: dict = field(default_factory=dict)

    def overall_score(self) -> float:
        """Weighted average of all 5 metrics."""
        weights = {
            "actionkit_mapping_rate": 0.25,
            "legal_basis_accuracy": 0.20,
            "document_validity": 0.20,
            "generation_success_rate": 0.15,
            "personalization_score": 0.20,
        }
        return (
            self.actionkit_mapping_rate * weights["actionkit_mapping_rate"]
            + self.legal_basis_accuracy * weights["legal_basis_accuracy"]
            + self.document_validity * weights["document_validity"]
            + self.generation_success_rate * weights["generation_success_rate"]
            + self.personalization_score * weights["personalization_score"]
        )

    def to_dict(self) -> dict:
        """Serialize to a plain dict (JSON-serialisable)."""
        return {
            "roadmap_id": str(self.roadmap_id) if self.roadmap_id else None,
            "actionkit_mapping_rate": self.actionkit_mapping_rate,
            "legal_basis_accuracy": self.legal_basis_accuracy,
            "document_validity": self.document_validity,
            "generation_success_rate": self.generation_success_rate,
            "personalization_score": self.personalization_score,
            "overall_score": self.overall_score(),
            "details": self.details,
        }


@dataclass
class PersonalizationEvalResult:
    """Result of comparing two roadmaps for personalization quality.

    Measures how much the two different user-input payloads produce
    meaningfully different roadmap outputs.

    Attributes:
        pair_description: Human-readable description of the comparison pair.
        checklist_difference: Jaccard distance between the two checklists
            (1.0 = completely different, 0.0 = identical).
        phase_difference: Normalised difference in phase names/counts.
        risk_notes_difference: Jaccard distance between risk note sets.
        estimated_days_difference: Normalised difference in total estimated
            days.
        overall_personalization_score: Combined score 0-1. Higher means the
            two roadmaps are more distinct (better personalization).
        analysis: Short text summary of the comparison result.
    """

    pair_description: str = ""
    checklist_difference: float = 0.0
    phase_difference: float = 0.0
    risk_notes_difference: float = 0.0
    estimated_days_difference: float = 0.0
    overall_personalization_score: float = 0.0
    analysis: str = ""

    def to_dict(self) -> dict:
        return {
            "pair_description": self.pair_description,
            "checklist_difference": self.checklist_difference,
            "phase_difference": self.phase_difference,
            "risk_notes_difference": self.risk_notes_difference,
            "estimated_days_difference": self.estimated_days_difference,
            "overall_personalization_score": self.overall_personalization_score,
            "analysis": self.analysis,
        }


# ─── Business-type keyword heuristics ─────────────────────────────

# Maps broad business-type terms to law keywords that should appear
# in legal_basis titles for a "relevant" mapping.
_BUSINESS_TYPE_LAW_HINTS: dict[str, list[str]] = {
    "휴게음식점": ["식품위생법", "위생", "영업신고", "소방", "건축"],
    "일반음식점": ["식품위생법", "위생", "영업신고", "소방", "건축"],
    "카페": ["식품위생법", "위생", "영업신고"],
    "커피숍": ["식품위생법", "위생", "영업신고"],
    "편의점": ["유통산업발전법", "식품위생법", "위생"],
    "주점": ["식품위생법", "주세법", "위생", "소방"],
    "노래방": ["식품위생법", "공중위생관리법", "소방"],
    "미용실": ["공중위생관리법", "위생"],
    "학원": ["학원법", "교육"],
    "의원": ["의료법", "의료"],
    "약국": ["약사법", "약"],
    "세탁소": ["공중위생관리법", "위생"],
    "숙박": ["공중위생관리법", "소방", "위생"],
    "부동산": ["공인중개사법", "부동산"],
}

# Personalization signal keywords for each input field
_EXPERIENCE_KEYWORDS = {
    "BEGINNER": ["확인", "준비", "절차", "안내", "방법", "필요"],
    "EXPERIENCED": ["핵심", "주요", "중요", "간략", "요약"],
}
_STARTUP_TYPE_KEYWORDS = {
    "양수양도": ["양수", "양도", "승계", "인수"],
    "프랜차이즈": ["프랜차이즈", "본사", "가맹", "지원"],
    "신규": [],  # No specific negative keywords; new startup is the default
}
_TIMELINE_SHORT = ["단기", "신속", "빠른", "조기", "빠르게", "단기간"]
_TIMELINE_LONG = ["장기", "여유", "준비", "충분", "천천히"]


# ─── Core evaluator ───────────────────────────────────────────────


class RoadmapEvaluator:
    """Evaluates roadmap generation quality across 5 dimensions.

    Usage (heuristic mode, no DB required):
        evaluator = RoadmapEvaluator()
        result = await evaluator.evaluate(steps_payload, business_type)

    Usage (with DB for document_validity):
        evaluator = RoadmapEvaluator(session=db_session)
        result = await evaluator.evaluate(steps_payload, business_type)
    """

    def __init__(self, session: Any | None = None):
        """
        Args:
            session: Optional async SQLAlchemy session. When provided,
                ``document_validity`` performs real DB lookups. When absent,
                the evaluator falls back to heuristic checks.
        """
        self.session = session

    # ──────────────────────────────────────────────────────────────
    # Public API
    # ──────────────────────────────────────────────────────────────

    async def evaluate(
        self,
        steps_payload: list[dict],
        business_type: str,
        payload: dict | None = None,
    ) -> RoadmapEvalResult:
        """Evaluate a generated roadmap.

        Args:
            steps_payload: The steps data as produced by roadmap generation.
                Each element is a dict with keys: phase, title, objective,
                checklist, legal_basis, documents, risk_notes, estimated_days,
                mapping_source (optional).
            business_type: The business type used for generation.
            payload: The full generation payload (optional). Used for
                personalization_score when available.

        Returns:
            RoadmapEvalResult with 5 metrics computed.
        """
        # Collect all actions from steps_payload
        legal_basis_actions = self._collect_actions(steps_payload, "legal_basis")
        document_actions = self._collect_actions(steps_payload, "documents")
        all_actions_with_source = self._collect_actions_with_source(steps_payload)

        # Metric 1: actionkit_mapping_rate
        mapping_rate, mapping_details = self._compute_mapping_rate(legal_basis_actions)

        # Metric 2: legal_basis_accuracy
        accuracy, accuracy_details = self._compute_legal_accuracy(
            legal_basis_actions, business_type
        )

        # Metric 3: document_validity
        doc_validity, doc_details = await self._compute_document_validity(
            document_actions
        )

        # Metric 4: generation_success_rate
        success_rate, success_details = self._compute_success_rate(
            all_actions_with_source
        )

        # Metric 5: personalization_score
        person_score, person_details = self._compute_personalization_score(
            steps_payload, business_type, payload or {}
        )

        return RoadmapEvalResult(
            actionkit_mapping_rate=mapping_rate,
            legal_basis_accuracy=accuracy,
            document_validity=doc_validity,
            generation_success_rate=success_rate,
            personalization_score=person_score,
            details={
                "total_steps": len(steps_payload),
                "total_legal_basis": len(legal_basis_actions),
                "total_documents": len(document_actions),
                "mapping": mapping_details,
                "accuracy": accuracy_details,
                "document": doc_details,
                "success": success_details,
                "personalization": person_details,
            },
        )

    async def evaluate_personalization(
        self,
        result_a: list[dict],
        result_b: list[dict],
        payload_a: dict,
        payload_b: dict,
    ) -> PersonalizationEvalResult:
        """Compare two roadmaps generated with different user inputs.

        Checks if different inputs produce meaningfully different outputs.

        Args:
            result_a: steps_payload for roadmap A.
            result_b: steps_payload for roadmap B.
            payload_a: Generation payload used for roadmap A.
            payload_b: Generation payload used for roadmap B.

        Returns:
            PersonalizationEvalResult with difference scores.
        """
        desc = (
            f"'{payload_a.get('business_type', '?')} / "
            f"{payload_a.get('startup_type', '신규')} / "
            f"{payload_a.get('experience_level', 'BEGINNER')}'"
            " vs "
            f"'{payload_b.get('business_type', '?')} / "
            f"{payload_b.get('startup_type', '신규')} / "
            f"{payload_b.get('experience_level', 'BEGINNER')}'"
        )

        # Checklist difference (Jaccard distance)
        cl_a = self._extract_text_set(result_a, "checklist")
        cl_b = self._extract_text_set(result_b, "checklist")
        checklist_diff = self._jaccard_distance(cl_a, cl_b)

        # Phase difference
        phases_a = {s.get("phase", "") for s in result_a}
        phases_b = {s.get("phase", "") for s in result_b}
        phase_diff = self._jaccard_distance(phases_a, phases_b)

        # Risk notes difference
        rn_a = self._extract_text_set(result_a, "risk_notes")
        rn_b = self._extract_text_set(result_b, "risk_notes")
        risk_diff = self._jaccard_distance(rn_a, rn_b)

        # Estimated days difference
        days_a = sum(s.get("estimated_days", 0) for s in result_a)
        days_b = sum(s.get("estimated_days", 0) for s in result_b)
        total = days_a + days_b
        days_diff = abs(days_a - days_b) / total if total > 0 else 0.0

        # Overall: weighted average of differences (higher = more personalized)
        overall = (
            checklist_diff * 0.40
            + phase_diff * 0.20
            + risk_diff * 0.25
            + days_diff * 0.15
        )

        # Analysis text
        analysis = self._build_analysis(
            checklist_diff,
            phase_diff,
            risk_diff,
            days_diff,
            overall,
            payload_a,
            payload_b,
        )

        return PersonalizationEvalResult(
            pair_description=desc,
            checklist_difference=round(checklist_diff, 4),
            phase_difference=round(phase_diff, 4),
            risk_notes_difference=round(risk_diff, 4),
            estimated_days_difference=round(days_diff, 4),
            overall_personalization_score=round(overall, 4),
            analysis=analysis,
        )

    # ──────────────────────────────────────────────────────────────
    # Metric 1: actionkit_mapping_rate
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def _compute_mapping_rate(
        legal_basis_actions: list[dict],
    ) -> tuple[float, dict]:
        """Compute fraction of LEGAL_BASIS actions with actionkit_item_id."""
        total = len(legal_basis_actions)
        if total == 0:
            return 0.0, {"total": 0, "mapped": 0, "unmapped": []}

        mapped = 0
        unmapped: list[str] = []
        for item in legal_basis_actions:
            # Check both direct key and metadata_json
            item_id = item.get("actionkit_item_id") or (
                item.get("metadata_json", {}) or {}
            ).get("actionkit_item_id")
            if item_id is not None:
                mapped += 1
            else:
                unmapped.append(item.get("title", "?"))

        rate = mapped / total
        return rate, {"total": total, "mapped": mapped, "unmapped": unmapped[:10]}

    # ──────────────────────────────────────────────────────────────
    # Metric 2: legal_basis_accuracy
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def _compute_legal_accuracy(
        legal_basis_actions: list[dict],
        business_type: str,
    ) -> tuple[float, dict]:
        """Heuristic check: are law names relevant to the business type?

        Looks up keyword hints for the business type. If no hints found,
        falls back to checking that law titles are non-empty (basic sanity).
        """
        total = len(legal_basis_actions)
        if total == 0:
            return 0.0, {
                "total": 0,
                "relevant": 0,
                "irrelevant": [],
                "mode": "heuristic",
            }

        # Find matching keyword hints
        hints: list[str] = []
        for key, kws in _BUSINESS_TYPE_LAW_HINTS.items():
            if key in business_type or business_type in key:
                hints.extend(kws)

        relevant = 0
        irrelevant: list[str] = []
        mode = "keyword_match" if hints else "non_empty_check"

        for item in legal_basis_actions:
            title = (item.get("title") or "").strip()
            if not title:
                irrelevant.append("(empty title)")
                continue

            if hints:
                if any(h in title for h in hints):
                    relevant += 1
                else:
                    irrelevant.append(title)
            else:
                # Fallback: any non-empty law title is considered valid
                relevant += 1

        rate = relevant / total
        return rate, {
            "total": total,
            "relevant": relevant,
            "irrelevant": irrelevant[:10],
            "mode": mode,
            "hints_used": hints[:5],
        }

    # ──────────────────────────────────────────────────────────────
    # Metric 3: document_validity
    # ──────────────────────────────────────────────────────────────

    async def _compute_document_validity(
        self,
        document_actions: list[dict],
    ) -> tuple[float, dict]:
        """Check if DOCUMENT actions have valid file references.

        When a DB session is available, verifies that ``actionkit_file_id``
        exists in the ``actionkit_files`` table. Otherwise, checks that
        ``file_url`` / ``actionkit_file_id`` field is non-empty.
        """
        total = len(document_actions)
        if total == 0:
            return 1.0, {"total": 0, "valid": 0, "invalid": [], "mode": "n/a"}

        if self.session is not None:
            return await self._validate_docs_with_db(document_actions)
        else:
            return self._validate_docs_heuristic(document_actions)

    @staticmethod
    def _validate_docs_heuristic(
        document_actions: list[dict],
    ) -> tuple[float, dict]:
        """Heuristic document validity: check that file reference is non-empty."""
        total = len(document_actions)
        valid = 0
        invalid: list[str] = []

        for item in document_actions:
            file_url = item.get("file_url") or item.get("source_url")
            file_id = item.get("actionkit_file_id") or (
                item.get("metadata_json", {}) or {}
            ).get("actionkit_file_id")

            if file_url or file_id:
                valid += 1
            else:
                invalid.append(item.get("name", "?"))

        rate = valid / total
        return rate, {
            "total": total,
            "valid": valid,
            "invalid": invalid[:10],
            "mode": "heuristic",
        }

    async def _validate_docs_with_db(
        self,
        document_actions: list[dict],
    ) -> tuple[float, dict]:
        """DB-backed document validity check using actionkit_files table."""
        from sqlmodel import select

        try:
            from app.models.file import File
        except ImportError:
            return self._validate_docs_heuristic(document_actions)

        total = len(document_actions)
        valid = 0
        invalid: list[str] = []

        # Collect all file_ids to batch-query
        file_ids: list[int] = []
        for item in document_actions:
            fid = item.get("actionkit_file_id") or (
                item.get("metadata_json", {}) or {}
            ).get("actionkit_file_id")
            if fid is not None:
                try:
                    file_ids.append(int(fid))
                except (ValueError, TypeError):
                    pass

        existing_ids: set[int] = set()
        if file_ids:
            stmt = select(File.id).where(
                File.id.in_(file_ids),
                File.is_current.is_(True),
            )
            result = await self.session.execute(stmt)
            existing_ids = set(result.scalars().all())

        for item in document_actions:
            fid = item.get("actionkit_file_id") or (
                item.get("metadata_json", {}) or {}
            ).get("actionkit_file_id")
            file_url = item.get("file_url") or item.get("source_url")

            if fid is not None and int(fid) in existing_ids:
                valid += 1
            elif file_url:
                # Treat non-empty URL as valid when no file_id
                valid += 1
            else:
                invalid.append(item.get("name", "?"))

        rate = valid / total
        return rate, {
            "total": total,
            "valid": valid,
            "invalid": invalid[:10],
            "mode": "db_lookup",
        }

    # ──────────────────────────────────────────────────────────────
    # Metric 4: generation_success_rate
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def _compute_success_rate(
        all_actions: list[dict],
    ) -> tuple[float, dict]:
        """Fraction of actions using ``actionkit_direct`` mapping_source.

        ``actionkit_direct`` indicates that the generation used real ActionKit
        data rather than LLM hallucination.
        """
        total = len(all_actions)
        if total == 0:
            # If no actions, evaluate at step level
            return 0.0, {"total": 0, "direct": 0, "llm_generated": 0}

        direct = 0
        llm_gen = 0
        for item in all_actions:
            source = item.get("mapping_source") or (
                item.get("metadata_json", {}) or {}
            ).get("mapping_source", "llm_generated")
            if source == "actionkit_direct":
                direct += 1
            else:
                llm_gen += 1

        rate = direct / total
        return rate, {
            "total": total,
            "direct": direct,
            "llm_generated": llm_gen,
        }

    # ──────────────────────────────────────────────────────────────
    # Metric 5: personalization_score
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def _compute_personalization_score(
        steps_payload: list[dict],
        business_type: str,
        payload: dict,
    ) -> tuple[float, dict]:
        """Heuristic: check if user inputs are reflected in roadmap text.

        Checks 4 signals:
        1. business_type mentioned in at least one objective/title
        2. startup_type-specific keywords appear (양수양도/프랜차이즈)
        3. experience_level reflected (BEGINNER → more checklist items)
        4. open_timeline / budget reflected (short/long timeline signals)
        """
        full_text = _flatten_roadmap_text(steps_payload)
        signals_hit = 0
        total_signals = 0
        signal_details: dict[str, Any] = {}

        # Signal 1: business_type present in output text
        total_signals += 1
        bt = business_type.strip()
        if bt and bt in full_text:
            signals_hit += 1
            signal_details["business_type"] = "FOUND"
        else:
            signal_details["business_type"] = f"NOT FOUND ('{bt}')"

        # Signal 2: startup_type-specific keywords
        startup_type = (payload.get("startup_type") or "신규").strip()
        kws = _STARTUP_TYPE_KEYWORDS.get(startup_type, [])
        if kws:
            total_signals += 1
            if any(kw in full_text for kw in kws):
                signals_hit += 1
                signal_details["startup_type"] = f"FOUND ({startup_type})"
            else:
                signal_details["startup_type"] = f"NOT FOUND ({startup_type}: {kws})"

        # Signal 3: experience level reflected in checklist depth
        experience = (payload.get("experience_level") or "BEGINNER").strip()
        exp_kws = _EXPERIENCE_KEYWORDS.get(experience, [])
        total_signals += 1
        if exp_kws:
            if any(kw in full_text for kw in exp_kws):
                signals_hit += 1
                signal_details["experience_level"] = f"FOUND ({experience})"
            else:
                signal_details["experience_level"] = f"NOT FOUND ({experience})"
        else:
            signals_hit += 1
            signal_details["experience_level"] = "OK (no specific keywords)"

        # Signal 4: timeline signals
        open_timeline = (payload.get("open_timeline") or "").strip()
        if open_timeline:
            total_signals += 1
            tl_lower = open_timeline.lower()
            short = any(kw in tl_lower for kw in ["1개월", "2개월", "빠른", "단기"])
            long_ = any(kw in tl_lower for kw in ["6개월", "장기", "여유"])
            target_kws = _TIMELINE_SHORT if short else (_TIMELINE_LONG if long_ else [])
            if target_kws:
                if any(kw in full_text for kw in target_kws):
                    signals_hit += 1
                    signal_details["timeline"] = f"REFLECTED ({open_timeline})"
                else:
                    signal_details["timeline"] = f"NOT REFLECTED ({open_timeline})"
            else:
                signals_hit += 1
                signal_details["timeline"] = "OK (timeline neutral)"

        score = signals_hit / total_signals if total_signals > 0 else 0.0
        return score, {
            "signals_hit": signals_hit,
            "total_signals": total_signals,
            "details": signal_details,
        }

    # ──────────────────────────────────────────────────────────────
    # Helper utilities
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def _collect_actions(steps_payload: list[dict], action_key: str) -> list[dict]:
        """Collect all items from a specific key across all steps."""
        result: list[dict] = []
        for step in steps_payload:
            items = step.get(action_key, [])
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, dict):
                        result.append(item)
                    elif isinstance(item, str):
                        result.append({"title": item})
        return result

    @staticmethod
    def _collect_actions_with_source(steps_payload: list[dict]) -> list[dict]:
        """Collect all action dicts (legal_basis + documents + checklist) with mapping_source."""
        result: list[dict] = []
        step_mapping_source = ""
        for step in steps_payload:
            step_mapping_source = step.get("mapping_source", "")
            for key in ("legal_basis", "documents", "checklist"):
                items = step.get(key, [])
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict):
                            # Inject step-level mapping_source as fallback
                            enriched = dict(item)
                            if "mapping_source" not in enriched and step_mapping_source:
                                enriched["mapping_source"] = step_mapping_source
                            result.append(enriched)
                        elif isinstance(item, str):
                            result.append(
                                {
                                    "title": item,
                                    "mapping_source": step_mapping_source
                                    or "llm_generated",
                                }
                            )
        return result

    @staticmethod
    def _extract_text_set(steps_payload: list[dict], key: str) -> set[str]:
        """Extract all text values from a repeating list field across all steps."""
        texts: set[str] = set()
        for step in steps_payload:
            items = step.get(key, [])
            if isinstance(items, list):
                for item in items:
                    if isinstance(item, str):
                        texts.add(item.strip())
                    elif isinstance(item, dict):
                        for field_ in ("title", "content", "text"):
                            v = item.get(field_)
                            if isinstance(v, str) and v.strip():
                                texts.add(v.strip())
                                break
        return texts

    @staticmethod
    def _jaccard_distance(set_a: set[str], set_b: set[str]) -> float:
        """Compute Jaccard distance between two text sets.

        Returns:
            0.0 if both sets are identical, 1.0 if completely disjoint.
        """
        if not set_a and not set_b:
            return 0.0
        union = set_a | set_b
        intersection = set_a & set_b
        return 1.0 - len(intersection) / len(union)

    @staticmethod
    def _build_analysis(
        checklist_diff: float,
        phase_diff: float,
        risk_diff: float,
        days_diff: float,
        overall: float,
        payload_a: dict,
        payload_b: dict,
    ) -> str:
        """Generate a short analysis text for the personalization comparison."""
        level = "높음" if overall >= 0.5 else ("보통" if overall >= 0.25 else "낮음")
        parts: list[str] = [
            f"개인화 수준: {level} (overall={overall:.2f})",
            f"체크리스트 차이: {checklist_diff:.2f}",
            f"단계 차이: {phase_diff:.2f}",
            f"위험 메모 차이: {risk_diff:.2f}",
            f"예상 일수 차이: {days_diff:.2f}",
        ]

        # Highlight payload differences
        diff_fields: list[str] = []
        for field_ in (
            "business_type",
            "startup_type",
            "experience_level",
            "budget_range",
        ):
            va = payload_a.get(field_, "")
            vb = payload_b.get(field_, "")
            if va != vb:
                diff_fields.append(f"{field_}: '{va}' vs '{vb}'")
        if diff_fields:
            parts.append("입력 차이: " + ", ".join(diff_fields))

        if overall < 0.25:
            parts.append(
                "경고: 두 로드맵이 거의 동일합니다. 개인화가 충분하지 않습니다."
            )

        return " | ".join(parts)


# ─── Module-level helpers ──────────────────────────────────────────


def _flatten_roadmap_text(steps_payload: list[dict]) -> str:
    """Concatenate all text content from a steps_payload into one string."""
    parts: list[str] = []
    for step in steps_payload:
        for key in ("phase", "title", "objective"):
            v = step.get(key, "")
            if v:
                parts.append(str(v))

        for item in step.get("checklist", []):
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(str(item.get("title", "")))

        for item in step.get("legal_basis", []):
            if isinstance(item, dict):
                parts.append(str(item.get("title", "")))
                parts.append(str(item.get("snippet", "")))

        for item in step.get("risk_notes", []):
            if isinstance(item, str):
                parts.append(item)

    return " ".join(parts)


def summarize_eval_result(result: RoadmapEvalResult) -> str:
    """Return a one-line text summary of an evaluation result."""
    return (
        f"overall={result.overall_score():.3f} | "
        f"mapping={result.actionkit_mapping_rate:.3f} | "
        f"accuracy={result.legal_basis_accuracy:.3f} | "
        f"doc_validity={result.document_validity:.3f} | "
        f"success={result.generation_success_rate:.3f} | "
        f"personalization={result.personalization_score:.3f}"
    )
