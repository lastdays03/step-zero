#!/usr/bin/env python3
"""청킹 품질 검증 스크립트.

10개 샘플 PDF에서 텍스트를 추출하고, VectorStoreService의 청킹 로직과
동일한 splitter를 적용하여 청크 경계의 적절성을 검증한다.

Usage:
    cd app-backend
    python -m scripts.verify_chunking
"""

from __future__ import annotations

from pathlib import Path

import pdfplumber
from langchain_text_splitters import RecursiveCharacterTextSplitter

# 청킹 파라미터 (VectorStoreService와 동일)
splitter = RecursiveCharacterTextSplitter(
    chunk_size=600,
    chunk_overlap=100,
    separators=["\n\n", "\n", ".", " "],
)

# 검증 대상 10개 샘플 (다양한 도메인/길이)
SAMPLE_PDFS = [
    # Chapter 1: 입지 적법성
    "uploads/actionkit/laws/chapter-1/1/v1/건축법(법률)(제21035호)(20260227).pdf",
    "uploads/actionkit/laws/chapter-1/2/v1/국토의 계획 및 이용에 관한 법률(법률)(제21169호)(20260603).pdf",
    # Chapter 2: 영업 성립 요건
    "uploads/actionkit/laws/chapter-2/6/v1/식품위생법(법률)(제21299호)(20261231).pdf",
    # Chapter 3: 안전소방
    "uploads/actionkit/laws/chapter-3/9/v1/소방시설 설치 및 관리에 관한 법률(법률)(제18522호)(20241201).pdf",
    # Chapter 4: 영업 중 준수의무
    "uploads/actionkit/laws/chapter-4/14/v1/부가가치세법(법률)(제21065호)(20260102).pdf",
    # Chapter 5: 위반 시 대응
    "uploads/actionkit/laws/chapter-5/15/v1/행정조사기본법(법률)(제19213호)(20240118).pdf",
    # Chapter 6: 행정처분 및 구제
    "uploads/actionkit/laws/chapter-6/16/v1/행정기본법(법률)(제20824호)(20260319).pdf",
    "uploads/actionkit/laws/chapter-6/17/v1/행정절차법(법률)(제18748호)(20230324).pdf",
    "uploads/actionkit/laws/chapter-6/20/v1/행정소송법(법률)(제14839호)(20170726).pdf",
    # Kit 도메인 (세무)
    "uploads/actionkit/kits/tax/33/v1/부가가치세법(법률)(제21065호)(20260102).pdf",
]

BACKEND_ROOT = Path(__file__).resolve().parents[1]


def extract_pdf_text(pdf_path: Path, max_pages: int = 5) -> str:
    """PDF에서 텍스트 추출 (최대 N 페이지)."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages = pdf.pages[:max_pages]
            return "\n".join(p.extract_text() or "" for p in pages)
    except Exception as e:
        return f"[ERROR] {e}"


def simulate_etl_content(title: str, raw_text: str) -> str:
    """ETL 결과물 형식으로 시뮬레이션.

    실제 VectorStoreService._build_content()와 동일 포맷:
      {title}\n\n{guide_text}\n\n[Reference]\n{law_reference}
    """
    # 실제 ETL은 LLM으로 구조화하지만, 청킹 검증에서는 원문을 그대로 사용
    truncated = raw_text[:3000]  # ETL은 10000자까지 처리
    return f"{title}\n\n{truncated}\n\n[Reference]\n{title} 전문 참조"


def verify():
    print("=" * 70)
    print("VectorStoreService 청킹 품질 검증")
    print(f"chunk_size={splitter._chunk_size}, chunk_overlap={splitter._chunk_overlap}")
    print("=" * 70)

    total_docs = 0
    total_chunks = 0
    issues = []

    for rel_path in SAMPLE_PDFS:
        pdf_path = BACKEND_ROOT / rel_path
        if not pdf_path.exists():
            print(f"\n[SKIP] 파일 없음: {rel_path}")
            continue

        title = pdf_path.stem
        raw_text = extract_pdf_text(pdf_path)
        if not raw_text.strip():
            print(f"\n[SKIP] 텍스트 추출 실패: {title}")
            continue

        content = simulate_etl_content(title, raw_text)
        chunks = splitter.split_text(content)

        total_docs += 1
        total_chunks += len(chunks)

        print(f"\n--- [{total_docs}] {title[:50]} ---")
        print(f"  원문 길이: {len(content):,} chars → {len(chunks)} 청크")

        for i, chunk in enumerate(chunks):
            # 청크 경계 품질 지표
            starts_mid_sentence = (
                not chunk[0].isupper()
                and chunk[0] not in "가나다라마바사아자차카타파하[#-•·"
            )
            ends_mid_word = chunk[-1] not in ".!?\n다요함됨음임)】"

            quality_flags = []
            if starts_mid_sentence and i > 0:
                quality_flags.append("MID-START")
            if ends_mid_word and i < len(chunks) - 1:
                quality_flags.append("MID-END")

            flags_str = f" ⚠️ {', '.join(quality_flags)}" if quality_flags else ""
            print(
                f"  chunk[{i}]: {len(chunk):>4} chars | "
                f"시작: {chunk[:30].replace(chr(10), '↵')!r} | "
                f"끝: ...{chunk[-30:].replace(chr(10), '↵')!r}{flags_str}"
            )

            if quality_flags:
                issues.append((title[:30], i, quality_flags))

    print("\n" + "=" * 70)
    print(
        f"요약: {total_docs}개 문서 → {total_chunks}개 청크 (평균 {total_chunks/max(total_docs,1):.1f})"
    )
    if issues:
        print(f"\n⚠️ 경계 이슈 {len(issues)}건:")
        for title, idx, flags in issues:
            print(f"  - {title} chunk[{idx}]: {', '.join(flags)}")
    else:
        print("\n✅ 모든 청크 경계가 양호합니다.")
    print("=" * 70)


if __name__ == "__main__":
    verify()
