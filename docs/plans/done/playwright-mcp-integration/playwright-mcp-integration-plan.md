# PLAN: Playwright MCP 통합 디버깅 인프라 구축

> Last Updated: 2026-03-12

---

## Executive Summary

Playwright MCP 디버깅 가이드(REPORT)를 기반으로, StepZero 프로젝트에 실질적인 브라우저 디버깅/테스트 인프라를 구축한다. 핵심은 두 가지다.

1. 프론트엔드 프로덕션 컴포넌트에 안정적인 `data-testid`를 추가해 selector를 고정한다.
2. `browser_run_code`에 재사용 가능한 repo-managed snippet source와 사용 규약을 정리해, MCP 기반 디버깅을 반복 가능한 루틴으로 만든다.

---

## Current State Analysis

### 현재 상태
- Playwright MCP가 Claude Code 플러그인으로 설정됨 (사용 가능)
- CLAUDE.md에 "Browser Testing (Playwright MCP)" 섹션 추가 완료
- 디버깅 가이드 보고서 작성 완료 (`docs/plans/reports/REPORT-playwright-mcp-debugging-guide.md`)
- 프로덕션 컴포넌트 기준 `data-testid` 공통 규약 없음 → 텍스트/CSS 셀렉터 의존
- `scripts/playwright/` 디렉터리 없음 → 재사용 snippet 자산 부재
- 인증/로드맵 생성 같은 시나리오의 로컬 prerequisite가 문서화되어 있지 않음

### 문제점
1. **테스트 셀렉터 불안정**: `data-testid` 없이 텍스트/ref 기반 셀렉터 사용 → UI 텍스트 변경 시 깨짐
2. **반복 작업**: 매 디버깅마다 로그인 → 페이지 이동 → 검증을 수동 반복
3. **성능 베이스라인 부재**: Core Web Vitals 목표는 있으나 정기 측정 체계 없음
4. **실행 경로 불명확**: “스크립트 작성” 계획은 있으나 MCP에서 어떻게 재사용할지 정의가 없음
5. **인증 전제 불명확**: pytest fixture 계정과 로컬 dev 계정을 혼동할 위험이 있음

---

## Proposed Future State

1. 핵심 UI 요소에 `data-testid` 속성 추가
2. `scripts/playwright/`에 `browser_run_code`용 snippet source + README 사용 규약 정리
3. 인증/워커/Redis 등 시나리오별 prerequisite를 문서화
4. Core Web Vitals 측정 스니펫과 초기 베이스라인 기록

---

## Implementation Phases

### Phase 0: 실행 모델 및 prerequisite 확정 (Priority: High)

문서만 있고 실행 방법이 없는 상태를 먼저 해소한다.

| # | Task | Effort | Acceptance Criteria |
|---|------|--------|---------------------|
| 0.1 | `scripts/playwright/README.md` 규약 정의 | S | snippet 파일을 MCP에서 어떻게 읽고 `browser_run_code`에 넣는지 문서화 |
| 0.2 | 인증 bootstrap 전략 확정 | S | “로컬 dev 계정 / social mock / public-only” 중 허용 경로 문서화 |
| 0.3 | 시나리오별 prerequisite 매트릭스 정리 | S | dashboard/login/chat/roadmap 생성 각각 필요한 backend/db/redis/worker 명시 |

### Phase 1: data-testid 속성 추가 (Priority: High)

프론트엔드 핵심 컴포넌트에 안정적 테스트 셀렉터 추가.

| # | Task | Effort | Acceptance Criteria |
|---|------|--------|---------------------|
| 1.1 | 로그인 폼 (`LoginForm`) | S | `data-testid="login-email"`, `login-password`, `login-submit` |
| 1.2 | 레이아웃 컨테이너 (`DashboardLayout`, `Header`) | S | `header`, `main-content` |
| 1.3 | 네비게이션 링크 (`Sidebar`, `MobileNav`) | S | `sidebar` container + desktop/mobile 각각에서 고정 nav testid 제공 |
| 1.4 | 로드맵 입력/검증/생성 (`RoadmapChatIntake`) | M | 실제 입력 필드, 검증 버튼, 생성 버튼에 testid 부여 |
| 1.5 | 로드맵 생성 상태 (`RoadmapGenerationPanel`) | S | 폴링 상태/오류/완료 전환을 잡을 수 있는 container testid |
| 1.6 | 채팅 상태 전환 (`ChatWidget`, `ChatFAB`, `ChatPanel`, `ChatInput`) | M | FAB ↔ Panel 전환과 입력 영역 선택이 안정적으로 가능 |

### Phase 2: 디버깅 스크립트 정리 (Priority: Medium)

보고서의 자동화 예시를 `browser_run_code`에 재사용 가능한 snippet source로 정리한다.

| # | Task | Effort | Acceptance Criteria |
|---|------|--------|---------------------|
| 2.1 | `scripts/playwright/smoke-test.js` | M | public + authenticated navigation smoke를 `browser_run_code`에 그대로 주입 가능 |
| 2.2 | `scripts/playwright/api-health.js` | M | localStorage의 token/teamId를 읽어 보호 API 호출 가능 또는 skip 전략 명시 |
| 2.3 | `scripts/playwright/web-vitals.js` | S | LCP/FCP/CLS/TTI/TBT 수집용 snippet source |

### Phase 3: 성능 베이스라인 (Priority: Low)

| # | Task | Effort | Acceptance Criteria |
|---|------|--------|---------------------|
| 3.1 | 주요 페이지별 Web Vitals 초기 측정 | M | 최소 5 페이지 측정, public/auth 시나리오 구분 포함 |
| 3.2 | 성능 회귀 감지 기준 문서화 | S | CLAUDE.md 목표와 실측값 비교 표 |

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| `data-testid` 추가가 번들 크기에 영향 | Low | 현 규모에서는 유지, 과도한 남용만 방지 |
| Playwright MCP 버전/설정 변경 | Medium | snippet source를 MCP 독립 JS 함수 형태로 유지하고 README에 주입 절차 명시 |
| 테스트 데이터(계정) 관리 | High | pytest fixture 계정과 dev DB 계정 분리 명시, auth bootstrap 전략 확정 |
| 비동기 플로우 flaky | Medium | 1차 smoke는 deterministic 경로(login/nav/layout) 우선, roadmap/chat full flow는 prerequisite 명시 후 확장 |

---

## Success Metrics

- [x] login/layout/nav/roadmap/chat 프로덕션 컴포넌트에 `data-testid` 반영 완료
- [x] `scripts/playwright/README.md` + 3개 snippet source 파일 정리 완료
- [ ] 최소 1개 public 시나리오와 1개 authenticated 시나리오를 Playwright MCP로 재현 성공
- [ ] Core Web Vitals 초기 측정 완료

---

## Dependencies

- 프론트엔드 + 백엔드 서버 실행 환경 (localhost:3000 / 8000)
- Docker Compose (DB + Redis) 가동
- Playwright MCP 플러그인 설정 완료 (이미 완료)
- 로드맵 생성 검증 시 worker 실행 (`cd app-backend && make worker`)
- 인증 필요 시나리오용 로컬 dev 계정 또는 허용된 mock/social login 전략

---

## Timeline Estimate

| Phase | Effort | 의존성 |
|-------|--------|--------|
| Phase 0 | S | 없음 |
| Phase 1 | S~M | Phase 0에서 대상/전략 확정 시 효율 상승 |
| Phase 2 | M | Phase 0 완료 필수, Phase 1 완료 시 selector 활용 가능 |
| Phase 3 | S | Phase 2 스크립트 활용 |
