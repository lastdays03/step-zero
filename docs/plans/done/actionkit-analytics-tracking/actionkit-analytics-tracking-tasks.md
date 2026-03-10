# TASKS: ActionKit 통계 추적 기능

**Last Updated:** 2026-03-10

---

## Phase 1: 이벤트 수집 인프라 (BE)

- [x] **1.1** ActionKitEvent 모델 생성 `[S]`
- [x] **1.2** 모델 등록 `[S]`
- [x] **1.3** Alembic 마이그레이션 생성 + 적용 `[S]`
- [x] **1.4** 트래킹 API 엔드포인트 `[M]`
- [x] **1.5** 라우터 등록 `[S]`
- [x] **1.6** files.py download/view 추적 삽입 `[M]`
- [x] **1.7** 마이그레이션 양쪽 DB 적용 확인 `[S]` (dind 적용 완료, Docker DB는 배포 시)

---

## Phase 2: 통계 집계 서비스 (BE)

- [x] **2.1** ActionKitStatsService 구현 `[L]`
- [x] **2.2** 응답 스키마 정의 `[M]`
- [x] **2.3** Stats API 엔드포인트 `[S]`
- [x] **2.4** 인사이트 자동 생성 `[M]`
- [x] **2.5** 이벤트 정리 cron job `[S]`

---

## Phase 3: 프론트엔드 연동

- [x] **3.1** API 함수 추가 `[S]`
- [x] **3.2** 사용자 뷰 트래킹 삽입 `[M]`
- [x] **3.3** 법령 뷰 트래킹 삽입 `[S]`
- [x] **3.4** stats-dashboard.tsx 전면 교체 `[L]`
- [x] **3.5** view.tsx allItems 연동 `[M]`
- [x] **3.6** 빈 데이터 + delta=null 처리 `[S]`

---

## Phase 4: 테스트 + 검증

- [x] **4.1** 트래킹 API 테스트 `[M]` — 6 tests passed
- [x] **4.2** 집계 서비스 테스트 `[L]` — 7 tests passed
- [x] **4.3** Quality Gate 통과 `[S]` — 436 passed, pnpm lint 0 errors
- [x] **4.4** 마이그레이션 최종 검증 `[S]` — alembic check clean
- [ ] **4.5** 브라우저 통합 테스트 `[M]` — 보류 (데이터 수집 후 실행 예정)

---

## Summary

| Phase | 태스크 수 | 상태 |
|-------|----------|------|
| Phase 1: 이벤트 수집 | 7 | 완료 |
| Phase 2: 집계 서비스 | 5 | 완료 |
| Phase 3: FE 연동 | 6 | 완료 |
| Phase 4: 테스트/검증 | 5 | 4/5 완료 (4.5 보류) |
| **합계** | **23** | **22/23 완료 → PR #30 머지** |
