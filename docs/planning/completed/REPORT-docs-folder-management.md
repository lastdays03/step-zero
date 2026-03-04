# docs/ + dev/ 문서 구조 분석 및 관리 방안 보고서

> 작성일: 2026-03-04
> 대상: `/docs/` (86개 파일, 9개 폴더, ~18,900줄) + `/dev/` (76개 파일, 18개 프로젝트, ~21,400줄)

---

## 1. 현황 총괄

프로젝트 루트에 **문서 관리 시스템이 2개** 병존하고 있다.

```
step-zero/
├── docs/                    # 86 files, ~18,900 lines — 기획/설계/운영 문서 (수동 관리)
│   ├── architecture/        # 5 files  — 아키텍처 설계
│   ├── brainstorm/          # 10 files — 초기 기획 브레인스토밍
│   ├── context/             # 6 files  — 경량 컨텍스트 메모리 (세션 운영)
│   ├── dev-guide/           # 4 files  — 개발자 가이드/체크리스트
│   ├── feedback/            # 2 files  — 외부 피드백
│   ├── guides/              # 1 file   — 기능 사용 가이드
│   ├── operations/          # 8 files  — 팀 운영규칙
│   ├── planning/            # 4 files  — 진행 중 계획 (수동 작성)
│   │   └── completed/       # 31 files — 완료 계획 아카이브
│   └── research/            # 15 files — 리서치/분석 보고서
│       └── roadmap-improvement/
│
└── dev/                     # 76 files, ~21,400 lines — /dev-docs 스킬 관리 구현 문서
    ├── active/              # 2 프로젝트 (6 files, ~1,700 lines)
    │   ├── ops-reports-dashboard/     # plan + tasks + context
    │   └── r2-storage-migration/      # plan + tasks + context
    └── done/                # 16 프로젝트 (70 files, ~19,700 lines)
```

**합산**: 162개 파일, ~40,300줄 — 프로젝트 규모 대비 상당한 문서량.

---

## 2. `dev/` 디렉토리 상세 분석

### 2.1 스킬 기반 관리 시스템

`dev/`는 두 개의 **커스텀 슬래시 커맨드**가 관리하는 구조화된 시스템이다:

| 스킬 | 파일 | 역할 |
|------|------|------|
| `/dev-docs` | `.claude/commands/dev-docs.md` | `dev/active/{name}/`에 3파일 세트(plan, tasks, context) 생성 |
| `/dev-docs-update` | `.claude/commands/dev-docs-update.md` | 컨텍스트 압축 전 active 문서 갱신 + 완료 태스크 `done/`으로 아카이브 |

**설계된 라이프사이클**:

```
/dev-docs "주제"               /dev-docs-update              완료 시
    │                              │                           │
    ▼                              ▼                           ▼
dev/active/{name}/          active 문서 갱신              dev/done/{name}/
├── {name}-plan.md          ├── context.md 상태 업데이트    (전체 폴더 이동)
├── {name}-tasks.md         ├── tasks.md 체크리스트 갱신
└── {name}-context.md       └── 완료 태스크 아카이브
```

### 2.2 3파일 세트 구조

| 파일 | 내용 | 크기 범위 |
|------|------|-----------|
| `{name}-plan.md` | Executive Summary, Current State, 기술 설계, API 스펙, 구현 단계 | 200~400줄 |
| `{name}-tasks.md` | `[x]`/`[ ]` 체크리스트, 세부 단계별 완료 추적, 우선순위 | 100~300줄 |
| `{name}-context.md` | 수정 파일 맵, 기술 결정, 디버깅 이력, 다음 스텝 | 150~500줄 |

일부 프로젝트는 추가 산출물 보유:
- 테스트 가이드 (`manual-test-guide.md`, `template-system-test-guide.md`)
- 감사 보고서 (`implementation-audit-report.md`)
- 리서치 (`research-*.md`, `chatbot-unification-research.md`)
- QA 시나리오 (`qa-safety-scenarios.md`)

### 2.3 프로젝트별 규모

| 프로젝트 | 파일 | 줄수 | 상태 |
|----------|------|------|------|
| **active/ops-reports-dashboard** | 3 | 521 | 🟡 진행 중 |
| **active/r2-storage-migration** | 3 | 1,170 | 🟡 진행 중 |
| done/rag-evaluation | 8 | 3,546 | ✅ 완료 |
| done/phase4-ai-coach-chatbot | 6 | 2,350 | ✅ 완료 |
| done/stepzero-ai-chat-rebuild | 5 | 1,734 | ✅ 완료 |
| done/phase2-template-system | 4 | 1,581 | ✅ 완료 |
| done/rag-integration | 4 | 1,408 | ✅ 완료 |
| done/law-data-collection | 3 | 1,316 | ✅ 완료 |
| done/roadmap-quality | 4 | 1,103 | ✅ 완료 |
| done/phase1-fe-quick-wins | 4 | 1,101 | ✅ 완료 |
| done/multi-roadmap | 3 | 1,025 | ✅ 완료 |
| done/rag-upgrade | 4 | 848 | ✅ 완료 |
| done/unified-chatbot-integration | 4 | 754 | ✅ 완료 |
| done/phase3-template-frontend | 3 | 646 | ✅ 완료 |
| done/phase0-roadmap-fix | 3 | 455 | ✅ 완료 |
| done/global-floating-chatbot | 3 | 433 | ✅ 완료 |
| done/template-auth-fixes | 3 | 407 | ✅ 완료 |
| done/roadmap-session-fix | 3 | 376 | ✅ 완료 |
| done/roadmap-ui-redesign | 3 | 336 | ✅ 완료 |
| done/template-matching-fix | 3 | 257 | ✅ 완료 |

**done/ 합계**: 16개 프로젝트, 70개 파일, ~19,700줄

### 2.4 `dev/` 시스템 평가

**강점**:
- `/dev-docs` 스킬로 일관된 3파일 구조 자동 생성
- `/dev-docs-update`로 컨텍스트 압축 전 상태 보존 + 완료 아카이브 자동화
- `active/` → `done/` 라이프사이클이 명확
- 각 프로젝트가 자체 완결적 (plan + tasks + context)
- 태스크 체크리스트로 진행률 추적 가능

**약점**:
- `done/`이 무한 축적 (현재 16개, 19,700줄) — 정리 기준 없음
- `docs/planning/`과의 역할 경계 불명확
- 추가 산출물(리서치, 감사보고서 등)의 위치 기준 없음 — `dev/done/` 내부에 산재

---

## 3. 핵심 문제: `docs/planning/` ↔ `dev/` 이원화

### 3.1 동일 프로젝트 중복 존재

현재 **2개 프로젝트가 양쪽에 동시 존재**:

| 프로젝트 | `docs/planning/` | `dev/active/` | 내용 비교 |
|----------|-------------------|---------------|-----------|
| ops-reports-dashboard | `PLAN-ops-reports-dashboard.md` (48줄, 개요) | 3파일 세트 (521줄, 상세 구현) | `dev/`가 10배 상세 |
| R2 마이그레이션 | `cloudflare-r2-migration-plan.md` (380줄) | 3파일 세트 (1,170줄, 상세 구현) | `dev/`가 태스크 추적 포함 |

### 3.2 완료 프로젝트도 양쪽에 존재

`docs/planning/completed/`의 31개 파일과 `dev/done/`의 16개 프로젝트가 주제적으로 겹침:

| `docs/planning/completed/` | `dev/done/` | 관계 |
|----------------------------|-------------|------|
| `PLAN-roadmap-ui-states.md` | `roadmap-ui-redesign/` | 동일 주제 |
| `PLAN-rag-hybrid-rollout.md` | `rag-upgrade/` | 동일 주제 |
| `PLAN-roadmap-execution-screen.md` | `roadmap-quality/` | 관련 주제 |
| `PLAN-google-auth.md` | `template-auth-fixes/` | 관련 주제 |
| (기타 다수) | | |

### 3.3 두 시스템의 차이점

| 비교 항목 | `docs/planning/` | `dev/` (/dev-docs 스킬) |
|-----------|-------------------|-------------------------|
| **생성 방식** | 수동 작성 | `/dev-docs` 스킬 자동 생성 |
| **파일 구조** | 단일 PLAN-*.md | 3파일 세트 (plan + tasks + context) |
| **상세도** | 개요~중간 | 상세 (파일 맵, API 스펙, 체크리스트) |
| **진행 추적** | 없음 | `[x]`/`[ ]` 체크리스트 |
| **컨텍스트 보존** | 없음 | `/dev-docs-update`로 세션 간 상태 보존 |
| **아카이브** | `completed/` 하위폴더 | `done/` 하위폴더 |
| **네이밍** | `PLAN-<topic>.md` 권장 (불일치 있음) | `<topic>/` 디렉토리 (일관됨) |

### 3.4 문제 요약

1. **신뢰 원천 불명확**: 같은 프로젝트의 계획을 어디서 찾아야 하는지 모호
2. **중복 유지보수**: 양쪽 다 갱신하거나, 한쪽이 방치됨
3. **탐색 비용 증가**: 문서를 찾을 때 두 곳 모두 확인해야 함
4. **`dev/done/` 비대화**: 정리 기준 없이 계속 축적

---

## 4. `docs/` 폴더별 상세 분석

### 4.1 `context/` — 핵심 운영 (상태: 양호)

| 파일 | 상태 | 비고 |
|------|------|------|
| `README.md` | ✅ | 운영 가이드 |
| `dev-status.md` | ✅ | 42줄 (50줄 가이드 이내) |
| `handoff.md` | ✅ | 32줄 (40줄 가이드 이내) |
| `decisions.md` | ✅ | 확정 결정 기록 |
| `ops-rules.md` | ✅ | 세션 운영 규칙 |
| `context-memory-validation-log.md` | ⚠️ | Phase 1 검증 완료 — 아카이브 후보 |

**판정**: 변경 불필요. `context-memory-validation-log.md`만 아카이브 검토.

### 4.2 `planning/` — 핵심 운영 (상태: 역할 재정의 필요)

**활성 파일**:
| 파일 | 문제 |
|------|------|
| `PLAN-ops-reports-dashboard.md` | `dev/active/`에 더 상세한 버전 존재 → 중복 |
| `cloudflare-r2-migration-plan.md` | `PLAN-` 접두사 누락 + `dev/active/`에 중복 |
| `REPORT-ops-monitoring-strategy.md` | REPORT 유형 — planning에 적합한지 검토 |

**completed/ (31개)**: `PLAN-` 접두사 누락 3건, `GUIDE-` 유형 혼재 1건, 버전 파일 중복 2쌍.

### 4.3 `architecture/` — 정적 참조 (상태: 현행화 필요)

5개 파일 모두 `2026-02-26` 이후 미갱신. Phase 0~4 구현 후 실제 코드와 괴리 가능성.
- `StepZero_DB_Schema.md` — Alembic 013까지 진행, 스키마 변경 반영 필요
- `StepZero_Tech_Lead_Foundation.md` ↔ `planning/completed/PLAN-tech-lead-foundation.md` 중복

### 4.4 `operations/` — 팀 운영규칙 (상태: 정리 필요)

| 파일 | 상태 |
|------|------|
| `linear-github-integration-test.md` | 🔴 **삭제 대상** — 5줄 더미 파일 |
| `StepZero_프로젝트_운영규칙_v20260214.md` | ⚠️ `context/ops-rules.md`와 역할 중복 |
| `Feature_개발_패키지_경계.md` | ⚠️ `dev-guide/`로 이동 후보 |
| `ops-audit-logs-guide.md` | ⚠️ `dev-guide/`로 이동 후보 |
| `StepZero_소셜로그인_관리자진입_컨셉_v20260215.md` | ⚠️ `architecture/`로 이동 후보 |

### 4.5 `research/` — 리서치 (상태: 아카이브 대상)

`roadmap-improvement/` 14개 파일(7,200줄) — Phase 0~4 모두 구현 완료. 역할 종료.

### 4.6 `brainstorm/` + `feedback/` — 초기 자료 (상태: 아카이브 대상)

12개 파일 모두 2026-02-26 이후 미갱신. 파일명 한글+공백 혼재, `채팅.md`는 2줄 메모.

### 4.7 `guides/` vs `dev-guide/` — 역할 중복

| 폴더 | 파일 수 | 성격 |
|------|---------|------|
| `guides/` | 1 | 기능 사용 가이드 (`phase4-ai-coach-feature-guide.md`, 47KB) |
| `dev-guide/` | 4 | 개발 프로세스 가이드 (체크리스트, 온보딩, 예외 기록) |

두 폴더 모두 "개발자용 가이드" 범주. 분리 근거 약함.

---

## 5. 핵심 문제 종합

### 5.1 구조적 문제 (3개)

| # | 문제 | 영향도 | 근거 |
|---|------|--------|------|
| **S1** | `docs/planning/` ↔ `dev/` 이원화 | 🔴 높음 | 동일 프로젝트 2곳 존재, 신뢰 원천 불명확 |
| **S2** | `guides/` ↔ `dev-guide/` 역할 중복 | 🟡 중간 | 가이드 문서 위치 모호 |
| **S3** | `operations/` 내 이질적 문서 혼재 | 🟡 중간 | 운영규칙 + 기술가이드 + 아키텍처 컨셉 혼재 |

### 5.2 위생 문제 (4개)

| # | 문제 | 파일 수 | 근거 |
|---|------|---------|------|
| **H1** | 아카이브 미처리 (docs/) | ~27개 | brainstorm 10 + feedback 2 + research 14 + validation-log 1 |
| **H2** | `dev/done/` 비대화 | 70개 (19,700줄) | 정리 기준 없이 16개 프로젝트 축적 |
| **H3** | 파일명 불일치 | ~10개 | PLAN- 누락, 한글+공백, 버전 표기 혼재 |
| **H4** | 더미/미니멀 파일 | 2개 | `linear-github-integration-test.md`, `채팅.md` |

---

## 6. 개선안: `docs/planning/` ↔ `dev/` 통합 전략

### 6.1 선택지 비교

| 방안 | 설명 | 장점 | 단점 |
|------|------|------|------|
| **A. `dev/` 단일화** | `docs/planning/` 폐지, `/dev-docs` 스킬만 사용 | 단일 원천, 스킬 자동화 활용 | 가벼운 기획 메모도 3파일 세트 필요, REPORT 유형 위치 없음 |
| **B. `docs/planning/` 단일화** | `dev/` 폐지, 수동 PLAN 문서만 사용 | 전통적 구조, 폴더 단순 | `/dev-docs` 스킬 무용화, 태스크 추적·컨텍스트 보존 손실 |
| **C. 역할 분리 (권장)** | 두 시스템 유지하되 역할을 명확히 구분 | 각 시스템의 강점 활용, 기존 스킬 유지 | 규칙 준수 필요 |

### 6.2 권장안: C. 역할 분리

```
┌─────────────────────────────────────────────────────────────────────┐
│                      문서 역할 분리 모델                              │
├────────────────────────┬────────────────────────────────────────────┤
│  docs/planning/        │  dev/ (/dev-docs 스킬)                     │
│  ────────────────────  │  ──────────────────────────────────────── │
│  "무엇을 왜 하는가"      │  "어떻게 구현하고 추적하는가"                 │
│                        │                                            │
│  • 프로젝트 기획 배경    │  • 상세 구현 계획 (plan.md)                 │
│  • 범위/비범위 정의      │  • 태스크 체크리스트 (tasks.md)              │
│  • 비즈니스 목표         │  • 파일 맵/기술 컨텍스트 (context.md)       │
│  • API 설계 개요         │  • 디버깅 이력/감사 보고서                   │
│  • 완료 기준 (DoD)       │  • 세션 간 컨텍스트 보존 (/dev-docs-update) │
│  • 보고서 (REPORT-*)    │                                            │
│                        │                                            │
│  작성 시점: 착수 전      │  작성 시점: 구현 시작 시 (/dev-docs 실행)    │
│  작성 주체: 사람 주도    │  작성 주체: /dev-docs 스킬 주도              │
│  라이프사이클:           │  라이프사이클:                               │
│   planning/ → completed/│   active/ → done/ (/dev-docs-update 실행)  │
└────────────────────────┴────────────────────────────────────────────┘
```

**핵심 규칙**:

1. **`docs/planning/`의 역할 = 기획 문서 (What/Why)**
   - 프로젝트 착수 전 작성하는 기획 개요
   - 범위, 비범위, 비즈니스 목표, 완료 기준 정의
   - `REPORT-*.md` 보고서류도 여기 보관
   - 구현 상세, 태스크 추적은 포함하지 않음

2. **`dev/`의 역할 = 구현 문서 (How)**
   - `/dev-docs` 스킬로 생성하는 상세 구현 계획
   - 태스크 체크리스트, 파일 맵, 기술 결정 추적
   - `/dev-docs-update`로 세션 간 컨텍스트 보존
   - 완료 시 자동 아카이브 (`active/` → `done/`)

3. **중복 금지 규칙**
   - 같은 프로젝트에 대해 양쪽에 동일 내용 작성 금지
   - `docs/planning/PLAN-*.md` → 기획 개요만 유지 (구현 상세 X)
   - `dev/active/*/plan.md` → 구현 상세만 유지 (기획 배경은 PLAN 참조)

4. **상호 참조 규칙**
   - `dev/active/{name}/plan.md` 상단에 `> 기획: docs/planning/PLAN-{topic}.md` 참조 링크
   - `docs/planning/PLAN-*.md`에 `> 구현 추적: dev/active/{name}/` 참조 링크

### 6.3 프로젝트 시작 시 문서 작성 워크플로우

```
1. 기획 단계
   └─ docs/planning/PLAN-{topic}.md 작성 (기획 개요, 범위, DoD)

2. 구현 착수
   └─ /dev-docs "{topic}" 실행 → dev/active/{topic}/ 자동 생성
      └─ plan.md 상단에 PLAN 문서 참조 링크 추가

3. 구현 중 (세션 전환 시)
   └─ /dev-docs-update 실행 → context/tasks 갱신

4. 구현 완료
   └─ /dev-docs-update 실행 → dev/done/으로 이동
   └─ docs/planning/PLAN-*.md → docs/planning/completed/로 이동
```

### 6.4 현재 중복 해소 방안

| 프로젝트 | 현재 상태 | 권장 액션 |
|----------|-----------|-----------|
| ops-reports-dashboard | `docs/planning/` (48줄 개요) + `dev/active/` (521줄 상세) | 이미 올바른 분리. PLAN에 `→ dev/active/ 참조` 링크만 추가 |
| R2 마이그레이션 | `docs/planning/` (380줄 상세) + `dev/active/` (1,170줄 상세) | PLAN 파일을 기획 개요로 축소하고 `PLAN-` 접두사 추가. 구현 상세는 `dev/active/`에만 유지 |

### 6.5 `dev/done/` 관리 전략

**현재 문제**: 16개 프로젝트(70개 파일, 19,700줄)가 정리 기준 없이 축적 중.

**권장안: git 이력 신뢰 + 주기적 정리**

```
dev/
├── active/          # 현재 진행 중 (변경 없음)
└── done/            # 완료 프로젝트 (정리 기준 적용)
```

**정리 규칙** (`/dev-docs-update` 스킬 또는 수동):
- `dev/done/`에 **20개 초과** 시 오래된 프로젝트부터 삭제
- 삭제 전 git에 커밋되어 있으므로 `git log --all -- dev/done/{name}/`으로 복구 가능
- 또는 `/dev-docs-update` 스킬에 아카이브 정리 로직 추가 검토

**`/dev-docs-update` 스킬 개선 제안**:
```
### 7. Clean Up Old Archives (선택적 추가)
- `dev/done/` 프로젝트가 20개 초과 시:
  - 가장 오래된 프로젝트부터 삭제 대상 목록 제시
  - 사용자 확인 후 삭제 실행
  - git 커밋되어 있으므로 복구 가능함을 안내
```

---

## 7. `docs/` 폴더별 개선안

### 7.1 `context/` — 변경 없음

유일한 액션: `context-memory-validation-log.md`를 `planning/completed/`로 이동.

### 7.2 `planning/` — README 갱신

`planning/README.md`에 `dev/`와의 역할 구분 규칙 추가:

```markdown
## docs/planning/ vs dev/ 역할 구분

- `docs/planning/PLAN-*.md` = 기획 문서 (What/Why) — 착수 전 작성
- `dev/active/` = 구현 문서 (How) — /dev-docs 스킬로 생성
- 구현 상세·태스크 추적은 `dev/`에만 작성
- PLAN 문서에 `→ 구현 추적: dev/active/{name}/` 참조 링크 포함
```

### 7.3 `architecture/` — 현행화 검증

5개 파일 모두 Phase 0~4 구현 후 미갱신. `Last Verified` 헤더 추가 + 분기별 검증.

### 7.4 `operations/` — 위치 교정

| 파일 | 액션 |
|------|------|
| `linear-github-integration-test.md` | 🔴 삭제 |
| `Feature_개발_패키지_경계.md` | → `dev-guide/` 이동 |
| `ops-audit-logs-guide.md` | → `dev-guide/` 이동 |
| `StepZero_소셜로그인_관리자진입_컨셉_v20260215.md` | → `architecture/` 이동 |

### 7.5 `guides/` → `dev-guide/` 병합

`phase4-ai-coach-feature-guide.md`를 `dev-guide/`로 이동, `guides/` 폴더 삭제.

### 7.6 `brainstorm/` + `feedback/` → `archive/` 이동

`docs/archive/brainstorm/`, `docs/archive/feedback/`으로 이동.

---

## 8. 전체 실행 계획

### Phase A: 즉시 실행 — 위생 정리 (리스크 없음)

| # | 액션 | 대상 |
|---|------|------|
| A1 | 더미 파일 삭제 | `docs/operations/linear-github-integration-test.md` |
| A2 | 검증 로그 이동 | `docs/context/context-memory-validation-log.md` → `docs/planning/completed/` |
| A3 | 파일명 수정 | `cloudflare-r2-migration-plan.md` → `PLAN-cloudflare-r2-migration.md` |
| A4 | 미니멀 파일 정리 | `docs/brainstorm/채팅.md` (2줄) 삭제 |

### Phase B: 역할 경계 확립 (핵심 — 검토 후 실행)

| # | 액션 | 상세 |
|---|------|------|
| B1 | **`docs/planning/` ↔ `dev/` 역할 규칙 수립** | `planning/README.md`에 역할 구분 규칙 추가 (§6.2 내용) |
| B2 | **중복 문서 참조 링크 추가** | 활성 PLAN 파일 ↔ `dev/active/` 간 상호 참조 링크 |
| B3 | **R2 PLAN 문서 정리** | `cloudflare-r2-migration-plan.md`를 기획 개요로 축소 (구현 상세는 `dev/active/`에만) |
| B4 | **`guides/` → `dev-guide/` 병합** | `phase4-ai-coach-feature-guide.md` 이동, `guides/` 삭제 |
| B5 | **문서 위치 교정** | operations/ 내 이질 문서 → 적절한 폴더로 이동 (§7.4) |
| B6 | **`docs/README.md` 생성** | 전체 인덱스 + 폴더 역할 + `dev/`와의 관계 (§9 초안) |

### Phase C: 아카이브 정리

| # | 액션 | 파일 수 |
|---|------|---------|
| C1 | `docs/archive/` 생성 | — |
| C2 | `brainstorm/` → `archive/brainstorm/` | 9개 (A4 삭제 후) |
| C3 | `feedback/` → `archive/feedback/` | 2개 |
| C4 | `research/roadmap-improvement/` 아카이브 마킹 | 14개 |
| C5 | `planning/completed/` 버전 중복 제거 | ~4개 감소 |

### Phase D: 장기 관리 규칙

| # | 액션 | 상세 |
|---|------|------|
| D1 | **네이밍 규칙 확정** | PLAN-*.md, REPORT-*.md, 영문+케밥케이스, 파일명 버전 접미사 지양 |
| D2 | **아키텍처 현행화 주기** | 분기별 `architecture/` 검증, `Last Verified` 헤더 |
| D3 | **`dev/done/` 정리 기준** | 20개 초과 시 오래된 것부터 삭제 (git 이력 복구 가능) |
| D4 | **새 프로젝트 워크플로우** | §6.3의 4단계 워크플로우 준수 |
| D5 | **`/dev-docs-update` 스킬 개선 검토** | `dev/done/` 정리 로직 추가, `docs/planning/` 아카이브 연동 |

---

## 9. `docs/README.md` 초안

```markdown
# docs/ 디렉토리 가이드

## 폴더 역할

| 폴더 | 역할 | 갱신 빈도 |
|------|------|-----------|
| `context/` | 세션 운영 (상태/결정/핸드오프/규칙) | 매 세션 |
| `architecture/` | 시스템 아키텍처 설계 | 분기별 검증 |
| `operations/` | 팀 협업 프로세스 규칙 | 규칙 변경 시 |
| `dev-guide/` | 개발자 가이드/체크리스트/기능 가이드 | 필요 시 |
| `planning/` | 기획 문서 — 프로젝트의 What/Why | 프로젝트 착수/완료 시 |
| `planning/completed/` | 완료 기획 아카이브 | 기획 완료 시 이동 |
| `research/` | 리서치/분석 보고서 | 조사 시 |
| `archive/` | 역할 완료 문서 보관 | 정리 시 |

## docs/planning/ vs dev/ 역할 구분

프로젝트 문서는 두 곳에 분리 관리된다:

| | `docs/planning/` | `dev/` (`/dev-docs` 스킬) |
|--|-------------------|---------------------------|
| 내용 | 기획 (What/Why) | 구현 (How) |
| 작성 시점 | 프로젝트 착수 전 | `/dev-docs` 스킬 실행 시 |
| 형식 | 단일 `PLAN-*.md` | 3파일 세트 (plan + tasks + context) |
| 진행 추적 | 없음 | 체크리스트 (`/dev-docs-update`로 갱신) |
| 완료 시 | `completed/`로 이동 | `done/`으로 이동 |
| 중복 금지 | 구현 상세 작성 X | 기획 배경은 PLAN 참조 링크로 대체 |

## 네이밍 규칙

- 계획: `PLAN-<topic>.md`
- 보고서: `REPORT-<topic>.md`
- 가이드: `<topic>-guide.md` 또는 자유 형식
- 영문 + 케밥케이스 권장
- 파일명 버전 접미사(`_v2`) 지양 — git 이력 활용

## 참조

- 세션 시작 복구: `context/README.md`
- 계획 문서 관리: `planning/README.md`
- 구현 계획 생성: `/dev-docs` 스킬
- 컨텍스트 보존: `/dev-docs-update` 스킬
```

---

## 10. 최종 목표 구조

```
docs/                           # 기획/설계/운영 — "프로젝트를 이해하기 위한 문서"
├── README.md                   # [신규] 전체 인덱스 + dev/ 관계 설명
├── context/                    # [유지] 세션 운영
├── architecture/               # [유지] 아키텍처 설계 (현행화 후)
├── operations/                 # [정리] 팀 협업 규칙만 유지
├── dev-guide/                  # [확장] 개발 가이드 + guides/ 병합
├── planning/                   # [유지] 기획 문서 (What/Why)
│   ├── README.md               # [갱신] dev/와의 역할 구분 규칙 추가
│   └── completed/              # [유지] 완료 기획 아카이브
├── research/                   # [유지] 리서치
└── archive/                    # [신규] 역할 완료 문서
    ├── brainstorm/
    └── feedback/

dev/                            # 구현 계획 — "/dev-docs 스킬이 관리하는 실행 문서"
├── active/                     # [유지] 진행 중 (plan + tasks + context)
└── done/                       # [유지] 완료 (20개 초과 시 정리)
```

---

## 11. 결론

현재 문서 관리의 **가장 큰 문제는 `docs/planning/`과 `dev/`(`/dev-docs` 스킬)의 역할 미분리**다. 두 시스템 모두 가치가 있으나, 경계가 없어 동일 프로젝트가 양쪽에 중복 존재하고 신뢰 원천이 모호하다.

**핵심 처방**:
1. **역할 분리 규칙** — `planning/` = 기획(What/Why), `dev/` = 구현(How)
2. **상호 참조 링크** — 양쪽 문서 간 참조 링크로 연결
3. **아카이브 정리** — 역할 완료 문서 27개+ 분리
4. **폴더 병합** — `guides/` → `dev-guide/`
5. **인덱스 생성** — `docs/README.md`로 전체 안내

| 효과 | 현재 | 개선 후 |
|------|------|---------|
| `docs/` 활성 파일 | 86개 | ~50개 |
| 역할 중복 | 3쌍 (planning↔dev, guides↔dev-guide, operations 내부) | 0 |
| 신뢰 원천 | 모호 | 기획=planning, 구현=dev |
| `dev/done/` | 무한 축적 | 20개 기준 정리 |

Phase A(위생 정리)는 리스크 없이 즉시 실행 가능하고, Phase B(역할 경계)가 가장 중요한 구조적 개선이다.
