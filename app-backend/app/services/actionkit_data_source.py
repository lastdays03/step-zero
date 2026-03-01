"""ActionKit 데이터를 LawData 형식으로 제공하는 DataSource.

seed 메타데이터(actionkit_seed_source.py)와 로컬 파일(PDF 파싱)을 결합하여
RAG 인덱싱에 사용할 LawData 리스트를 반환한다.

- PDF(39개): pdfplumber 파싱 + seed 메타데이터 보강
- HWP(6개) + PPTX(1개): seed 메타데이터만 사용 (parse 불가)
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import List

import pdfplumber

from app.core.config import get_settings
from app.core.logging import get_logger
from app.services.law_fetcher import LawData, LawDataSource, SourceType
from scripts.seeds.actionkit_seed_source import ACTION_KIT_DATA, LAW_DATA

logger = get_logger(__name__)

# pdfplumber로 파싱 가능한 확장자
_PARSEABLE_EXTENSIONS = {".pdf"}
# 메타데이터만 사용하는 확장자
_METADATA_ONLY_EXTENSIONS = {".hwp", ".pptx"}


def _file_sha256(path: Path) -> str:
    """파일 SHA256 해시를 계산한다."""
    sha = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest()


def _extract_pdf_text(path: Path, max_pages: int = 10) -> str:
    """PDF에서 텍스트를 추출한다 (최대 N 페이지)."""
    try:
        with pdfplumber.open(path) as pdf:
            pages = pdf.pages[:max_pages]
            return "\n".join(p.extract_text() or "" for p in pages)
    except Exception as e:
        logger.error("PDF 파싱 실패: path=%s, error=%s", path, e)
        return ""


def _build_seed_content(item: dict, *, include_parsed: str = "") -> str:
    """seed 메타데이터로 content_body를 조합한다.

    구조: name + summary + highlights + relatedLaws + parsed_text
    """
    parts = [item.get("name", "")]

    summary = item.get("summary", "")
    if summary:
        parts.append(f"\n{summary}")

    # highlights (LAW_DATA 아이템)
    highlights = item.get("highlights", [])
    if highlights:
        parts.append("\n\n### 핵심 포인트")
        for h in highlights:
            parts.append(f"- {h}")

    # relatedLaws (ACTION_KIT_DATA 아이템)
    related_laws = item.get("relatedLaws", [])
    if related_laws:
        parts.append("\n\n### 관련 법령")
        for rl in related_laws:
            if isinstance(rl, dict):
                name = rl.get("name", "")
                rl_summary = rl.get("summary", "")
                parts.append(f"- {name}: {rl_summary}" if rl_summary else f"- {name}")
            else:
                parts.append(f"- {rl}")

    # 파싱된 원문 (PDF인 경우)
    if include_parsed:
        parts.append(f"\n\n### 원문 발췌\n{include_parsed[:3000]}")

    return "\n".join(parts)


def _strip_path_prefix(path_str: str) -> str:
    """seed 경로에서 'actionkits/files/' 접두사를 제거한다."""
    normalized = path_str.strip().lstrip("/")
    if normalized.startswith("actionkits/files/"):
        return normalized[len("actionkits/files/") :]
    return normalized


class ActionKitDataSource(LawDataSource):
    """ActionKit seed 데이터 + 로컬 파일 파싱을 결합한 DataSource.

    fetch_all_laws()는 46개의 LawData를 반환한다:
    - LAW_DATA: 21개 (6개 챕터)
    - ACTION_KIT_DATA: 25개 (4개 카테고리, "all" 제외)
    """

    def __init__(self, storage_root: Path | None = None):
        settings = get_settings()
        self.storage_root = storage_root or settings.ACTIONKIT_STORAGE_PATH

    def _find_file(
        self, domain: str, category_slug: str, item_index: int, filename: str
    ) -> Path | None:
        """uploads/actionkit/ 아래에서 파일을 찾는다."""
        expected = (
            self.storage_root
            / domain
            / category_slug
            / str(item_index)
            / "v1"
            / filename
        )
        if expected.exists():
            return expected
        return None

    def _process_item(
        self,
        item: dict,
        *,
        domain: str,
        category_slug: str,
        item_index: int,
    ) -> LawData | None:
        """개별 seed 아이템을 LawData로 변환한다."""
        # 파일 이름 추출
        seed_path = item.get("path", "")
        filename = Path(_strip_path_prefix(seed_path)).name if seed_path else ""
        file_type = item.get("type") or item.get("ext", ".pdf").replace(".", "").upper()
        ext = f".{file_type.lower()}" if file_type else ".pdf"

        # 파일 탐색
        file_path = self._find_file(domain, category_slug, item_index, filename)
        parse_status = "metadata_only"
        parsed_text = ""
        file_hash = ""

        if file_path and file_path.exists():
            file_hash = _file_sha256(file_path)
            if ext in _PARSEABLE_EXTENSIONS:
                parsed_text = _extract_pdf_text(file_path)
                if parsed_text.strip():
                    parse_status = "full"

        # content_body 조합
        content_body = _build_seed_content(item, include_parsed=parsed_text)
        if not content_body.strip():
            logger.warning(
                "빈 content_body: domain=%s, name=%s", domain, item.get("name")
            )
            return None

        category = f"actionkit/{domain}/{category_slug}"
        title = item.get("name", filename)

        return LawData(
            title=title,
            category=category,
            content_body=content_body,
            source_type=SourceType.LOCAL,
            file_path=str(file_path) if file_path else None,
            metadata={
                "source": "actionkit",
                "domain": domain,
                "category": category,
                "item_id": item_index,
                "tag": item.get("tag", ""),
                "sha256": file_hash,
                "file_type": file_type,
                "parse_status": parse_status,
            },
        )

    async def fetch_all_laws(self) -> List[LawData]:
        """LAW_DATA + ACTION_KIT_DATA의 전체 아이템을 LawData 리스트로 반환한다."""
        results: list[LawData] = []
        item_index = 1  # seed_actionkit.py와 동일한 순서로 순차 부여

        # 1) LAW_DATA (21개)
        for chapter_slug, chapter in LAW_DATA.items():
            category_slug = f"chapter-{chapter_slug}"
            for item in chapter["items"]:
                law_data = self._process_item(
                    item,
                    domain="laws",
                    category_slug=category_slug,
                    item_index=item_index,
                )
                if law_data:
                    results.append(law_data)
                item_index += 1

        # 2) ACTION_KIT_DATA (25개, "all" 제외)
        for category_slug, category_data in ACTION_KIT_DATA.items():
            if category_slug == "all":
                continue
            for item in category_data["items"]:
                law_data = self._process_item(
                    item,
                    domain="kits",
                    category_slug=category_slug,
                    item_index=item_index,
                )
                if law_data:
                    results.append(law_data)
                item_index += 1

        logger.info(
            "ActionKit 데이터 로드 완료: total=%d, full_parse=%d, metadata_only=%d",
            len(results),
            sum(1 for r in results if r.metadata.get("parse_status") == "full"),
            sum(
                1 for r in results if r.metadata.get("parse_status") == "metadata_only"
            ),
        )
        return results
