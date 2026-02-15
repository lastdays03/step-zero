# Dev Status

## 현재 상태
- Backend API 구조를 `app/api/v2/<feature>/<function>.py`로 통일했다.
- Frontend 피처 패키지 경계를 정리했고 `/`는 `/dashboard`로 리다이렉트된다.
- 사이드/모바일 메뉴는 주요 진입점(`/roadmap`, `/actionkit`, `/growth-club`, `/settings`, `/profile`, `/billing`)까지 연결됐다.

## 이번 스프린트 포커스
- 소셜로그인 전용 운영 플로우에 맞춘 `/ops` 접근 정책 구현
- 피처별 실제 기능 구현(현재 placeholder 상태 제거)

## Next 3 Actions
1. `/ops` 권한 가드(프론트+백엔드) 최소 구현
2. `roadmap`/`actionkit` 페이지 placeholder를 실제 데이터 로딩 화면으로 교체
3. 메뉴/라우트 규칙을 e2e 또는 통합 테스트로 1차 검증
