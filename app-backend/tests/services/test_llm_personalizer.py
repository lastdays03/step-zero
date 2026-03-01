"""Tests for LLMPersonalizer reference validation and fuzzy matching."""

from dataclasses import dataclass, field

import pytest

from app.features.roadmaps.application.llm_personalizer import (
    LLMPersonalizer,
    PersonalizedStepDetail,
)

# ── Minimal stubs for ActionKit models ──


@dataclass
class _StubItem:
    id: int | None = None
    domain: str = "laws"
    name: str = ""
    summary: str = ""


@dataclass
class _StubLaw:
    law_name: str = ""
    law_summary: str | None = None


@dataclass
class _StubFile:
    id: int | None = None
    object_key: str = ""
    original_filename: str | None = None


@dataclass
class _StubMatched:
    item: _StubItem = field(default_factory=_StubItem)
    highlights: list = field(default_factory=list)
    related_laws: list = field(default_factory=list)
    files: list = field(default_factory=list)
    phase_group: str = ""
    relevance_score: float = 0.0


# ── Helper ──


def _make_matched(
    item_id: int,
    laws: list[tuple[str, str]] | None = None,
    files: list[tuple[int, str, str]] | None = None,
) -> _StubMatched:
    item = _StubItem(id=item_id, name=f"Item {item_id}")
    related_laws = [_StubLaw(law_name=n, law_summary=s) for n, s in (laws or [])]
    file_list = [
        _StubFile(id=fid, object_key=key, original_filename=fname)
        for fid, key, fname in (files or [])
    ]
    return _StubMatched(item=item, related_laws=related_laws, files=file_list)


# ============================================================
# TestValidateAndRepairReferences
# ============================================================


class TestValidateAndRepairReferences:
    """Test suite for _validate_and_repair_references."""

    def _matched_items(self):
        return [
            _make_matched(
                item_id=10,
                laws=[("식품위생법", "영업신고 필요")],
                files=[(100, "laws/food/hygiene.pdf", "식품위생법.pdf")],
            ),
            _make_matched(
                item_id=20,
                laws=[("공중위생관리법", "위생 관리 의무")],
                files=[(200, "laws/health/public.pdf", "공중위생관리법.pdf")],
            ),
        ]

    def test_valid_references_pass_through(self):
        """References with correct item_ids and titles should pass unchanged."""
        matched = self._matched_items()
        details = [
            PersonalizedStepDetail(
                phase="인허가",
                legal_basis=[
                    {"title": "식품위생법", "snippet": "ok", "actionkit_item_id": 10},
                ],
                documents=[
                    {
                        "name": "식품위생법.pdf",
                        "file_url": "laws/food/hygiene.pdf",
                        "actionkit_item_id": 10,
                    },
                ],
                actionkit_items=[10],
            ),
        ]
        result = LLMPersonalizer._validate_and_repair_references(details, matched)
        assert len(result) == 1
        assert result[0].legal_basis[0]["title"] == "식품위생법"
        assert result[0].documents[0]["file_url"] == "laws/food/hygiene.pdf"

    def test_repair_via_item_id(self):
        """If item_id is valid but title was modified by LLM, restore original."""
        matched = self._matched_items()
        details = [
            PersonalizedStepDetail(
                phase="인허가",
                legal_basis=[
                    {
                        "title": "식품 위생법 시행규칙",
                        "snippet": "변조됨",
                        "actionkit_item_id": 10,
                    },
                ],
                documents=[
                    {
                        "name": "wrong.pdf",
                        "file_url": "wrong/path.pdf",
                        "actionkit_item_id": 10,
                    },
                ],
                actionkit_items=[10],
            ),
        ]
        result = LLMPersonalizer._validate_and_repair_references(details, matched)
        # Title should be repaired to original
        assert result[0].legal_basis[0]["title"] == "식품위생법"
        # File should be repaired to original
        assert result[0].documents[0]["file_url"] == "laws/food/hygiene.pdf"

    def test_repair_via_reverse_mapping(self):
        """If item_id is invalid but title exists in originals, reverse-map it."""
        matched = self._matched_items()
        details = [
            PersonalizedStepDetail(
                phase="인허가",
                legal_basis=[
                    {
                        "title": "공중위생관리법",
                        "snippet": "ok",
                        "actionkit_item_id": 999,
                    },
                ],
                documents=[
                    {
                        "name": "공중위생관리법.pdf",
                        "file_url": "laws/health/public.pdf",
                        "actionkit_item_id": 999,
                    },
                ],
            ),
        ]
        result = LLMPersonalizer._validate_and_repair_references(details, matched)
        assert result[0].legal_basis[0]["actionkit_item_id"] == 20
        assert result[0].documents[0]["actionkit_item_id"] == 20

    def test_hallucination_removed_with_valid_remaining(self):
        """Hallucinated entries removed when valid ones remain."""
        matched = self._matched_items()
        details = [
            PersonalizedStepDetail(
                phase="인허가",
                legal_basis=[
                    {
                        "title": "존재하지않는법률",
                        "snippet": "hallucinated",
                        "actionkit_item_id": 999,
                    },
                    {"title": "식품위생법", "snippet": "ok", "actionkit_item_id": 10},
                ],
                documents=[
                    {
                        "name": "fake.pdf",
                        "file_url": "fake/path.pdf",
                        "actionkit_item_id": 999,
                    },
                    {
                        "name": "식품위생법.pdf",
                        "file_url": "laws/food/hygiene.pdf",
                        "actionkit_item_id": 10,
                    },
                ],
            ),
        ]
        result = LLMPersonalizer._validate_and_repair_references(details, matched)
        # Hallucinated law removed, valid one kept
        assert len(result[0].legal_basis) == 1
        assert result[0].legal_basis[0]["title"] == "식품위생법"
        # Hallucinated doc removed, valid one kept
        assert len(result[0].documents) == 1
        assert result[0].documents[0]["file_url"] == "laws/food/hygiene.pdf"

    def test_all_hallucinated_preserves_originals(self):
        """When all entries are hallucinated, originals are preserved to prevent data loss."""
        matched = self._matched_items()
        details = [
            PersonalizedStepDetail(
                phase="인허가",
                legal_basis=[
                    {
                        "title": "존재하지않는법률",
                        "snippet": "hallucinated",
                        "actionkit_item_id": 999,
                    },
                ],
                documents=[
                    {
                        "name": "fake.pdf",
                        "file_url": "fake/path.pdf",
                        "actionkit_item_id": 999,
                    },
                ],
            ),
        ]
        result = LLMPersonalizer._validate_and_repair_references(details, matched)
        # Defensive: originals preserved when all entries would be removed
        assert len(result[0].legal_basis) == 1
        assert len(result[0].documents) == 1

    def test_invalid_actionkit_items_filtered(self):
        """Invalid actionkit_items IDs should be filtered out."""
        matched = self._matched_items()
        details = [
            PersonalizedStepDetail(
                phase="인허가",
                actionkit_items=[10, 999, 20, 888],
            ),
        ]
        result = LLMPersonalizer._validate_and_repair_references(details, matched)
        assert result[0].actionkit_items == [10, 20]

    def test_empty_matched_items_preserves_originals(self):
        """With no matched items, originals are preserved (defensive behavior)."""
        details = [
            PersonalizedStepDetail(
                phase="인허가",
                legal_basis=[
                    {"title": "식품위생법", "snippet": "ok", "actionkit_item_id": 10},
                ],
            ),
        ]
        result = LLMPersonalizer._validate_and_repair_references(details, [])
        # Defensive: when no matches exist, originals are preserved
        assert len(result[0].legal_basis) == 1


# ============================================================
# TestFuzzyMatching
# ============================================================


class TestFuzzyMatching:
    """Test suite for fuzzy matching helpers."""

    def test_exact_law_name_match(self):
        law_names = {"식품위생법", "공중위생관리법"}
        assert (
            LLMPersonalizer._fuzzy_match_law_name("식품위생법", law_names)
            == "식품위생법"
        )

    def test_substring_law_name_match(self):
        law_names = {"식품위생법", "공중위생관리법"}
        # "식품위생법 시행규칙" contains "식품위생법" as substring -> should match
        result = LLMPersonalizer._fuzzy_match_law_name("식품위생법 시행규칙", law_names)
        assert result == "식품위생법"

    def test_no_law_name_match(self):
        law_names = {"식품위생법", "공중위생관리법"}
        result = LLMPersonalizer._fuzzy_match_law_name("완전히다른법률", law_names)
        assert result is None

    def test_empty_title_returns_none(self):
        assert LLMPersonalizer._fuzzy_match_law_name("", {"식품위생법"}) is None

    def test_empty_set_returns_none(self):
        assert LLMPersonalizer._fuzzy_match_law_name("식품위생법", set()) is None

    def test_exact_file_key_match(self):
        file_keys = {"laws/food/hygiene.pdf", "laws/health/public.pdf"}
        result = LLMPersonalizer._fuzzy_match_file_key(
            "laws/food/hygiene.pdf", file_keys
        )
        assert result == "laws/food/hygiene.pdf"

    def test_basename_file_key_match(self):
        file_keys = {"laws/food/hygiene.pdf", "laws/health/public.pdf"}
        result = LLMPersonalizer._fuzzy_match_file_key(
            "wrong/path/hygiene.pdf", file_keys
        )
        assert result == "laws/food/hygiene.pdf"

    def test_substring_file_key_match(self):
        file_keys = {"laws/food/hygiene.pdf"}
        result = LLMPersonalizer._fuzzy_match_file_key("hygiene.pdf", file_keys)
        assert result == "laws/food/hygiene.pdf"

    def test_no_file_key_match(self):
        file_keys = {"laws/food/hygiene.pdf"}
        result = LLMPersonalizer._fuzzy_match_file_key(
            "totally_different.docx", file_keys
        )
        assert result is None

    def test_empty_url_returns_none(self):
        assert (
            LLMPersonalizer._fuzzy_match_file_key("", {"laws/food/hygiene.pdf"}) is None
        )

    def test_empty_set_returns_none_for_file(self):
        assert LLMPersonalizer._fuzzy_match_file_key("hygiene.pdf", set()) is None


# ============================================================
# TestBuildRepairIndexes
# ============================================================


class TestBuildRepairIndexes:
    """Test _build_repair_indexes produces correct lookup structures."""

    def test_basic_indexes(self):
        matched = [
            _make_matched(
                item_id=10,
                laws=[("식품위생법", "영업신고")],
                files=[(100, "food/hygiene.pdf", "식품위생법.pdf")],
            ),
        ]
        idx = LLMPersonalizer._build_repair_indexes(matched)
        assert 10 in idx["valid_item_ids"]
        assert "식품위생법" in idx["law_name_set"]
        assert "food/hygiene.pdf" in idx["file_key_set"]
        assert idx["law_name_to_item_id"]["식품위생법"] == 10
        assert idx["file_key_to_item_id"]["food/hygiene.pdf"] == 10

    def test_none_item_id_skipped(self):
        matched = [_StubMatched(item=_StubItem(id=None))]
        idx = LLMPersonalizer._build_repair_indexes(matched)
        assert len(idx["valid_item_ids"]) == 0
