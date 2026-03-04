# 로드맵 개선 통합 구현 순서 보고서

> 작성일: 2026-03-01
> 목적: REPORT-chatbot-enhancement-analysis.md, REPORT-roadmap-template-management-analysis.md, REPORT-roadmap-template-implementation-plan.md 3개 문서의 전체 작업 항목을 코드베이스와 대조 검증한 후, 의존성 그래프 기반 최적 구현 순서를 제시
> 방법: 백엔드(파이프라인/모델/Ops/RAG) + 프론트엔드(로드맵/챗봇/Ops) + 인프라(마이그레이션/의존성) 총 3개 영역 병렬 코드 분석

---

## 1. 3개 문서 핵심 요약

### 문서 A: AI 코치 챗봇 개선 분석 (REPORT-chatbot-enhancement-analysis.md)

**Part 1 — AI 코치 챗봇 MVP (신규 기능)**
- SSE 스트리밍 엔드포인트 (`POST /roadmaps/{id}/steps/{id}/chat/stream`)
- 3레이어 시스템 프롬프트 (`RoadmapContextBuilder`)
- 대화 이력 DB 테이블 2개 (`RoadmapChatThread`, `RoadmapChatMessage`)
- 할루시네이션 방지 4가지 안전장치
- 프론트엔드: `StepChatPanel`, `useStepChat` hook, SSE 스트리밍 렌더링
- 예상 공수: BE 15.5일 + FE 11일 = **약 5-8주** (QA 포함)

**Part 2 — 링크 오류 수정 (기존 버그)**
- 근본 원인 7가지 발견 (LLM item_id 누락, 파일 미등록, 첫 파일만 매핑 등)
- P0 4건 + P1 3건 = 총 7건
- 예상 공수: P0 4일 + P1 3.5일 = **약 1.5주**

### 문서 B: 템플릿 관리 시스템 분석 (REPORT-roadmap-template-management-analysis.md)

- 현재 로드맵 생성의 비결정성 문제 분석
- 공통(법령/서류) vs 개인화(체크리스트/일수) 분리 전략
- `business_type × startup_method` 조합으로 최대 24개 템플릿
- `startup_type` 프론트/백엔드 정의 불일치 발견 (개인/법인 vs 신규/양수양도/프랜차이즈)
- 3개 신규 테이블 설계 (`RoadmapTemplate`, `RoadmapTemplateStep`, `RoadmapTemplateAction`)
- `TemplateResolver` + 기존 파이프라인 통합 설계
- 관리자 UI 설계 (기존 Ops ActionKit 패턴 재활용)
- 예상 공수: **약 4주** (19일)

### 문서 C: 템플릿 구현 상세 계획 (REPORT-roadmap-template-implementation-plan.md)

문서 B의 분석을 7개 Group으로 구체화:
- Group 1: DB 스키마 & 마이그레이션
- Group 2: 백엔드 템플릿 CRUD 서비스
- Group 3: 파이프라인 통합 (TemplateResolver)
- Group 4: startup_type/startup_method 어휘 수정
- Group 5: 프론트엔드 관리자 UI
- Group 6: 테스트
- Group 7: 문서 업데이트

---

## 2. 코드베이스 검증 — 문서 분석 vs 현실

### 2.1 백엔드 현황 확인

| 문서 주장 | 코드베이스 검증 결과 | 판정 |
|----------|-------------------|:----:|
| Alembic 마이그레이션 8개 존재 | `001_core` ~ `008_feature_merge_all` 확인 | ✅ 일치 |
| `ChatOpenAI` gpt-4o-mini 사용 | `rag_service.py`, `chat_service.py`에서 확인 | ✅ 일치 |
| SSE 스트리밍 구현 없음 | FastAPI `StreamingResponse` 미사용 확인 | ✅ 일치 |
| 대화 이력 DB 모델 없음 | `models/` 디렉토리에 chat 관련 모델 없음 | ✅ 일치 |
| SemanticRouter 2카테고리 | `semantic_router.py`: legal(8앵커) + general(4앵커) | ✅ 일치 |
| LLM Personalizer `_validate_references()` 경고만 | `llm_personalizer.py`: `logger.debug` 출력만, 데이터 수정 없음 | ✅ 일치 |
| `item_file_urls` 첫 파일만 사용 (break문) | `roadmap_generation_service.py` 확인 | ✅ 일치 |
| Ops 라우터에 7개 서브라우터 | home, reports, users, growth_club, actionkit, announcements, audit_logs | ✅ 일치 |
| 감사로그 상수 확장 가능 | `constants.py`에 `AuditAction`, `AuditTargetType` enum 존재 | ✅ 일치 |
| Roadmap 모델에 `template_id` 없음 | `models/roadmap.py` 확인: 필드 없음 | ✅ 일치 |

### 2.2 프론트엔드 현황 확인

| 문서 주장 | 코드베이스 검증 결과 | 판정 |
|----------|-------------------|:----:|
| 글로벌 FAB 챗봇 | `GlobalChatbot.tsx` + `ChatFAB.tsx` + `ChatPanel.tsx` 확인 | ✅ 일치 |
| SSE 스트리밍 렌더링 없음 | `useChatbot.ts`: `POST /rag/chat` → JSON 일괄 응답 | ✅ 일치 |
| 출처 표시 `"법률 RAG"` / `"일반 AI"` 배지만 | `ChatBubble.tsx` 확인 | ✅ 일치 |
| `TimelineStepItem.tsx` ACTIVE 상태 구조 | CHECKLIST → DOCUMENT → LEGAL_BASIS 순서로 렌더링 확인 | ✅ 일치 |
| Ops 6개 카드 | OpsHomeView: reports, users, growth-club, actionkit, announcements, audit-logs | ✅ 일치 |
| OpsActionKitView drag-drop 재정렬 | `@hello-pangea/dnd` 사용 확인 | ✅ 일치 |
| shadcn/ui 컴포넌트 | Button, Card, Dialog, Badge, Progress, Table 등 15+ 컴포넌트 | ✅ 일치 |

### 2.3 기술 스택 버전 확인

| 영역 | 항목 | 현재 버전 |
|------|------|----------|
| BE | Python | 3.11+ |
| BE | FastAPI | >=0.109.0 |
| BE | SQLModel | 0.0.14 |
| BE | LangChain | >=0.1.0, langchain-openai >=0.0.5 |
| BE | ARQ (비동기 큐) | 0.25.0 |
| FE | Next.js | 16.1.6 (App Router) |
| FE | React | 18.x |
| FE | Tailwind CSS | 3.3.0 |
| FE | DnD | @hello-pangea/dnd 18.0.1 |

### 2.4 검증 결론

**3개 문서의 현황 분석은 코드베이스와 100% 일치한다.** 문서 내 제안된 수정/신규 코드 위치, 재활용 가능 컴포넌트, 의존성 관계 모두 정확하다.

---

## 3. 의존성 그래프 분석

### 3.1 작업 간 핵심 의존성

```
[링크 오류 수정] ──────────────────────────────────────────┐
  │                                                        │
  │  링크가 제대로 동작해야:                                  │
  │  - 템플릿 source_url도 유효                             │
  │  - AI 코치 출처 인용 링크도 유효                          │
  │                                                        │
  ▼                                                        │
[startup_type/method 어휘 수정] ─────┐                      │
  │                                  │                      │
  │  매칭 키가 일관되어야               │                      │
  │  템플릿 검색이 정확                  │                      │
  │                                  │                      │
  ▼                                  │                      │
[템플릿 DB 스키마 + 마이그레이션] ─────┤                      │
  │                                  │                      │
  ▼                                  ▼                      │
[템플릿 CRUD 서비스 + API] ──→ [템플릿 관리자 UI]             │
  │                                                        │
  ▼                                                        │
[파이프라인 통합 (TemplateResolver)]                         │
  │                                                        │
  │  템플릿에 고정된 팩트 데이터가 있어야                      │
  │  AI 코치 3레이어 컨텍스트가 더 정확                       │
  │                                                        │
  ▼                                                        ▼
[AI 코치 DB 모델 + ContextBuilder] ◀─────────────────────────
  │
  ▼
[AI 코치 SSE 백엔드] ──→ [AI 코치 프론트엔드]
  │
  ▼
[안전장치 QA + 프롬프트 튜닝]
```

### 3.2 병렬 가능 구간 식별

| 구간 | 병렬 가능 작업 | 조건 |
|------|--------------|------|
| 링크 수정 중 | 마스터 플랜 Phase 1 FE Quick Wins (Endowed Progress 등) | BE 변경 불필요 |
| 템플릿 DB 완료 후 | BE CRUD 서비스 ∥ FE 관리자 UI 스켈레톤 | API 스키마 확정 후 |
| 템플릿 CRUD 완료 후 | 파이프라인 통합 ∥ AI 코치 DB 모델 설계 | 독립적 |
| AI 코치 BE 완료 후 | FE SSE 채팅 UI ∥ 안전장치 프롬프트 튜닝 | SSE 엔드포인트 존재 시 |

---

## 4. 최적 구현 순서 — 6 Phase 권장안

### 전체 타임라인 요약

```
Week  1    2    3    4    5    6    7    8    9   10   11   12
      │    │    │    │    │    │    │    │    │    │    │    │
P-0 ──████████──
      링크 수정 + startup_method 정리

P-1 ──████████████──
      FE Quick Wins (Phase 1 마스터플랜) [병렬]

P-2 ────────████████████──
            템플릿 DB + CRUD + 파이프라인

P-3 ──────────────████████████──
                  템플릿 관리자 UI

P-4 ────────────────────████████████████──
                        AI 코치 BE + FE

P-5 ──────────────────────────────████████──
                                  QA + 통합 테스트
```

---

### Phase 0: 선행 수정 — 링크 오류 + 어휘 정리 (Week 1-2, 10일)

> **목적**: 이후 모든 작업의 기반이 되는 data integrity 확보

#### 0-A. 링크 오류 P0 수정 (4일)

| # | 작업 | 파일 | 공수 |
|---|------|------|:----:|
| 0-A-1 | FE: DOCUMENT/LEGAL_BASIS 일관된 폴백 표시 | `TimelineStepItem.tsx` | 0.5일 |
| 0-A-2 | FE: `metadata_json.actionkit_item_id` 기반 대안 링크 | `TimelineStepItem.tsx` | 1일 |
| 0-A-3 | BE: LLM `actionkit_item_id` 자동 복구 로직 | `llm_personalizer.py` (`_validate_and_repair_references()`) | 2일 |
| 0-A-4 | BE: 다중 파일 매핑 수정 (break 제거) | `roadmap_generation_service.py:319` | 0.5일 |

**검증**: 기존 로드맵 재생성 후 링크 클릭 → 404 발생 0건

#### 0-B. 링크 오류 P1 수정 (3.5일)

| # | 작업 | 파일 | 공수 |
|---|------|------|:----:|
| 0-B-1 | BE: `source_url`을 `item_id` 기반 URL로 통일 | `roadmap_generation_service.py` | 1일 |
| 0-B-2 | DB: 기존 데이터 마이그레이션 (source_url 복구) | Alembic 마이그레이션 스크립트 | 0.5일 |
| 0-B-3 | BE: hybrid 매칭 모드 도입 (부분 폴백) | `llm_personalizer.py` | 2일 |

#### 0-C. `startup_type` / `startup_method` 어휘 수정 (2일, 0-B와 병렬)

| # | 작업 | 파일 | 공수 |
|---|------|------|:----:|
| 0-C-1 | FE: 인테이크 폼에 `startup_method` 질문 추가 | `RoadmapChatIntake.tsx`, `roadmap-constants.ts` | 1일 |
| 0-C-2 | BE: `GenerationPayload`에 `startup_method` 추가 | `roadmap_generation_service.py`, `llm_personalizer.py` | 0.5일 |
| 0-C-3 | BE: Roadmap 모델에 `startup_method` 컬럼 추가 | `models/roadmap.py`, Alembic 마이그레이션 | 0.5일 |

**검증**: `cd app-backend && make test` 통과, `cd app-frontend && npm run lint` 통과

---

### Phase 1: FE Quick Wins — 마스터 플랜 Phase 1 (Week 1-3, Phase 0과 병렬)

> **목적**: BE 변경 없이 UX 가치를 즉시 전달. Phase 0과 동시 진행 가능.

| # | 작업 | 파일 | 공수 |
|---|------|------|:----:|
| 1-1 | Endowed Progress UI ("이미 17% 완료") | `RoadmapExecutionView.tsx`, `RoadmapSidebar.tsx` | 3일 |
| 1-2 | 다음 3-5 액션 집중 표시 | `TimelineStepItem.tsx` | 2일 |
| 1-3 | 준비도 5단계 스코어 (🌱→🚀) | `RoadmapSidebar.tsx`, `DashboardView.tsx` | 5일 |
| 1-4 | 마일스톤 축하 모먼트 (인사이트 카드) | `TimelinePhaseCard.tsx` | 3일 |
| 1-5 | 첫 5분 경험 최적화 | `RoadmapChatIntake.tsx` | 2일 |

**합계**: 15일 (3주), Phase 0과 병렬로 실제 일정 추가 없음

**검증**: `cd app-frontend && npm run build` 성공

---

### Phase 2: 템플릿 관리 시스템 — 백엔드 (Week 3-5, 12일)

> **목적**: 로드맵 품질 일관성 확보 + LLM 비용 60% 절감 기반 구축

#### 2-A. DB 스키마 + 마이그레이션 (2일)

| # | 작업 | 파일 | 공수 |
|---|------|------|:----:|
| 2-A-1 | 3개 모델 생성 | `app/models/roadmap_template.py` (신규) | 1일 |
| 2-A-2 | Roadmap 모델에 `template_id` FK 추가 | `app/models/roadmap.py` | 0.5일 |
| 2-A-3 | Alembic 마이그레이션 `009_roadmap_templates.py` | `alembic/versions/` | 0.5일 |

**핵심 결정사항** (문서 B Section 10.1 반영):
- Phase 1 매칭 키: `business_type`만 (8개 템플릿)
- 자동 DRAFT: 업종 최초 생성 시만
- 버전 관리: 새 버전 레코드 생성 방식
- APPROVED 수정: 새 버전으로만

#### 2-B. 백엔드 CRUD 서비스 + API (5일)

| # | 작업 | 파일 | 공수 |
|---|------|------|:----:|
| 2-B-1 | 감사로그 상수 추가 | `audit_logs/constants.py` | 0.5일 |
| 2-B-2 | 서비스 레이어 (8개 함수) | `features/ops/application/roadmap_templates.py` (신규) | 2일 |
| 2-B-3 | API 스키마 정의 | `api/v1/ops/schemas.py` (확장) | 0.5일 |
| 2-B-4 | API 라우터 (10개 엔드포인트) | `api/v1/ops/roadmap_templates.py` (신규) | 1.5일 |
| 2-B-5 | 라우터 등록 | `api/v1/ops/router.py` (수정) | 0.5일 |

**재활용**: `ops/actionkit.py` 패턴 (CRUD + 감사로그 + 정렬) 그대로 적용

#### 2-C. 파이프라인 통합 (5일)

| # | 작업 | 파일 | 공수 |
|---|------|------|:----:|
| 2-C-1 | `TemplateResolver` 구현 (매칭 로직) | `features/roadmaps/application/template_resolver.py` (신규) | 1.5일 |
| 2-C-2 | `RoadmapGenerationService` 수정 (템플릿 분기 + 자동 DRAFT) | `roadmap_generation_service.py` | 2일 |
| 2-C-3 | `LLMPersonalizer` 템플릿 모드 (경량 프롬프트) | `llm_personalizer.py` | 1일 |
| 2-C-4 | `RoadmapRepository` 수정 (`template_id` 파라미터) | `roadmap_repository.py` | 0.5일 |

**검증**: `cd app-backend && make test` 통과, 템플릿 없는 기존 경로 100% 호환 확인

---

### Phase 3: 템플릿 관리 시스템 — 프론트엔드 (Week 5-7, 10일)

> **목적**: 운영자가 템플릿을 검수/승인/관리할 수 있는 Ops UI

| # | 작업 | 파일 | 공수 |
|---|------|------|:----:|
| 3-1 | 디렉토리 구조 + API 호출 함수 + 타입 | `features/ops/roadmap-templates/` (신규) | 1일 |
| 3-2 | Ops 홈 카드 추가 (7번째) | `features/ops/home/view.tsx` | 0.5일 |
| 3-3 | 라우트 페이지 2개 | `app/(dashboard)/ops/roadmap-templates/` (신규) | 0.5일 |
| 3-4 | 목록 뷰 (통계카드 + 필터 + 테이블) | `roadmap-templates/view.tsx` | 2일 |
| 3-5 | 상세 편집 뷰 (스텝 아코디언 + 액션 CRUD) | `roadmap-templates/template-detail-view.tsx` | 3일 |
| 3-6 | 상태 변경 워크플로우 UI | 상세 뷰 내 포함 | 1일 |
| 3-7 | 로드맵 역생성 + 통계 | `roadmap-templates/view.tsx` | 1일 |
| 3-8 | `npm run types:sync` + ops index 등록 | `features/ops/index.ts` 등 | 0.5일 |
| 3-9 | 테스트 | `roadmap-templates/__tests__/` | 0.5일 |

**재활용**: `OpsActionKitView` 패턴 (탭 + 테이블 + 모달 + DnD 정렬)

**검증**: `cd app-frontend && npm run build` 성공, Ops 콘솔에서 CRUD 동작

---

### Phase 4: AI 코치 챗봇 MVP (Week 7-11, 20일)

> **목적**: Step Zero의 핵심 차별화 기능. ChatGPT 이탈 차단.
> **전제**: 법률 자문(변호사법 + AI 기본법) Week 3에서 착수하여 이 시점까지 완료

#### 4-A. BE 기반 구축 (5일)

| # | 작업 | 파일 | 공수 |
|---|------|------|:----:|
| 4-A-1 | DB 모델 2개 (`RoadmapChatThread`, `RoadmapChatMessage`) | `models/roadmap_chat.py` (신규) | 1일 |
| 4-A-2 | Alembic 마이그레이션 | `alembic/versions/010_roadmap_chat.py` | 0.5일 |
| 4-A-3 | `RoadmapContextBuilder` (3레이어 직렬화) | `features/roadmaps/application/context_builder.py` (신규) | 3일 |
| 4-A-4 | `SemanticRouter` OUT_OF_SCOPE 확장 | `features/rag/application/semantic_router.py` | 0.5일 |

**핵심**: `RoadmapContextBuilder`는 기존 `RoadmapRepository` 메서드 조합으로 구현. 템플릿 시스템이 있으면 LAYER 1 팩트 데이터가 검수 완료된 상태로 제공되어 정확도 향상.

#### 4-B. BE 핵심 (7일)

| # | 작업 | 파일 | 공수 |
|---|------|------|:----:|
| 4-B-1 | `RoadmapChatService` (SSE 스트리밍 + 이력 저장) | `features/roadmaps/application/chat_service.py` (신규) | 4일 |
| 4-B-2 | SSE 라우터 (`/roadmaps/{id}/steps/{id}/chat/stream`) | `api/v1/roadmaps/chat.py` (신규) | 2일 |
| 4-B-3 | 안전장치 시스템 프롬프트 설계 | 프롬프트 텍스트 + 출처 파싱 | 1일 |

**기술 결정**: SSE 클라이언트는 `fetch` + `ReadableStream` (JWT 헤더 전송 필수)

#### 4-C. FE 구현 (8일)

| # | 작업 | 파일 | 공수 |
|---|------|------|:----:|
| 4-C-1 | `useStepChat` hook (SSE + 상태 관리) | `features/roadmap/hooks/useStepChat.ts` (신규) | 3일 |
| 4-C-2 | `StepChatPanel` (슬라이드아웃 패널) | `features/roadmap/components/StepChatPanel.tsx` (신규) | 2일 |
| 4-C-3 | 출처 인용 파싱 + 출처 카드 UI | StepChatPanel 내부 | 1.5일 |
| 4-C-4 | "AI에게 물어보기" 버튼 (TimelineStepItem 통합) | `TimelineStepItem.tsx` 수정 | 0.5일 |
| 4-C-5 | 면책 문구 고정 렌더링 | StepChatPanel 하단 | 0.5일 |
| 4-C-6 | 모바일 풀스크린 대응 | StepChatPanel 반응형 | 0.5일 |

**재활용**: `ChatBubble`, `ChatInput` 컴포넌트 구조 참고 (대부분 재작성이지만 패턴 동일)

---

### Phase 5: 품질 검증 + 안전장치 QA (Week 11-12, 8일)

| # | 작업 | 공수 |
|---|------|:----:|
| 5-1 | 안전장치 QA 시나리오 100건+ 테스트 | 3일 |
| 5-2 | 프롬프트 레드팀 테스트 (경계 케이스) | 2일 |
| 5-3 | 통합 테스트 (템플릿 → 로드맵 생성 → AI 코치 대화) | 2일 |
| 5-4 | 성능 테스트 (SSE 동시 연결, 토큰 예산 검증) | 1일 |

---

## 5. 공수 총괄 및 크리티컬 패스

### 5.1 Phase별 공수

| Phase | 작업 | 공수 | 누적 |
|:-----:|------|:----:|:----:|
| **P0** | 링크 수정 + startup_method | 10일 | 2주 |
| **P1** | FE Quick Wins (P0과 병렬) | 15일 | 2주 (병렬) |
| **P2** | 템플릿 BE (DB + CRUD + 파이프라인) | 12일 | 4.5주 |
| **P3** | 템플릿 FE (관리자 UI) | 10일 | 6.5주 |
| **P4** | AI 코치 (BE + FE) | 20일 | 10.5주 |
| **P5** | QA + 통합 테스트 | 8일 | 12주 |

### 5.2 크리티컬 패스 (직렬 의존성)

```
P0 링크 수정 (2주)
  → P2 템플릿 BE (2.5주)
    → P4-A AI 코치 기반 (1주)
      → P4-B AI 코치 핵심 BE (1.5주)
        → P4-C AI 코치 FE (1.5주)
          → P5 QA (1.5주)

크리티컬 패스 합계: 약 10.5주
```

### 5.3 병렬화 시 총 일정

```
P0 + P1 (병렬) = 3주
P2 + P3 (부분 병렬) = 3주
P4 = 4주
P5 = 1.5주

총 예상: 약 11-12주 (2.5-3개월)
```

---

## 6. 비개발 병행 작업 (일정에 포함 안 됨 — 별도 진행 필수)

| 작업 | 시작 시점 | 소요 기간 | Phase 4 전까지 완료 필수 |
|------|:--------:|:--------:|:--------------------:|
| **법률 자문** (변호사법 109조 + AI 기본법) | Week 3 | 4-6주 | **필수** |
| 안전장치 QA 시나리오 100건+ 작성 | Week 5 | 2주 | **필수** |
| 프롬프트 레드팀 테스트 계획 | Week 7 | 1주 | 권장 |
| 비음식점 업종 ActionKit 시드 데이터 확충 | Week 4~ | 지속적 | 권장 |

---

## 7. 리스크 및 완화 전략

| 리스크 | 영향도 | 완화 전략 |
|--------|:------:|----------|
| 법률 자문 지연 → AI 코치 출시 차단 | ★★★★★ | Week 3에 즉시 착수, P4 이전 완료 |
| LangChain `astream` 버전 호환성 | ★★★☆☆ | 현재 `langchain-openai>=0.0.5` 확인, 필요 시 OpenAI SDK 직접 사용 |
| 템플릿 + AI 코치 마이그레이션 충돌 | ★★☆☆☆ | 009(템플릿) → 010(채팅) 순차 생성, 충돌 없음 |
| FE Quick Wins와 링크 수정 코드 충돌 | ★★☆☆☆ | `TimelineStepItem.tsx`만 공유 — 링크 수정 먼저 머지 후 Quick Wins 진행 |
| 안전장치 QA에서 할루시네이션 발견 | ★★★★☆ | Phase 5에 2주 버퍼 확보, 실패 시 AI 코치 출시 연기 |

---

## 8. 핵심 결론

### 왜 이 순서가 최적인가

1. **링크 수정 선행**: 템플릿의 `source_url`과 AI 코치의 출처 인용 모두 유효한 링크에 의존. 기반 없이 위층을 쌓으면 나중에 전부 재수정 필요.

2. **템플릿이 AI 코치보다 먼저**: 템플릿 시스템이 있으면 AI 코치의 `RoadmapContextBuilder`가 **운영자 검수 완료된 팩트 데이터**를 사용할 수 있어 할루시네이션 위험이 구조적으로 감소.

3. **FE Quick Wins 병렬 진행**: BE 변경 불필요한 UX 개선을 링크 수정과 동시에 진행하여 사용자 가치를 빠르게 전달.

4. **법률 자문 타이밍**: Week 3에 착수하면 4-6주 후인 Week 7-9에 결과 도출 → Phase 4 AI 코치 FE 구현 시작 전 완료 가능.

### 마스터 플랜 대비 조정사항

| 마스터 플랜 | 이 보고서 조정 | 이유 |
|-----------|-------------|------|
| Phase 1 → Phase 2 → Phase 3 순차 | P0(링크) + P1(Quick Wins) 병렬 → P2-3(템플릿) → P4(AI코치) | 링크 수정과 템플릿을 AI 코치 전에 배치하여 data integrity 확보 |
| AI 코치 2-3주 (낙관적) | AI 코치 4주 (보수적) | 문서 A의 실제 평가 ~55-60% 재활용률 반영 |
| 템플릿 미언급 | 템플릿 3주 삽입 | 품질 일관성 + 비용 절감 + AI 코치 정확도 향상의 3중 효과 |
| 총 16주 | **총 12주** (템플릿 포함, Phase 3 마케팅/법령알림 제외) | 핵심 기능에 집중, Phase 3는 별도 사이클 |
