"""국가법령정보센터 API 클라이언트 유닛 테스트.

실제 외부 API 호출 없이 httpx 응답을 mock하여 테스트한다.
"""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.services.law_api_client import (
    AdminRuleResult,
    LawApiClient,
    LawApiError,
    LawArticle,
    LawFullText,
    LawSearchResult,
    _extract_items,
    _parse_articles_from_response,
    _safe_int,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def client():
    """OC를 직접 주입하여 settings 의존성 제거."""
    return LawApiClient(oc="test_oc")


# ---------------------------------------------------------------------------
# _safe_int
# ---------------------------------------------------------------------------

class TestSafeInt:
    def test_int_value(self):
        assert _safe_int(42) == 42

    def test_str_value(self):
        assert _safe_int("123") == 123

    def test_none(self):
        assert _safe_int(None) == 0

    def test_invalid(self):
        assert _safe_int("abc") == 0


# ---------------------------------------------------------------------------
# _extract_items
# ---------------------------------------------------------------------------

class TestExtractItems:
    def test_nested_list(self):
        data = {"LawSearch": {"law": [{"a": 1}, {"a": 2}]}}
        assert _extract_items(data, "law") == [{"a": 1}, {"a": 2}]

    def test_nested_single_dict(self):
        """단일 결과는 dict로 오는 경우 → list로 wrapping."""
        data = {"LawSearch": {"law": {"a": 1}}}
        assert _extract_items(data, "law") == [{"a": 1}]

    def test_top_level_key(self):
        data = {"law": [{"a": 1}]}
        assert _extract_items(data, "law") == [{"a": 1}]

    def test_empty(self):
        data = {"LawSearch": {"totalCnt": 0}}
        assert _extract_items(data, "law") == []


# ---------------------------------------------------------------------------
# LawSearchResult model
# ---------------------------------------------------------------------------

class TestLawSearchResult:
    def test_from_alias(self):
        item = LawSearchResult(**{
            "법령ID": "001805",
            "법령일련번호": 277149,
            "법령명한글": "식품위생법",
            "법령구분명": "법률",
            "공포일자": "20240101",
            "시행일자": "20240701",
        })
        assert item.law_name == "식품위생법"
        assert item.law_id == "001805"
        assert item.law_mst == 277149
        assert item.law_type == "법률"

    def test_defaults(self):
        item = LawSearchResult()
        assert item.law_id == ""
        assert item.law_name == ""


# ---------------------------------------------------------------------------
# LawArticle model
# ---------------------------------------------------------------------------

class TestLawArticle:
    def test_from_alias(self):
        item = LawArticle(**{
            "조문번호": "1",
            "조문제목": "목적",
            "조문내용": "이 법은 ...",
        })
        assert item.article_no == "1"
        assert item.article_title == "목적"
        assert item.article_content == "이 법은 ..."


# ---------------------------------------------------------------------------
# AdminRuleResult model
# ---------------------------------------------------------------------------

class TestAdminRuleResult:
    def test_from_alias(self):
        item = AdminRuleResult(**{
            "행정규칙명": "식품안전관리지침",
            "행정규칙종류": "훈령",
            "행정규칙일련번호": 111,
            "발령기관명": "식약처",
            "시행일자": "20240301",
        })
        assert item.rule_name == "식품안전관리지침"
        assert item.rule_type == "훈령"


# ---------------------------------------------------------------------------
# LawApiClient - init
# ---------------------------------------------------------------------------

class TestClientInit:
    def test_no_oc_raises(self):
        with patch("app.services.law_api_client.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(LAW_API_OC=None)
            with pytest.raises(ValueError, match="LAW_API_OC"):
                LawApiClient()

    def test_explicit_oc(self):
        c = LawApiClient(oc="my_oc")
        assert c._oc == "my_oc"


# ---------------------------------------------------------------------------
# LawApiClient - search_laws
# ---------------------------------------------------------------------------

class TestSearchLaws:
    @pytest.mark.asyncio
    async def test_success(self, client: LawApiClient):
        mock_resp = httpx.Response(
            200,
            json={
                "LawSearch": {
                    "law": [
                        {
                            "법령일련번호": 1,
                            "법령명한글": "식품위생법",
                            "법령MST": 100,
                            "법령구분명": "법률",
                            "공포일자": "20240101",
                            "시행일자": "20240701",
                        }
                    ]
                }
            },
            request=httpx.Request("GET", "http://test"),
        )
        with patch.object(client, "_get_client") as mock_get:
            mock_http = AsyncMock()
            mock_http.get = AsyncMock(return_value=mock_resp)
            mock_get.return_value = mock_http

            results = await client.search_laws("식품위생법")

        assert len(results) == 1
        assert isinstance(results[0], LawSearchResult)
        assert results[0].law_name == "식품위생법"

    @pytest.mark.asyncio
    async def test_empty_results(self, client: LawApiClient):
        mock_resp = httpx.Response(
            200,
            json={"LawSearch": {"totalCnt": 0}},
            request=httpx.Request("GET", "http://test"),
        )
        with patch.object(client, "_get_client") as mock_get:
            mock_http = AsyncMock()
            mock_http.get = AsyncMock(return_value=mock_resp)
            mock_get.return_value = mock_http

            results = await client.search_laws("없는법률")

        assert results == []


# ---------------------------------------------------------------------------
# _parse_articles_from_response
# ---------------------------------------------------------------------------

class TestParseArticlesFromResponse:
    def test_basic_articles(self):
        law_data = {
            "조문": {
                "조문단위": [
                    {"조문번호": "1", "조문제목": "목적", "조문내용": "이 법은...", "조문여부": "조문"},
                    {"조문번호": "2", "조문제목": "정의", "조문내용": "용어 정의", "조문여부": "조문"},
                ]
            }
        }
        articles = _parse_articles_from_response(law_data)
        assert len(articles) == 2
        assert isinstance(articles[0], LawArticle)
        assert articles[0].article_title == "목적"

    def test_filters_non_articles(self):
        law_data = {
            "조문": {
                "조문단위": [
                    {"조문번호": "1", "조문내용": "제1장 총칙", "조문여부": "전문"},
                    {"조문번호": "1", "조문제목": "목적", "조문내용": "이 법은...", "조문여부": "조문"},
                ]
            }
        }
        articles = _parse_articles_from_response(law_data)
        assert len(articles) == 1

    def test_empty(self):
        articles = _parse_articles_from_response({})
        assert articles == []


# ---------------------------------------------------------------------------
# LawApiClient - get_law_full_text
# ---------------------------------------------------------------------------

class TestGetLawFullText:
    @pytest.mark.asyncio
    async def test_success(self, client: LawApiClient):
        mock_resp = httpx.Response(
            200,
            json={
                "법령": {
                    "기본정보": {
                        "법령명_한글": "식품위생법",
                        "법령ID": "001805",
                        "시행일자": "20240701",
                    },
                    "조문": {
                        "조문단위": [
                            {"조문번호": "1", "조문제목": "목적", "조문내용": "내용1", "조문여부": "조문"},
                        ]
                    },
                }
            },
            request=httpx.Request("GET", "http://test"),
        )

        with patch.object(client, "_get_client") as mock_get_client:
            mock_http = AsyncMock()
            mock_http.get = AsyncMock(return_value=mock_resp)
            mock_get_client.return_value = mock_http

            result = await client.get_law_full_text("100")

        assert isinstance(result, LawFullText)
        assert result.law_name == "식품위생법"
        assert result.law_id == 1805
        assert len(result.articles) == 1


# ---------------------------------------------------------------------------
# LawApiClient - search_admin_rules
# ---------------------------------------------------------------------------

class TestSearchAdminRules:
    @pytest.mark.asyncio
    async def test_success(self, client: LawApiClient):
        mock_resp = httpx.Response(
            200,
            json={
                "AdmRulSearch": {
                    "admrul": [
                        {
                            "행정규칙명": "식품안전관리지침",
                            "행정규칙종류": "훈령",
                            "행정규칙일련번호": 111,
                            "발령기관명": "식약처",
                            "시행일자": "20240301",
                        }
                    ]
                }
            },
            request=httpx.Request("GET", "http://test"),
        )
        with patch.object(client, "_get_client") as mock_get:
            mock_http = AsyncMock()
            mock_http.get = AsyncMock(return_value=mock_resp)
            mock_get.return_value = mock_http

            results = await client.search_admin_rules("식품안전")

        assert len(results) == 1
        assert isinstance(results[0], AdminRuleResult)
        assert results[0].rule_name == "식품안전관리지침"


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

class TestErrorHandling:
    @pytest.mark.asyncio
    async def test_timeout(self, client: LawApiClient):
        with patch.object(client, "_get_client") as mock_get:
            mock_http = AsyncMock()
            mock_http.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            mock_get.return_value = mock_http

            with pytest.raises(LawApiError, match="timed out"):
                await client.search_laws("test")

    @pytest.mark.asyncio
    async def test_http_error(self, client: LawApiClient):
        mock_resp = httpx.Response(
            500,
            request=httpx.Request("GET", "http://test"),
        )
        with patch.object(client, "_get_client") as mock_get:
            mock_http = AsyncMock()
            mock_http.get = AsyncMock(return_value=mock_resp)
            mock_get.return_value = mock_http

            with pytest.raises(LawApiError, match="HTTP 500"):
                await client.search_laws("test")

    @pytest.mark.asyncio
    async def test_json_parse_error(self, client: LawApiClient):
        mock_resp = MagicMock(spec=httpx.Response)
        mock_resp.status_code = 200
        mock_resp.raise_for_status = MagicMock()
        mock_resp.json = MagicMock(side_effect=ValueError("bad json"))
        mock_resp.text = "<html>error</html>"

        with patch.object(client, "_get_client") as mock_get:
            mock_http = AsyncMock()
            mock_http.get = AsyncMock(return_value=mock_resp)
            mock_get.return_value = mock_http

            with pytest.raises(LawApiError, match="parse JSON"):
                await client.search_laws("test")


# ---------------------------------------------------------------------------
# Context manager
# ---------------------------------------------------------------------------

class TestContextManager:
    @pytest.mark.asyncio
    async def test_async_context(self):
        async with LawApiClient(oc="test") as c:
            assert c._oc == "test"

    @pytest.mark.asyncio
    async def test_close(self):
        c = LawApiClient(oc="test")
        # _client is lazily created, so closing without init is safe
        await c.close()
        assert c._client is None
