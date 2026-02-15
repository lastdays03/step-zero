# DECISIONS

- Backend API HTTP 계층은 `app/api/v2/<feature>/<function>.py`로 운영한다.
- Backend 비즈니스 계층은 `app/features/<feature>/{domain,application}`에 둔다.
- 운영콘솔 네이밍은 `ops`로 통일한다(`ops-console`, `ops_console` 사용 금지).
- Frontend 피처는 public entry(`index.ts`)를 유지하되, 서버 컴포넌트에서는 hook export를 직접 import하지 않는다.
- 루트(`/`)는 랜딩 페이지 대신 `/dashboard`로 리다이렉트한다.
- 관리자 진입 기본 URL은 `/ops`로 유지한다.
