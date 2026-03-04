# Ops Reports Dashboard - Tasks

> Last Updated: 2026-03-04

---

## Phase A: 백엔드 서비스 재작성

- [ ] **A-1** `OpsReportsService` 클래스 생성 (Effort: M)
  - `service.py` 전면 재작성
  - `AsyncSession` 주입, `get_summary(range_days: int) -> OpsSummary` 비동기 메서드
  - `OpsSummary` TypedDict 확장 (~15 필드)
  - **AC:** 클래스 생성, 타입 정의 완료, import 에러 없음

- [ ] **A-2** 활성 사용자 집계 쿼리 (Effort: S)
  - `_count_active_users(since, until?)`
  - `User.last_login_at >= since AND is_active AND NOT is_suspended`
  - **AC:** 7d/30d 기간 모두 정확한 COUNT 반환

- [ ] **A-3** 신규 가입 집계 쿼리 (Effort: S)
  - `_count_new_signups(since, until?)`
  - `User.created_at >= since`
  - **AC:** 기간 필터 정확, 비활성 사용자도 포함 (가입 이벤트이므로)

- [ ] **A-4** 로드맵 생성 집계 쿼리 (Effort: S)
  - `_count_roadmaps(since, until?)`
  - `Roadmap.created_at >= since AND deleted_at IS NULL`
  - **AC:** soft delete 제외, 기간 필터 정확

- [ ] **A-5** 채팅 세션 집계 쿼리 (Effort: S)
  - `_count_chat_sessions(since, until?)`
  - `RoadmapChatThread.created_at >= since AND is_deleted = False`
  - **AC:** 삭제된 스레드 제외

- [ ] **A-6** 커뮤니티 게시물 집계 쿼리 (Effort: S)
  - `_count_community_posts(since, until?)`
  - `GrowthClubPost.created_at >= since`
  - **AC:** blinded 게시물도 포함 (운영 지표이므로)

- [ ] **A-7** 총계 쿼리 (Effort: S)
  - `total_users`: `User` 전체 COUNT (is_active 필터)
  - `total_teams`: `Team` 전체 COUNT (deleted_at IS NULL)
  - `total_roadmaps`: `Roadmap` 전체 COUNT (deleted_at IS NULL)
  - **AC:** soft delete 제외한 정확한 총계

- [ ] **A-8** 비율 지표 계산 (Effort: M)
  - `dau_mau_ratio`: `active_users_7d / active_users_30d` (30d=0 → 0.0)
  - `signup_to_roadmap_rate`: 기간 내 가입자 중 로드맵 생성 사용자 비율
    - subquery: `Roadmap.created_by IN (SELECT id FROM user WHERE created_at >= cutoff)`
  - **AC:** 0 나누기 방지, 0~1 사이 float 반환

- [ ] **A-9** 전기간 대비 변화율 (delta) 계산 (Effort: M)
  - 현재 기간 값 vs 직전 동일 기간 값
  - `delta = (current - prev) / prev` (prev=0 → None)
  - 대상: active_users, new_signups, roadmaps_generated
  - **AC:** prev=0이면 None, 음수/양수 모두 정확, float 반환
  - **Depends:** A-2, A-3, A-4

- [ ] **A-10** `get_summary()` 통합 및 반환 (Effort: S)
  - 모든 private 메서드 호출 → OpsSummary dict 조립
  - `generated_at`: UTC ISO 포맷
  - `range`: "7d" | "30d"
  - **AC:** 전체 응답 구조 일치, 에러 없이 반환
  - **Depends:** A-2 ~ A-9

---

## Phase B: 백엔드 API 수정

- [ ] **B-1** API 라우트에 `range` 파라미터 + session DI 추가 (Effort: S)
  - `range: str = Query("7d", pattern="^(7d|30d)$")`
  - `session: AsyncSession = Depends(get_session)`
  - `OpsReportsService(session)` 인스턴스화
  - **AC:** `?range=7d`와 `?range=30d` 모두 200 OK, 잘못된 값 422 반환
  - **Depends:** A-10

- [ ] **B-2** `__init__.py` export 업데이트 (Effort: S)
  - `get_summary` → `OpsReportsService`로 변경
  - **AC:** import 에러 없음
  - **Depends:** A-1

---

## Phase C: 프론트엔드 타입/API

- [ ] **C-1** `OpsSummary` 타입 확장 (Effort: S)
  - 4필드 → ~15필드 (백엔드 응답 구조와 1:1)
  - delta 필드는 `number | null`
  - **AC:** 타입 정의가 백엔드 응답과 정확히 매칭
  - **Depends:** A-10 (응답 구조 확정)

- [ ] **C-2** `fetchOpsSummary(range)` 파라미터 추가 (Effort: S)
  - `range` 파라미터를 query param으로 전달
  - **AC:** `fetchOpsSummary("7d")`, `fetchOpsSummary("30d")` 모두 동작
  - **Depends:** B-1

---

## Phase D: 프론트엔드 UI 확장

- [ ] **D-1** `MetricCard` 컴포넌트 추출 (Effort: M)
  - Props: `title: string`, `value: string | number`, `delta?: number | null`, `suffix?: string`, `badge?: { label: string; variant: "good" | "warning" }`
  - delta 포맷: `+12.5%` (녹색) / `-5.2%` (빨간색) / `null` → 미표시
  - 기존 인라인 `<div>` 패턴을 컴포넌트로 추출
  - **AC:** 독립 컴포넌트로 동작, delta 색상 구분 정확

- [ ] **D-2** 기간 필터 탭 UI (Effort: S)
  - 7일 / 30일 토글 버튼
  - 선택 시 `fetchOpsSummary(range)` 재호출
  - **AC:** 탭 전환 시 로딩 표시 → 데이터 갱신

- [ ] **D-3** KPI 카드 그리드 구성 (Effort: M)
  - Row 1 (핵심 지표 + delta): 활성 사용자, 신규 가입, 로드맵 생성, 채팅 세션
  - Row 2 (비율 + 총계): DAU/MAU, 가입→로드맵, 커뮤니티 게시물, 총 사용자
  - `md:grid-cols-4` 그리드
  - 총 사용자 카드에 `총 팀: N` 부가 정보 표시
  - **AC:** 8개 카드가 2행×4열로 렌더링 (모바일: 1열)
  - **Depends:** D-1, C-1, C-2

- [ ] **D-4** 비율 지표 상태 뱃지 (Effort: S)
  - DAU/MAU >= 0.2 → "양호" (녹색), < 0.2 → "주의" (노란색)
  - signup_to_roadmap >= 0.5 → "우수" (녹색), < 0.5 → "보통" (회색)
  - **AC:** 값에 따라 뱃지 색상 정확히 변경
  - **Depends:** D-1

---

## Phase E: 검증

- [ ] **E-1** 백엔드 pytest 전체 통과 (Effort: S)
  - `cd app-backend && .venv/bin/pytest -q`
  - **AC:** 기존 테스트 전부 통과 (260+ passed)
  - **Depends:** B-1

- [ ] **E-2** 프론트엔드 ESLint 통과 (Effort: S)
  - `cd app-frontend && npm run lint`
  - **AC:** 0 errors
  - **Depends:** D-3

- [ ] **E-3** 수동 API 테스트 (Effort: S)
  - `curl` 또는 MCP로 7d/30d 응답 확인
  - 잘못된 range 값에 422 반환 확인
  - **AC:** 실제 데이터가 0이 아닌 값으로 반환 (DB에 데이터 있을 경우)
  - **Depends:** B-1

- [ ] **E-4** 프론트엔드 UI 확인 (Effort: S)
  - `/ops/reports` 페이지 접속
  - 8개 KPI 카드 렌더링 확인
  - 7일/30일 탭 전환 동작 확인
  - delta 색상 표시 확인
  - **Depends:** D-3

---

## Summary

| Phase | 태스크 수 | 총 Effort |
|-------|----------|----------|
| A: 백엔드 서비스 | 10 | L |
| B: 백엔드 API | 2 | S |
| C: 프론트엔드 타입/API | 2 | S |
| D: 프론트엔드 UI | 4 | M |
| E: 검증 | 4 | S |
| **합계** | **22** | |

**Critical Path:** A-1 → A-2~A-9 → A-10 → B-1 → C-1/C-2 → D-1~D-4 → E-1~E-4
