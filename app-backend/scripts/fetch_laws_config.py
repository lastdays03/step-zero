"""WAVE_CONFIG: 업종별 법률 수집 대상 매핑.

각 Wave는 우선순위 그룹이며, 업종별로 검색 쿼리와 법령 계층 구조를 정의한다.
hierarchy 값: "법률", "시행령", "시행규칙", "행정규칙"
"""

from __future__ import annotations

WAVE_CONFIG: dict[int, dict[str, list[dict[str, list[str] | str]]]] = {
    1: {
        "식품제조가공업": [
            {
                "query": "식품위생법",
                "hierarchy": ["법률", "시행령", "시행규칙"],
            },
            {
                "query": "식품제조가공업 영업허가",
                "hierarchy": ["행정규칙"],
            },
        ],
        "통신판매업": [
            {
                "query": "전자상거래 등에서의 소비자보호에 관한 법률",
                "hierarchy": ["법률", "시행령", "시행규칙"],
            },
            {
                "query": "통신판매업 신고",
                "hierarchy": ["행정규칙"],
            },
        ],
    },
    2: {
        "미용업": [
            {
                "query": "공중위생관리법",
                "hierarchy": ["법률", "시행령", "시행규칙"],
            },
        ],
        "일반소매업": [
            {
                "query": "유통산업발전법",
                "hierarchy": ["법률", "시행령", "시행규칙"],
            },
        ],
    },
    3: {
        "학원업": [
            {
                "query": "학원의 설립운영 및 과외교습에 관한 법률",
                "hierarchy": ["법률", "시행령", "시행규칙"],
            },
        ],
        "숙박업": [
            {
                "query": "공중위생관리법",
                "hierarchy": ["법률", "시행령", "시행규칙"],
            },
            {
                "query": "관광진흥법",
                "hierarchy": ["법률", "시행령", "시행규칙"],
            },
        ],
    },
}


def get_wave_targets(wave: int) -> dict[str, list[dict]]:
    """특정 Wave의 수집 대상을 반환한다."""
    if wave not in WAVE_CONFIG:
        raise ValueError(
            f"존재하지 않는 Wave: {wave}. 가능한 값: {list(WAVE_CONFIG.keys())}"
        )
    return WAVE_CONFIG[wave]


def get_all_targets() -> dict[str, list[dict]]:
    """모든 Wave의 수집 대상을 하나의 dict로 합쳐서 반환한다."""
    merged: dict[str, list[dict]] = {}
    for wave_targets in WAVE_CONFIG.values():
        for biz_type, queries in wave_targets.items():
            if biz_type in merged:
                merged[biz_type].extend(queries)
            else:
                merged[biz_type] = list(queries)
    return merged


def list_all_queries() -> list[tuple[int, str, str, list[str]]]:
    """(wave, 업종, 검색어, hierarchy) 리스트를 반환한다."""
    results = []
    for wave, biz_map in WAVE_CONFIG.items():
        for biz_type, queries in biz_map.items():
            for q in queries:
                results.append((wave, biz_type, q["query"], q["hierarchy"]))
    return results
