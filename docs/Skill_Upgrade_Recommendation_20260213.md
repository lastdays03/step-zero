# StepZero 스킬 업그레이드 제안서 (2026-02-13)

## 1) 목적

StepZero(Next.js 14 + FastAPI + RAG + 문서/기획 중심 워크플로우)에 맞춰,

- 공식 지원(신뢰도 최상) 스킬 우선 세트
- SkillsMP 커뮤니티 스킬(확장성) 추천 세트

를 함께 정리하고, 설치 우선순위를 제안한다.

## 2) 탐색 기준

- 프로젝트 적합성: 현재 코드베이스(Next.js/FastAPI/테스트/문서화)와 직접 연관
- 신뢰도: 공식 curated 여부, 저장소 활동/스타 등 공개 지표
- 즉시성: 설치 후 바로 생산성 향상 가능한지
- 리스크: 스킬 설명/링크 무결성, 특정 환경 종속성

## 3) 공식 스킬 요약 (OpenAI curated)

공식 curated 목록은 `skill-installer` 스크립트로 2026-02-13 확인했다.

### 3.1 추천 코어 7

| 우선순위 | 스킬 | 분류 | 적용 효과 |
| --- | --- | --- | --- |
| P1 | `openai-docs` | LLM/RAG | 모델/API 선택, 파라미터 결정 정확도 향상 |
| P1 | `playwright` | 테스트 | 핵심 사용자 플로우 E2E 자동화 |
| P1 | `gh-fix-ci` | DevEx/CI | CI 실패 원인 분석 및 수정 루틴 표준화 |
| P1 | `gh-address-comments` | 코드리뷰 | PR 코멘트 반영 속도 개선 |
| P1 | `security-best-practices` | 보안 | 인증/비밀키/입력검증 기본 보안 점검 |
| P1 | `security-threat-model` | 보안 설계 | 기능 확장 전 위협 모델링 체계화 |
| P2 | `notion-meeting-intelligence` | 문서화 | 회의록 -> 실행 항목 전환 자동화 |

### 3.2 차순위(상황별) 7

| 우선순위 | 스킬 | 분류 | 적용 시점 |
| --- | --- | --- | --- |
| P2 | `notion-spec-to-implementation` | 기획->개발 | PRD에서 구현 태스크 추출이 잦을 때 |
| P2 | `notion-research-documentation` | 리서치 | 조사/레퍼런스 문서화가 많을 때 |
| P2 | `sentry` | 운영/관측성 | Sentry 스택이 이미 도입된 경우에만 |
| P2 | `doc` | 문서 처리 | 장문 문서 편집/정리 빈도가 높을 때 |
| P3 | `pdf` | 문서 처리 | 정부 양식/PDF 가공 자동화가 필요할 때 |
| P3 | `spreadsheet` | 데이터 작업 | KPI/운영 수치 시트 자동 처리 시 |
| P3 | `screenshot` | QA/디자인 | UI 증적 캡처 워크플로우 필요 시 |

## 4) SkillsMP 상세 탐색 결과

### 4.1 탐색 메모

- SkillsMP는 커뮤니티 스킬 마켓이며, 스킬 포맷은 `SKILL.md` 기반이다.
- 설치/운영 전제와 안전성 문구(공개 저장소 기반, 설치 전 코드 검토 권장)가 명시되어 있다.
- 일부 스킬 페이지는 메타데이터/설명 품질 편차가 있고, 일부는 링크/인덱스 상태가 고르지 않다.

### 4.2 추천 스킬 20 (우선순위 + 분류)

아래 20개는 StepZero 프로젝트 기준으로 활용 가능성이 높은 항목이다.

| 우선순위 | 분류 | 스킬 | 핵심 내용 요약 | 비고 |
| --- | --- | --- | --- | --- |
| P1 | Backend Architecture | `api-design-principles` | API 설계 원칙 정리 및 일관성 있는 인터페이스 설계 지원 | wshobson/agents |
| P1 | Backend Architecture | `architecture-patterns` | 서비스 아키텍처 패턴 선택/적용 가이드 | wshobson/agents |
| P1 | Testing (Python) | `python-testing-patterns` | pytest/fixture/mocking/TDD 기반 테스트 전략 | wshobson/agents |
| P1 | Frontend (Next.js) | `nextjs-anti-patterns` | Next.js App Router 안티패턴 탐지/수정 | wsimmonds/claude-nextjs-skills |
| P1 | E2E/Browser | `playwright-mcp-dev` | Playwright MCP 기반 브라우저 자동화 개발 흐름 | microsoft/playwright |
| P1 | Testing (Python) | `pytest` | FastAPI/SQLAlchemy/async 포함 Python 테스트 실무 패턴 | manutej/luxor-claude-marketplace |
| P2 | Backend Architecture | `microservices-patterns` | 마이크로서비스 설계/분리 패턴 | wshobson/agents |
| P2 | Distributed Systems | `saga-orchestration` | 분산 트랜잭션/오케스트레이션 패턴 | wshobson/agents |
| P2 | Backend Architecture | `cqrs-implementation` | CQRS 구현 패턴 적용 가이드 | wshobson/agents |
| P2 | Backend Architecture | `projection-patterns` | Read 모델/프로젝션 패턴 구성 | wshobson/agents |
| P2 | CI/CD | `gitlab-ci-patterns` | 멀티스테이지 파이프라인/캐시/러너 최적화 | wshobson/agents |
| P2 | Python Runtime | `async-python-patterns` | asyncio 기반 비동기 설계 패턴 | wshobson/agents |
| P2 | Python Tooling | `python-packaging` | 패키징/배포 구조 표준화 | wshobson/agents |
| P2 | Frontend Design System | `tailwind-design-system` | Tailwind 기반 디자인 시스템 구성 | wshobson/agents |
| P2 | Frontend State | `react-state-management` | React 상태관리 설계 패턴 | wshobson/agents |
| P2 | Backend Testing | `temporal-python-testing` | Temporal + Python 테스트 전략 | wshobson/agents |
| P3 | Observability | `observability-monitoring` | Prometheus/Grafana/알림 패턴 | manutej/luxor-claude-marketplace |
| P3 | API Infra | `api-gateway-patterns` | 게이트웨이 라우팅/레이트리밋/인증 패턴 | manutej/luxor-claude-marketplace |
| P3 | Frontend (Next.js) | `nextjs-development` | Next.js 14+ 전체 개발 가이드(범용) | CROW-B3/.claude |
| P3 | Infra/Automation | `cloudflare-browser-rendering` | Workers 기반 headless 브라우저/스크린샷/크롤링 | jezweb/claude-skills |

## 5) 중복 제거 후 최종 설치 목록

중복 스킬은 다음 원칙으로 정리했다.

- 동일 기능군에서는 `공식 curated`를 우선 채택
- 커뮤니티 스킬 간 중복은 상위 우선순위(P1/P2)와 범용성을 기준으로 1개만 채택
- 현재 저장소(Next.js + FastAPI + GitHub 중심 운영)에 맞지 않는 플랫폼 특화 스킬은 제외

### 5.1 최종 설치 스킬 (11개, sentry 제외)

| 우선순위 | 분류 | 스킬 | 선정 이유 |
| --- | --- | --- | --- |
| P1 | LLM/RAG | `openai-docs` | RAG/LLM 구현 정확도 향상 (공식) |
| P1 | E2E 테스트 | `playwright` | 브라우저 자동화 표준 (공식) |
| P1 | CI 안정화 | `gh-fix-ci` | GitHub CI 실패 복구 효율 (공식) |
| P1 | 코드리뷰 처리 | `gh-address-comments` | PR 반영 리드타임 단축 (공식) |
| P1 | 보안 점검 | `security-best-practices` | 기본 보안 베이스라인 (공식) |
| P1 | 보안 설계 | `security-threat-model` | 기능 확장 전 위협 모델링 (공식) |
| P2 | 문서 자동화 | `notion-meeting-intelligence` | 회의록 -> 액션 전환 (공식) |
| P1 | API 설계 | `api-design-principles` | FastAPI 인터페이스 일관성 강화 |
| P1 | 아키텍처 | `architecture-patterns` | 백엔드 구조 결정 가이드 |
| P1 | Python 테스트 | `python-testing-patterns` | pytest 전략 전반 커버 |
| P1 | Next.js 품질 | `nextjs-anti-patterns` | App Router 안티패턴 예방 |

### 5.2 중복/비우선 제외 스킬

| 제외 스킬 | 남긴 스킬 | 제외 사유 |
| --- | --- | --- |
| `playwright-mcp-dev` | `playwright` | 기능군 중복, 공식 스킬 우선 |
| `pytest` | `python-testing-patterns` | Python 테스트 영역 중복(범용성 낮음) |
| `nextjs-development` | `nextjs-anti-patterns` | Next.js 가이드 중복(안티패턴 특화 우선) |
| `observability-monitoring` | - | 관측성 스택 도입 전 단계이므로 보류 |
| `gitlab-ci-patterns` | `gh-fix-ci` | 현재 저장소 운영축이 GitHub 중심 |
| `microservices-patterns` | `architecture-patterns` | 아키텍처 패턴 상위 개념에 포함 |
| `saga-orchestration` | `architecture-patterns` | 분산 트랜잭션은 현 단계 과도한 특화 |
| `cqrs-implementation` | `architecture-patterns` | CQRS는 특정 아키텍처 선택 이후 도입 항목 |
| `projection-patterns` | `architecture-patterns` | CQRS/이벤트소싱 선택 전엔 우선순위 낮음 |
| `temporal-python-testing` | `python-testing-patterns` | Temporal 도입 전에는 범용 테스트가 우선 |
| `api-gateway-patterns` | `api-design-principles` | 게이트웨이 특화보다 API 기본 설계가 선행 |
| `cloudflare-browser-rendering` | `playwright` | 브라우저 자동화 목적 중복, 인프라 종속성 큼 |

### 5.3 설치 순서

1. 기반(공식 7): `openai-docs`, `playwright`, `gh-fix-ci`, `gh-address-comments`, `security-best-practices`, `security-threat-model`, `notion-meeting-intelligence`
2. 확장(커뮤니티 4): `api-design-principles`, `architecture-patterns`, `python-testing-patterns`, `nextjs-anti-patterns`
3. 2주 운영 후 재평가: 제외군 중 필요 항목만 선택 재도입

### 5.4 최종 선정 스킬의 MCP 의존도 매트릭스

| 스킬 | MCP 의존도 | 필요/권장 MCP | 메모 |
| --- | --- | --- | --- |
| `playwright` | 높음 (핵심 자동화) | `playwright-mcp` | MCP 없이도 테스트 코드는 작성 가능하나 브라우저 조작 자동화 이점이 크게 감소 |
| `gh-fix-ci` | 높음 (핵심 자동화) | `github-mcp-server` | Actions/PR/체크 상태 조회-수정 루프 자동화 |
| `gh-address-comments` | 높음 (핵심 자동화) | `github-mcp-server` | 리뷰 코멘트 수집/반영/응답 자동화 |
| `notion-meeting-intelligence` | 높음 (핵심 자동화) | `notion-mcp` | MCP 없으면 회의록 초안까지만 가능, Notion 반영은 수동 |
| `openai-docs` | 중간 (품질 향상) | `context7` 또는 `openai-docs-mcp` | OpenAI 작업 비중이 높으면 전용 MCP 추가 권장 |
| `nextjs-anti-patterns` | 중간 (품질 향상) | `context7` | 최신 Next.js 권장사항 교차 확인에 유리 |
| `api-design-principles` | 중간 (품질 향상) | `context7` | API 설계 레퍼런스 보강 |
| `python-testing-patterns` | 중간 (품질 향상) | `context7` | pytest 패턴/관행 교차 확인 |
| `security-best-practices` | 낮음 (로컬 중심) | `filesystem` | 코드/설정 점검 중심으로 동작 |
| `security-threat-model` | 낮음 (로컬 중심) | `filesystem` | 설계 문서/코드 경계 분석 중심 |
| `architecture-patterns` | 낮음 (로컬 중심) | `filesystem` | 현재 코드 구조 기반 의사결정 가능 |

### 5.5 최종 선정 스킬 상세 설명 (11개)

#### 1) `openai-docs` (공식)
- 언제 쓰나: 모델 선택, 파라미터 결정, 응답 포맷/툴콜/에이전트 구성처럼 OpenAI 문서 정확도가 중요한 작업.
- 기대 효과: 추측 기반 구현을 줄이고, 문서 기준으로 빠르게 의사결정 가능.
- 이 프로젝트 적용 포인트: RAG 품질 튜닝, API 옵션 정합성 점검.
- 주의점: `context7`과 함께 쓰면 문서 출처가 섞일 수 있어, 최종 스펙은 공식 문서 기준으로 확정.

#### 2) `playwright` (공식)
- 언제 쓰나: 사용자 핵심 플로우(로그인, 문서 업로드, 검색, 결과 확인) 회귀 테스트 자동화 시.
- 기대 효과: UI 변경 시 치명 회귀를 조기 발견.
- 이 프로젝트 적용 포인트: Next.js 프론트와 백엔드 연동 플로우 E2E 검증.
- 주의점: 테스트 데이터/시드 전략을 먼저 정하지 않으면 flaky 테스트가 증가.

#### 3) `gh-fix-ci` (공식)
- 언제 쓰나: GitHub Actions 실패 원인 분석과 재현/수정이 반복될 때.
- 기대 효과: CI 실패 복구 리드타임 단축, 원인 분류 표준화.
- 이 프로젝트 적용 포인트: 프론트엔드/백엔드 분리 파이프라인의 실패 지점 빠른 수습.
- 주의점: 임시 우회성 수정이 누적되지 않도록 재발 방지 액션(테스트/룰)까지 함께 반영.

#### 4) `gh-address-comments` (공식)
- 언제 쓰나: PR 리뷰 코멘트 반영이 느려 병목이 생길 때.
- 기대 효과: 코멘트 추적/반영/응답 사이클 일관화.
- 이 프로젝트 적용 포인트: 아키텍처/보안/테스트 피드백 반영 속도 향상.
- 주의점: 코멘트 자동 반영 시 의도 왜곡이 없는지 마지막 수동 검토 필요.

#### 5) `security-best-practices` (공식)
- 언제 쓰나: 인증/인가, 입력 검증, 비밀키 관리, 로그 민감정보 처리 점검 시.
- 기대 효과: 기본 보안 결함 예방, 릴리스 전 보안 체크리스트 강화.
- 이 프로젝트 적용 포인트: FastAPI 입력 검증, 환경변수/키 관리, 파일 업로드 검증.
- 주의점: 체크리스트 통과만으로 충분하지 않으므로 실제 위협 시나리오 점검과 함께 사용.

#### 6) `security-threat-model` (공식)
- 언제 쓰나: 새 기능(파일 처리, 외부 연동, 권한 모델) 추가 전 설계 단계.
- 기대 효과: 공격면/신뢰경계/완화책을 사전에 구조화.
- 이 프로젝트 적용 포인트: 문서 업로드-RAG 인덱싱-응답 경로의 위협 모델링.
- 주의점: 문서화만 하고 끝내지 말고, 실제 태스크(테스트/코드 변경)로 연결해야 효과가 큼.

#### 7) `notion-meeting-intelligence` (공식)
- 언제 쓰나: 회의가 잦고 의사결정이 작업 항목으로 잘 안 떨어질 때.
- 기대 효과: 회의 내용 -> 실행 가능한 액션/담당자/기한으로 변환.
- 이 프로젝트 적용 포인트: 기획/개발/QA 회의의 후속 작업 누락 방지.
- 주의점: Notion 권한 및 페이지 구조(템플릿)를 먼저 표준화해야 자동화 품질이 안정적.

#### 8) `api-design-principles` (커뮤니티)
- 언제 쓰나: 엔드포인트 네이밍/응답 포맷/에러 규약이 흔들릴 때.
- 기대 효과: API 인터페이스 일관성 향상, 프론트-백엔드 협업 비용 감소.
- 이 프로젝트 적용 포인트: FastAPI 라우트 규칙, 오류 응답 스키마 표준화.
- 주의점: 기존 API와의 하위호환 정책(versioning/deprecation)을 함께 정의해야 함.

#### 9) `architecture-patterns` (커뮤니티)
- 언제 쓰나: 모놀리식 유지 vs 분리, 계층 구조, 경계 설정 같은 상위 설계 결정 시.
- 기대 효과: 패턴 선택의 근거 명확화, 기술 부채 누적 완화.
- 이 프로젝트 적용 포인트: Next.js + FastAPI + RAG 모듈 경계와 책임 분리.
- 주의점: 과도한 패턴 도입은 복잡도만 늘릴 수 있어 현재 규모에 맞는 최소 설계 우선.

#### 10) `python-testing-patterns` (커뮤니티)
- 언제 쓰나: 테스트 커버리지와 신뢰도를 동시에 개선하려고 할 때.
- 기대 효과: fixture/mocking/계층별 테스트 전략 정돈.
- 이 프로젝트 적용 포인트: FastAPI 서비스/리포지토리 계층 테스트 표준화.
- 주의점: 통합 테스트 없이 단위 테스트만 늘리면 실제 회귀 탐지력이 떨어질 수 있음.

#### 11) `nextjs-anti-patterns` (커뮤니티)
- 언제 쓰나: App Router 구조에서 성능/가독성/데이터 패칭 문제가 반복될 때.
- 기대 효과: 흔한 안티패턴 조기 제거, 렌더링/캐싱 전략 개선.
- 이 프로젝트 적용 포인트: 서버 컴포넌트 경계, 클라이언트 컴포넌트 남용 방지, fetch/cache 정책 점검.
- 주의점: 프레임워크 버전 업데이트에 따라 권장 패턴이 바뀔 수 있으므로 주기적 재검토 필요.

## 6) 운영 가드레일

- 커뮤니티 스킬은 설치 전 `SKILL.md`, `scripts/`, 외부 호출 여부를 검토
- 프로젝트 로컬 스킬(`.codex/skills` 또는 `~/.codex/skills`)로 격리 적용
- 동일 도메인 스킬 중복 설치 시 우선순위 규칙을 문서화
- 2주 단위로 "실행 빈도/효율/오탐" 점검 후 제거 또는 승격

## 7) 출처

### 공식
- OpenAI skills repository: https://github.com/openai/skills
- Curated list check script (local): `/Users/bagjongman/.codex/skills/.system/skill-installer/scripts/list-skills.py`

### SkillsMP
- SkillsMP 홈: https://skillsmp.com/
- SkillsMP API 문서: https://skillsmp.com/docs/api
- API design principles: https://skillsmp.com/skills/wshobson-agents-plugins-backend-development-skills-api-design-principles-skill-md
- Architecture patterns: https://skillsmp.com/skills/wshobson-agents-plugins-backend-development-skills-architecture-patterns-skill-md
- Python testing patterns: https://skillsmp.com/skills/wshobson-agents-plugins-python-development-skills-python-testing-patterns-skill-md
- Next.js anti-patterns: https://skillsmp.com/skills/wsimmonds-claude-nextjs-skills-nextjs-anti-patterns-skill-md
- Playwright MCP dev: https://skillsmp.com/skills/microsoft-playwright-claude-skills-playwright-mcp-dev-skill-md
- Pytest (luxor): https://skillsmp.com/skills/manutej-luxor-claude-marketplace-plugins-luxor-testing-essentials-skills-pytest-skill-md
- Microservices patterns: https://skillsmp.com/skills/wshobson-agents-plugins-backend-development-skills-microservices-patterns-skill-md
- Saga orchestration: https://skillsmp.com/skills/wshobson-agents-plugins-backend-development-skills-saga-orchestration-skill-md
- CQRS implementation: https://skillsmp.com/skills/wshobson-agents-plugins-backend-development-skills-cqrs-implementation-skill-md
- Projection patterns: https://skillsmp.com/skills/wshobson-agents-plugins-backend-development-skills-projection-patterns-skill-md
- GitLab CI patterns: https://skillsmp.com/zh/skills/wshobson-agents-plugins-cicd-automation-skills-gitlab-ci-patterns-skill-md
- Async Python patterns: https://skillsmp.com/de/skills/wshobson-agents-plugins-python-development-skills-async-python-patterns-skill-md
- Python packaging: https://skillsmp.com/skills/wshobson-agents-plugins-python-development-skills-python-packaging-skill-md
- Tailwind design system: https://skillsmp.com/skills/wshobson-agents-plugins-frontend-mobile-development-skills-tailwind-design-system-skill-md
- React state management: https://skillsmp.com/zh/skills/wshobson-agents-plugins-frontend-mobile-development-skills-react-state-management-skill-md
- Temporal Python testing: https://skillsmp.com/ko/skills/wshobson-agents-plugins-backend-development-skills-temporal-python-testing-skill-md
- Observability monitoring: https://skillsmp.com/skills/manutej-luxor-claude-marketplace-plugins-luxor-devops-suite-skills-observability-monitoring-skill-md
- API gateway patterns: https://skillsmp.com/zh/skills/manutej-luxor-claude-marketplace-plugins-luxor-devops-suite-skills-api-gateway-patterns-skill-md
- Next.js development: https://skillsmp.com/skills/crow-b3-claude-skills-nextjs-development-skill-md
- Cloudflare browser rendering: https://skillsmp.com/skills/jezweb-claude-skills-skills-cloudflare-browser-rendering-skill-md
