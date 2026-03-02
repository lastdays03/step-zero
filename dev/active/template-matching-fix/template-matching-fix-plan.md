# 템플릿 매칭 로직 수정 계획

Last Updated: 2026-03-02

## Executive Summary

로드맵 생성 시 `TemplateResolver.resolve()` 매칭 우선순위에 **업종+창업형태(btype+stype)** 조합이 누락되어 있어, 해당 조합의 범용 템플릿을 만들어도 매칭이 되지 않는 문제를 수정한다. 4단계 → 5단계 우선순위로 확장.

## 현재 상태 분석

### 매칭 로직 (`template_resolver.py:20-90`)

현재 `TemplateResolver.resolve()`는 4단계 우선순위로 APPROVED 템플릿을 매칭:

```
1순위: btype + smethod + stype    (정확 매칭)
2순위: btype + smethod + NULL     (방식 기준, 형태 무관)
3순위: btype + NULL    + NULL     (업종 기준, 공통 폴백)
4순위: None                       (기존 파이프라인 사용)
```

### 발견된 문제

| ID | 유형 | 설명 |
|----|------|------|
| ISSUE-1 | 데이터 | 로드맵 `c01797ec`이 startup_type=개인사업자인데 template_id=6(법인용)이 할당됨. 이전 코드 버전에서 발생한 역사적 데이터 문제 |
| ISSUE-2 | 코드 | `btype + stype (smethod=NULL)` 매칭 조합이 누락. 업종+형태 범용 템플릿 생성 불가 |
| ISSUE-3 | 운영 | 모든 기존 템플릿이 smethod/stype 둘 다 채워져 있어 3순위(업종만) 폴백이 실질적으로 작동 불가 |

### 현재 DB 상태

| ID | business_type | startup_method | startup_type | status | 매칭 가능? |
|----|---------------|---------------|-------------|--------|----------|
| 5 | 통신판매업 | 신규 창업 | 개인사업자 | REVIEW | X |
| 6 | 통신판매업 | 신규 창업 | 법인 | APPROVED | O |
| 7 | 휴게음식점 | 양수양도 | 개인사업자 | DRAFT | X |

→ APPROVED 템플릿 1개뿐. 통신판매업+신규 창업+법인 조합에서만 템플릿 경로 동작.

## 수정 후 목표 상태

### 새 매칭 우선순위 (5단계)

```
1순위: btype + smethod + stype    (정확 매칭)
2순위: btype + smethod + NULL     (방식 기준, 형태 무관)
3순위: btype + NULL    + stype    (형태 기준, 방식 무관)  ← 신규
4순위: btype + NULL    + NULL     (업종 기준, 공통 폴백)
5순위: None                       (기존 파이프라인 사용)
```

### 매칭 시나리오 예시

| 입력 | 1순위 | 2순위 | 3순위(신규) | 4순위 | 결과 |
|------|-------|-------|------------|-------|------|
| 통신판매업+신규+법인 | #6 HIT | - | - | - | TEMPLATE(#6) |
| 통신판매업+신규+개인 | MISS | MISS | `btype+개인` 템플릿 있으면 HIT | MISS | 3순위 또는 None |
| 통신판매업+프랜차이즈+법인 | MISS | MISS | `btype+법인` 있으면 HIT | MISS | 3순위 또는 None |
| 미용업+신규+개인 | MISS | MISS | MISS | `미용업` 공통 있으면 HIT | 4순위 또는 None |

## 구현 계획

### Phase 1: 코드 수정 (Effort: S)

**수정 파일**: `app-backend/app/features/roadmaps/application/template_resolver.py`

**변경 1**: `resolve()` 메서드 docstring 업데이트 (L27-33)
- 4단계 → 5단계 우선순위 반영

**변경 2**: 2순위(L59-71)와 기존 3순위(L73-84) 사이에 새 3순위 블록 삽입

```python
# 3. Partial B: business_type + startup_type (startup_method=NULL)
if startup_type:
    stmt = base.where(
        RoadmapTemplate.startup_method.is_(None),
        RoadmapTemplate.startup_type == startup_type,
    )
    template = (await session.execute(stmt)).scalar_one_or_none()
    if template:
        logger.info(
            "Template resolved: partial-stype id=%d btype=%s stype=%s",
            template.id, business_type, startup_type,
        )
        return template
```

### Phase 2: 테스트 추가 (Effort: M)

**수정 파일**: `app-backend/tests/services/test_template_resolver.py`

**변경 1**: `_create_approved_template` 헬퍼에 `startup_type` 파라미터 추가

**변경 2**: 새 테스트 케이스 5개 추가

| 테스트명 | 검증 내용 | 우선순위 관계 |
|---------|----------|-------------|
| `test_resolve_partial_stype_match` | btype+stype 매칭 동작 | 3순위 단독 |
| `test_resolve_exact_over_partial_stype` | 정확 > btype+stype | 1순위 > 3순위 |
| `test_resolve_smethod_over_stype` | btype+smethod > btype+stype | 2순위 > 3순위 |
| `test_resolve_stype_fallback_when_no_smethod` | smethod=None 입력 시 stype 매칭 | 3순위 직접 진입 |
| `test_resolve_common_fallback_still_works` | 공통 폴백 여전히 동작 | 4순위 회귀 |

## 변경하지 않는 범위

| 대상 | 이유 |
|------|------|
| `should_create_auto_draft()` | 현재 additive AND 필터가 목적에 정확히 부합 (exact 조합별 auto-draft 판단) |
| `roadmap_generation_service.py` | 이미 `startup_type`을 `resolve()`에 전달 중 (L213) |
| 프론트엔드/API | 이미 startup_method, startup_type 편집 지원 |
| DB 모델/마이그레이션 | `startup_type` 컬럼 이미 nullable로 존재, 복합 인덱스 완비 |
| ISSUE-1 (역사적 데이터) | 이전 코드 버전 문제, 현재 코드 수정 대상 아님 |

## 리스크 평가

| 리스크 | 영향 | 확률 | 대응 |
|--------|------|------|------|
| 기존 테스트 실패 | 중 | 낮 | 기존 4개 테스트가 startup_type 미사용이라 영향 없음 |
| 의도치 않은 템플릿 매칭 | 높 | 낮 | IS NULL 조건으로 명시적 범용 템플릿만 매칭 (기존 패턴 동일) |
| 성능 저하 | 낮 | 극히 낮 | 쿼리 1개 추가뿐, 복합 인덱스 활용 |

## 검증 방법

```bash
# 1. 단위 테스트 (대상 파일)
cd app-backend && .venv/bin/pytest tests/services/test_template_resolver.py -v

# 2. 전체 회귀 테스트
cd app-backend && .venv/bin/pytest -q
```

## 성공 기준

- [ ] 새 5개 테스트 전체 통과
- [ ] 기존 4개 테스트 회귀 없음
- [ ] 전체 pytest 스위트 통과
