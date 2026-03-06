# PLAN: Google OAuth Integration

StepZero 프로젝트에 구글 소셜 로그인 기능을 통합하여 정식 사용자 인증 체계를 구축합니다.

## Overview
- **Goal**: 구글 계정을 이용한 원클릭 로그인 및 자동 회원가입 구현
- **Strategy**: 프론트엔드(`@react-oauth/google`) 라이브러리와 백엔드(`google-auth-library`) 검증 로직을 결합한 표준 JWT 방식 채택

## Success Criteria
- [ ] 구글 로그인 버튼 클릭 시 OAuth 팝업이 정상적으로 노출됨
- [ ] 구글 인증 성공 후 `id_token`이 백엔드로 정확히 전달됨
- [ ] 백엔드에서 토큰 검증 후 사용자 생성/조회 및 자체 JWT 발급이 완료됨
- [ ] 로그인 후 `AuthProvider` 상태가 업데이트되고 대시보드 데이터가 새로고침됨

## Tech Stack
- **Frontend**: `@react-oauth/google`
- **Backend**: `google-auth-library` (Python/FastAPI)
- **Auth Flow**: Authorization Code Flow (Implicit flow via library for simplified SPA integration)

## Google Cloud Console Setup Guide
1. [Google Cloud Console](https://console.cloud.google.com/) 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. **APIs & Services > OAuth consent screen** 설정 (User Type: External)
   - 앱 이름, 사용자 지원 이메일 등 필수 항목 입력
4. **APIs & Services > Credentials**에서 "OAuth 2.0 Client ID" 생성
   - **Application Type**: Web Application
   - **Name**: StepZero Web Client (자유롭게 입력)
   - **Authorized JavaScript origins**:
     - `http://localhost:3000`
   - **Authorized redirect URIs (중요)**:
     - `http://localhost:3000`
     - `http://localhost:3000/api/auth/callback/google` (백엔드 직접 연동 시 필요할 수 있음)
     > [!IMPORTANT]
     > `@react-oauth/google` 라이브러리의 팝업 방식을 사용할 경우 JavaScript origin 설정만으로도 작동할 수 있으나, 보안 및 확장성을 위해 리디렉션 URI에 메인 도메인(`http://localhost:3000`)을 등록해두는 것을 권장합니다.
5. 발급된 `Client ID`와 `Client Secret`을 복사하여 보관합니다.

## Task Breakdown

### Phase 1: Foundation & Credentials
- [ ] **Task 1.1**: 백엔드 `.env` 파일에 구글 자격 증명 추가 (Agent: `backend-specialist`)
  - INPUT: Client ID, Secret
  - OUTPUT: `GOOGLE_CLIENT_ID` 환경변수 로드 확인
- [ ] **Task 1.2**: 프론트엔드 `.env.local`에 `NEXT_PUBLIC_GOOGLE_CLIENT_ID` 추가 (Agent: `frontend-specialist`)

### Phase 2: Backend Implementation
- [ ] **Task 2.1**: 백엔드 의연성 설치 (`google-auth-library`) (Agent: `backend-specialist`)
- [ ] **Task 2.2**: 구글 토큰 검증 로직 구현 (`app/api/v1/auth.py` 수정) (Agent: `backend-specialist`)
  - INPUT: `id_token`
  - OUTPUT: 구글 프로필 정보 (email, name)
- [ ] **Task 2.3**: 자동 회원가입 및 JWT 발급 로직 연동 (Agent: `backend-specialist`)

### Phase 3: Frontend Implementation
- [ ] **Task 3.1**: 프론트엔드 라이브러리 설치 (`@react-oauth/google`) (Agent: `frontend-specialist`)
- [ ] **Task 3.2**: `AuthProvider` 또는 최상위 `layout.tsx`에 `GoogleOAuthProvider` 적용 (Agent: `frontend-specialist`)
- [ ] **Task 3.3**: `SocialAuthModal.tsx`에 정식 구글 로그인 버튼 구현 및 API 연동 (Agent: `frontend-specialist`)

### Phase X: Verification
- [ ] 구글 로그인 성공 후 `localStorage`에 정식 JWT 저장 확인
- [ ] 로그아웃 후 세션 초기화 확인
- [ ] 신규 유저 로그인 시 DB(mock)에 사용자 정보 생성 여부 확인

## Next Steps
1. 환경 변수 설정 (User)
2. `/create` 명령어로 구현 시작
