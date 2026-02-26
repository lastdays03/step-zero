"""국가법령정보센터 Open API 클라이언트 래퍼."""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
from pydantic import BaseModel, Field

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Response Models
# ---------------------------------------------------------------------------

class LawSearchResult(BaseModel):
    """법령검색 결과 항목."""
    law_id: str = Field("", alias="법령ID")
    law_name: str = Field("", alias="법령명한글")
    law_mst: int = Field(0, alias="법령일련번호")
    law_type: str = Field("", alias="법령구분명")
    promulgation_date: str = Field("", alias="공포일자")
    enforcement_date: str = Field("", alias="시행일자")

    model_config = {"populate_by_name": True}


class LawArticle(BaseModel):
    """조문 항목."""
    article_no: str = Field("", alias="조문번호")
    article_title: str = Field("", alias="조문제목")
    article_content: str = Field("", alias="조문내용")

    model_config = {"populate_by_name": True}


class LawFullText(BaseModel):
    """법령 본문 (기본정보 + 조문 목록)."""
    law_name: str = Field("")
    law_id: int = Field(0)
    mst: int = Field(0)
    enforcement_date: str = Field("")
    articles: list[LawArticle] = Field(default_factory=list)


class AdminRuleResult(BaseModel):
    """행정규칙 검색 결과 항목."""
    rule_name: str = Field("", alias="행정규칙명")
    rule_type: str = Field("", alias="행정규칙종류")
    rule_id: int = Field(0, alias="행정규칙일련번호")
    issuing_org: str = Field("", alias="발령기관명")
    enforcement_date: str = Field("", alias="시행일자")

    model_config = {"populate_by_name": True}


# ---------------------------------------------------------------------------
# API Client
# ---------------------------------------------------------------------------

_BASE_URL = "http://www.law.go.kr/DRF"

# Rate-limit: max 2 concurrent requests, 0.5s between requests
_SEMAPHORE_LIMIT = 2
_REQUEST_INTERVAL = 0.5


class LawApiError(Exception):
    """국가법령정보센터 API 호출 중 발생하는 에러."""


class LawApiClient:
    """httpx 기반 국가법령정보센터 Open API 비동기 클라이언트."""

    def __init__(self, oc: str | None = None):
        self._oc = oc or get_settings().LAW_API_OC
        if not self._oc:
            raise ValueError("LAW_API_OC is not configured")
        self._semaphore = asyncio.Semaphore(_SEMAPHORE_LIMIT)
        self._client: httpx.AsyncClient | None = None

    # -- lifecycle -----------------------------------------------------------

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def __aenter__(self) -> LawApiClient:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()

    # -- internal helpers ----------------------------------------------------

    async def _request(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        async with self._semaphore:
            client = await self._get_client()
            try:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
            except httpx.TimeoutException as exc:
                logger.error("API 타임아웃: url=%s, params=%s", url, params)
                raise LawApiError(f"Request timed out: {url}") from exc
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "HTTP 에러: status=%s, url=%s",
                    exc.response.status_code,
                    url,
                )
                raise LawApiError(
                    f"HTTP {exc.response.status_code}: {url}"
                ) from exc

            # rate-limit delay
            await asyncio.sleep(_REQUEST_INTERVAL)

            try:
                data = resp.json()
            except Exception as exc:
                logger.error("JSON 파싱 실패: url=%s, body=%s", url, resp.text[:200])
                raise LawApiError("Failed to parse JSON response") from exc

            return data

    # -- public API ----------------------------------------------------------

    async def search_laws(
        self,
        query: str,
        display: int = 20,
        page: int = 1,
    ) -> list[LawSearchResult]:
        """법령 검색."""
        params = {
            "OC": self._oc,
            "target": "law",
            "type": "JSON",
            "query": query,
            "display": display,
            "page": page,
        }
        data = await self._request(f"{_BASE_URL}/lawSearch.do", params)
        items = _extract_items(data, "law")
        return [LawSearchResult(**item) for item in items]

    async def get_law_full_text(self, mst: str) -> LawFullText:
        """법령 본문 조회. target=law 응답에서 기본정보 + 조문을 함께 파싱한다."""
        params = {
            "OC": self._oc,
            "target": "law",
            "MST": mst,
            "type": "JSON",
        }
        data = await self._request(f"{_BASE_URL}/lawService.do", params)

        # 응답 구조: {"법령": {"기본정보": {...}, "조문": {"조문단위": [...]}}}
        law_data = data.get("법령", data)
        base = law_data.get("기본정보", {})
        articles = _parse_articles_from_response(law_data)

        return LawFullText(
            law_name=base.get("법령명_한글", ""),
            law_id=_safe_int(base.get("법령ID", 0)),
            mst=_safe_int(mst),
            enforcement_date=base.get("시행일자", ""),
            articles=articles,
        )

    async def search_admin_rules(
        self,
        query: str,
        display: int = 20,
        page: int = 1,
    ) -> list[AdminRuleResult]:
        """행정규칙 검색."""
        params = {
            "OC": self._oc,
            "target": "admrul",
            "type": "JSON",
            "query": query,
            "display": display,
            "page": page,
        }
        data = await self._request(f"{_BASE_URL}/lawSearch.do", params)
        items = _extract_items(data, "admrul")
        return [AdminRuleResult(**item) for item in items]


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _safe_int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _parse_articles_from_response(law_data: dict[str, Any]) -> list[LawArticle]:
    """target=law 응답의 조문단위 리스트에서 LawArticle 목록을 생성한다."""
    jo_section = law_data.get("조문", {})
    units = jo_section.get("조문단위", [])
    if isinstance(units, dict):
        units = [units]

    articles: list[LawArticle] = []
    for unit in units:
        if unit.get("조문여부") != "조문":
            continue

        content = _build_article_content(unit)
        articles.append(LawArticle(
            조문번호=unit.get("조문번호", ""),
            조문제목=unit.get("조문제목", ""),
            조문내용=content,
        ))
    return articles


def _build_article_content(unit: dict[str, Any]) -> str:
    """조문단위 dict에서 조문내용 + 항 + 호를 합쳐 본문 텍스트를 만든다."""
    lines: list[str] = []

    main = unit.get("조문내용", "")
    if main:
        lines.append(main.strip())

    # 항 (paragraphs)
    paragraphs = unit.get("항", [])
    if isinstance(paragraphs, dict):
        paragraphs = [paragraphs]
    for para in paragraphs:
        para_text = para.get("항내용", "")
        if para_text:
            lines.append(para_text.strip())
        # 호 (items)
        items = para.get("호", [])
        if isinstance(items, dict):
            items = [items]
        for item in items:
            item_text = item.get("호내용", "")
            if item_text:
                lines.append(f"  {item_text.strip()}")

    return "\n".join(lines)


def _extract_items(data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    """API 응답에서 항목 리스트를 추출.

    국가법령정보 API 응답 구조가 다양하므로 여러 패턴에 대응한다.
    """
    # 패턴 1: {"LawSearch": {"law": [...]}}  또는 {"LawSearch": {"law": {...}}}
    for top_key in data:
        inner = data[top_key]
        if isinstance(inner, dict) and key in inner:
            val = inner[key]
            return val if isinstance(val, list) else [val]

    # 패턴 2: 최상위에 key 존재
    if key in data:
        val = data[key]
        return val if isinstance(val, list) else [val]

    # 패턴 3: 결과 없음
    logger.debug("응답에 '%s' 키 없음: keys=%s", key, list(data.keys()))
    return []
