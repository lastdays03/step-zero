# Tasks: 테스트 성능 감사

> Last Updated: 2026-03-06

## Phase 1: P0 — 백엔드 테스트 인프라 (즉시)

- [x] 1-1. `pyproject.toml`에 `addopts = "--ignore=tests/eval"` + 마커 등록 [S]
- [x] 1-2. `conftest.py`에 `pytest_collection_modifyitems` requires_openai 자동 skip [S]
- [x] 1-3. `tests/eval/README.md` 수동 실행 가이드 생성 [S]
- [x] 1-4. Makefile에 `test-eval`, `test-eval-t2`, `test-eval-t3` 타겟 추가 [S]
- [x] 1-5. CLAUDE.md Quick Commands에 eval 테스트 명령 갱신 [S]

## Phase 2: P1 — 테스트 품질 개선 (단기)

- [x] 2-1. Dashboard.test.tsx act() 경고 제거 (`waitFor` 패턴 적용) [S]

## Phase 3: P2 — 중기 인프라 (Backlog)

- [x] 3-1. 프론트엔드 테스트 커버리지 확대 계획 수립 [XL] → `docs/plans/active/frontend-test-coverage/`로 분리
