# Plan: 테스트 성능 감사 — 구현 계획

> Last Updated: 2026-03-06

## Executive Summary

백엔드 테스트 실행 시간이 287초(4분 47초)로 개발 루프에 심각한 병목을 유발하고 있다.
원인의 90%는 RAG 품질 평가 테스트(`tests/eval/`)가 일반 `make test`에 혼입된 것이며,
추가로 `requires_openai` 마커 미작동(10건 항상 FAIL), 프론트엔드 act() 경고 등의 문제가 있다.

본 계획은 보고서(`REPORT-test-performance-audit.md`)의 P0~P2 권장사항을 구현한다.

## Current State

| 지표 | 백엔드 | 프론트엔드 |
|------|--------|------------|
| 실행 시간 | 287초 | 2.8초 |
| Pass / Fail / Skip | 341 / 77 / 1 | 22 / 0 / 0 |
| eval 테스트 | 일반 테스트에 포함 (16건, 291초) | N/A |
| requires_openai | 마커 등록만, 자동 skip 없음 → 10건 FAIL | N/A |
| 마커 등록 | `eval`, `slow`, `full_eval` 미등록 → 경고 56개 | N/A |
| act() 경고 | N/A | DashboardView 10회 반복 |
| Makefile eval 타겟 | 없음 | N/A |

## Proposed Future State

| 지표 | 백엔드 | 프론트엔드 |
|------|--------|------------|
| `make test` 시간 | **~23초** (-92%) | 2.8초 (변동 없음) |
| Pass / Fail / Skip | ~394 / 0* / 10 | 22 / 0 / 0 |
| eval 실행 | `make test-eval`로 수동 분리 | N/A |
| 경고 | 0 | 0 (act() 해결) |

*R2 마이그레이션 브랜치 작업 완료 가정

---

## Phase 1: P0 — 백엔드 테스트 인프라 (즉시)

이미 적용 완료된 항목과 남은 항목으로 구분.

### 1-1. eval 테스트 기본 제외 — DONE
- `pyproject.toml`에 `addopts = "--ignore=tests/eval"` 추가
- 마커 3개 등록 (`eval`, `slow`, `full_eval`)
- **검증**: `make test` 시 eval 미수집 확인 (404 tests, ~23초)

### 1-2. requires_openai 자동 skip — DONE
- `conftest.py`에 `pytest_collection_modifyitems` 추가
- 더미 키(`sk-test*`) 환경에서 `requires_openai` 마커 테스트 자동 skip
- **검증**: 10건 FAIL → 10건 SKIP 전환 확인

### 1-3. eval README 문서화 — DONE
- `tests/eval/README.md` 생성
- 실행 방법, 티어 구조, 비용, 실행 시점, 결과 확인 명시

### 1-4. Makefile eval 타겟 추가 — TODO
- `make test-eval`, `make test-eval-t2`, `make test-eval-t3` 추가
- `.PHONY` 선언 포함
- **수용 기준**: `make test-eval` 실행 시 eval 테스트만 수행됨
- **Effort**: S

### 1-5. CLAUDE.md 테스트 명령어 갱신 — TODO
- Quick Commands > Backend 섹션에 eval 테스트 명령 추가
- `make test`의 설명에 "eval 제외" 명시
- **수용 기준**: CLAUDE.md에 eval 수동 실행 방법 기재
- **Effort**: S

---

## Phase 2: P1 — 테스트 품질 개선 (단기)

### 2-1. Dashboard 테스트 act() 경고 제거 — TODO
- `Dashboard.test.tsx`에서 비동기 state 업데이트를 `waitFor`로 래핑
- `apiClient.get` mock이 resolve된 후의 state 업데이트를 `act()` 범위 안에서 처리
- **수용 기준**: `pnpm test --verbose 2>&1 | grep "act("` 결과 0건
- **Effort**: S
- **파일**: `app-frontend/src/features/dashboard/__tests__/Dashboard.test.tsx`

---

## Phase 3: P2 — 중기 인프라 (Backlog)

### 3-1. 프론트엔드 테스트 커버리지 확대 — BACKLOG
- 현재 3/22 feature만 테스트 존재
- 우선순위: roadmap 컴포넌트 > actionkit > growth-club
- **Effort**: XL (별도 계획 필요)

---

## Risk Assessment

| 리스크 | 확률 | 영향 | 완화 |
|--------|------|------|------|
| eval 제외로 RAG 회귀 미감지 | 중 | 높 | Makefile에 eval 타겟 명시 + 릴리즈 전 체크리스트에 포함 |
| conftest 변경이 기존 테스트에 영향 | 낮 | 중 | `pytest_collection_modifyitems`는 마커 기반 필터링만, 기존 동작 불변 |
| act() 경고 수정이 테스트 동작 변경 | 낮 | 낮 | `waitFor` 패턴은 기존 assertion 보존, 타이밍만 조정 |

## Success Metrics

- `make test` 실행 시간 < 30초
- `make test` 결과에 FAIL 0건 (R2 브랜치 제외)
- pytest 경고 0건 (unknown mark)
- 프론트엔드 act() 경고 0건
