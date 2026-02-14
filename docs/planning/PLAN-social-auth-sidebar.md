# PLAN: 소셜 로그인 및 게스트 경험 고도화 (Auth & Guest Experience)

## 📋 개요
StepZero의 프리미엄 감성을 유지하면서 가입 허들을 낮추기 위해 **소셜 로그인(Google/Kakao)**을 도입하고, **'그로스 클럽'은 오픈, '로드맵 생성'은 회원 전용**으로 분리하는 하이브리드 게스트 경험을 구축합니다.

## 🎯 주요 목표
1. **사이드바 UI 리액티브화**: 비로그인(게스트) 상태와 로그인 상태에 따른 프로필 영역 시각적 차별화.
2. **소셜 로그인 도입**: Google/Kakao OAuth2 연동을 통한 3초 회원가입/로그인 구현.
3. **핵심 기능 보호 (Gating)**: 로드맵 작성 시도 시 세련된 로그인 유도 모달 노출.
4. **Context 유지**: 그로스 클럽 및 대시보드 구조는 로그인 없이도 탐색 가능하게 하여 Social Proof 제공.

---

## 🏗️ 단계별 구현 계획

### Phase 1: 기반 인프라 및 상태 관리 (Backend & Auth State)
- **Backend (FastAPI)**:
  - `authlib` 기반 OAuth2 처리기 구현 (Google, Kakao).
  - JWT 토큰 발급 및 소셜 계정 연동 스키마 확장.
- **Frontend (Next.js)**:
  - `AuthContext` 또는 전역 상태(Zustand 등)를 통한 `user`, `isLoggedIn` 상태 관리.
  - API Client 인터셉터에 토큰 처리 로직 강화.

### Phase 2: 사이드바 게스트 모드 UI (UI/UX)
- **Sidebar 컴포넌트 수정**:
  - 하단 프로필 섹션을 `LoginButton` 세트로 교체.
  - "게스트 모드로 탐색 중"이라는 부드러운 인디케이터 제공.
  - AI 도우미 섹션을 "회원가입하고 AI 법률 비서 받기" 문구로 캐주얼하게 유도.

### Phase 3: 소셜 로그인 모달 (Premium Modal)
- **SocialAuthModal 구현**:
  - Glassmorphism 디자인이 적용된 Shadcn/UI Dialog 사용.
  - Google, Kakao 브랜드 컬러가 적용된 프리미엄 버튼 세트.
  - "왜 로그인해야 하는가?"에 대한 핵심 가치(Value Prop) 3줄 요약 포함.

### Phase 4: 기능별 접근 제어 (Feature Gating)
- **Roadmap Generation**:
  - `CreateRoadmapButton` 클릭 시 `isLoggedIn` 체크.
  - 비로그인 시 로드맵 생성 로직 대신 `SocialAuthModal` 트리거.
- **Growth Club**:
  - 데이터 조회 API는 공개하되, 실제 채팅/댓글 시도 시 로그인 유도.

---

## 🛠️ 검증 계획 (Verification)

### 1. 자동화 테스트
- **Auth Flow**: Mock OAuth 응답을 통한 로그인 성공/실패 시나리오 테스트.
- **Route Guard**: 비로그인 상태에서 보호된 API 호출 시 401 에러 및 리다이렉트 확인.

### 2. 사용자 경험(UX) 체크
- 로드맵 생성 시도 -> 로그인 성공 -> 다시 로드맵 생성 화면으로 자연스럽게 복귀하는지 확인.
- 그로스 클럽 탐색 시 비로그인 상태에서 끊김 없는 UI 확인.

---

## 👥 에이전트 할당
- **Backend Specialist**: OAuth2 연동 및 JWT 보안 레이어 강화.
- **Frontend Specialist**: 사이드바 게스트 UI 및 소셜 로그인 모달 구현.
- **Orchestrator**: 전체 상태 동기화 및 전역 Auth Context 설계.

---

[OK] Plan created: `docs/PLAN-social-auth-sidebar.md`

Next steps:
- 이 플랜을 검토해 주세요.
- 승인하시면 `/create` 명령어로 구현을 시작하거나, 세부 사항을 수정할 수 있습니다.
