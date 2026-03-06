# Ops Reports Dashboard - Tasks

> Last Updated: 2026-03-04

---

## Phase A: 백엔드 서비스 재작성

- [x] **A-1** `OpsReportsService` 클래스 생성 (Effort: M)
- [x] **A-2** 활성 사용자 집계 쿼리 (Effort: S)
- [x] **A-3** 신규 가입 집계 쿼리 (Effort: S)
- [x] **A-4** 로드맵 생성 집계 쿼리 (Effort: S)
- [x] **A-5** 채팅 세션 집계 쿼리 (Effort: S)
- [x] **A-6** 커뮤니티 게시물 집계 쿼리 (Effort: S)
- [x] **A-7** 총계 쿼리 (Effort: S)
- [x] **A-8** 비율 지표 계산 (Effort: M)
- [x] **A-9** 전기간 대비 변화율 (delta) 계산 (Effort: M)
- [x] **A-10** `get_summary()` 통합 및 반환 (Effort: S)

## Phase B: 백엔드 API 수정

- [x] **B-1** API 라우트에 `range` 파라미터 + session DI 추가 (Effort: S)
- [x] **B-2** `__init__.py` export 업데이트 (Effort: S)

## Phase C: 프론트엔드 타입/API

- [x] **C-1** `OpsSummary` 타입 확장 (Effort: S)
- [x] **C-2** `fetchOpsSummary(range)` 파라미터 추가 (Effort: S)

## Phase D: 프론트엔드 UI 확장

- [x] **D-1** `MetricCard` 컴포넌트 추출 (Effort: M)
- [x] **D-2** 기간 필터 탭 UI (Effort: S)
- [x] **D-3** KPI 카드 그리드 구성 (Effort: M)
- [ ] **D-4** 비율 지표 상태 뱃지 (Effort: S) — 간소화 구현 (badge prop으로 텍스트만 표시, 색상 분기 미구현)

## Phase E: 검증

- [x] **E-1** 백엔드 pytest 전체 통과 — 384 passed
- [x] **E-2** 프론트엔드 ESLint 통과 — 0 errors
- [ ] **E-3** 수동 API 테스트 — Docker 환경 필요
- [ ] **E-4** 프론트엔드 UI 확인 — Docker 환경 필요

---

## Result

- PR #19 생성 → develop 머지 완료
- 브랜치 `feature/0-ops-reports-dashboard` 삭제됨
- 커밋: `96976e9`
