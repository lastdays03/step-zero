# Pre-Push 훅 성능 최적화 계획

> Last Updated: 2026-03-12

## Executive Summary

pre-push 훅이 **~27초** 소요되어 개발 흐름을 방해하고 있었다. 근본 원인은 로컬 훅이 CI와 거의 같은 백엔드 회귀 테스트 451개를 그대로 돌리는 설계였다. pre-push 범위를 smoke subset으로 축소하고 확정 병목을 제거한 결과, pre-push 체감 시간은 **27.16초 → 5.61초**로 단축됐다.

## 현재 상태

- `.husky/pre-push:24` — `uv run pytest -q -m "not slow and not requires_openai"` (451개)
- `.github/workflows/ci.yml:155` — 동일한 pytest 명령 (CI에서 중복 실행)
- `app-backend/pyproject.toml:78` — `--ignore=tests/eval`만 기본 제외
- `law_api_client.py:74` — `_REQUEST_INTERVAL = 0.5` (mock 테스트에도 sleep 적용)

### 실측 시간

| 구간 | 시간 |
|------|------|
| 전체 pre-push (구현 후) | 5.61s |
| backend 전체 회귀 | 24.37s |
| smoke subset (구현 후) | 3.30s |
| 프론트 lint | 5.47s |
| law_api_client 파일 | 26 passed in 0.40s |

## 목표 상태

- pre-push 체감 시간: **7초 이내** (그린 경로)
- CI는 전체 회귀 유지 (안전망 보존)
- 테스트 인프라 안정성 향상 (동시 실행 내성)

## 구현 단계

### Phase 1: 핵심 개선 (1순위 + 2순위)

pre-push 범위 축소와 확정 병목 제거. 구현 완료.

| # | 태스크 | Effort | 의존성 |
|---|--------|--------|--------|
| 1.1 | `.husky/pre-push` 수정: smoke subset 적용 | S | 없음 |
| 1.2 | `test_law_api_client.py`에 `_REQUEST_INTERVAL=0` 패치 | S | 없음 |
| 1.3 | 적용 후 실측 및 결과 기록 | S | 1.1, 1.2 |

### Phase 2: 보조 개선

실패 UX 개선 및 문서 정비. 구현 완료.

| # | 태스크 | Effort | 의존성 |
|---|--------|--------|--------|
| 2.1 | `-x` fail-fast 옵션 추가 여부 결정 및 적용 | S | Phase 1 완료 |
| 2.2 | CLAUDE.md Quality Gates 섹션 업데이트 | S | Phase 1 완료 |
| 2.3 | CI와 로컬 훅의 역할 분리 문서화 | S | Phase 1 완료 |

### Phase 3: 추가 최적화 (계측 전제)

확정 병목이 아닌 후보들. 계측 후 적용 여부 판단.

| # | 태스크 | Effort | 의존성 |
|---|--------|--------|--------|
| 3.1 | client fixture `scope="session"` A/B 계측 | M | Phase 1 완료 |
| 3.2 | 계측 결과에 따라 fixture scope 변경 적용 | S | 3.1 |
| 3.3 | SQLite in-memory 전환 검토 (xdist 도입 시) | M | 별도 판단 |

## 리스크

| 리스크 | 영향 | 완화 |
|--------|------|------|
| smoke subset에서 API 회귀 누락 | CI에서 감지되므로 push → PR 단계에서 발견 | CI가 안전망 역할, PR 머지 전 반드시 통과 |
| fixture scope 변경 시 테스트 격리 깨짐 | 위양성/위음성 발생 가능 | A/B 계측으로 사전 검증 |
| 기존 Makefile의 `make test` 의미 혼동 | 개발자 혼란 | 문서에 로컬 smoke vs CI 전체 회귀 구분 명시 |

## 성공 지표

- pre-push 그린 경로 실측 시간 **< 7초**
- CI 전체 회귀 테스트 범위 유지 (451개 이상)
- `law_api_client` 테스트 개별 시간 **< 0.05초**

## 구현 결과

- Phase 1 완료: `.husky/pre-push` smoke subset 적용, `test_law_api_client.py` sleep 패치 적용
- Phase 2 완료: `-x` fail-fast 적용, `CLAUDE.md`/`README.md`/`docs/operations/project-operation-rules.md` 문서화 완료
- 성공 지표 달성:
  - pre-push: **5.61초**
  - CI 전체 회귀 유지: **451 passed, 10 deselected**
  - `law_api_client`: setup을 제외한 durations가 **< 0.005초**
