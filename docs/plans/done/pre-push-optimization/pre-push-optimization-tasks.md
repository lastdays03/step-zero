# Pre-Push 최적화 태스크

> Last Updated: 2026-03-12

## Phase 1: 핵심 개선

- [x] **1.1** `.husky/pre-push` 수정 — pytest 범위를 `tests/services tests/repositories tests/integration`으로 축소
  - 수용 기준: pre-push가 `tests/api` 제외한 subset만 실행
- [x] **1.2** `test_law_api_client.py`에 `_REQUEST_INTERVAL=0` autouse fixture 추가
  - 수용 기준: 해당 테스트 파일의 개별 테스트가 0.05초 이내
- [x] **1.3** 적용 후 실측
  - 수용 기준: pre-push 그린 경로 실측 < 7초, 결과를 보고서에 기록
  - 결과: pre-push `5.61s`, smoke subset `3.30s`, 보고서 반영 완료

## Phase 2: 보조 개선

- [x] **2.1** `-x` fail-fast 옵션 추가 여부 결정 및 적용
  - 수용 기준: 결정 사유 기록, 적용 시 pre-push에 반영
- [x] **2.2** `CLAUDE.md` Quality Gates 섹션 업데이트
  - 수용 기준: 로컬 smoke vs CI 전체 회귀 구분 명시
- [x] **2.3** CI vs 로컬 훅 역할 분리 문서화
  - 수용 기준: 어디에 무엇이 실행되는지 명확히 기술

## Phase 3: 추가 최적화 (선택)

- [ ] **3.1** client fixture `scope="session"` A/B 계측
  - 수용 기준: scope 변경 전후 API 테스트 시간 비교 데이터
- [ ] **3.2** 계측 결과 기반 fixture scope 변경 적용/보류 결정
- [ ] **3.3** SQLite in-memory 전환 검토 (xdist 병렬화 도입 시)
