# API v1 Rules

## Scope
- 이 문서는 `app-backend/app/api/v1/` 하위 라우팅 코드에 적용된다.

## Routing Rules
- 엔드포인트는 feature 단위 폴더(`auth`, `dashboard`, `roadmaps`...)에 둔다.
- 각 feature는 `router.py`를 진입점으로 사용한다.
- 경로 prefix는 `api.py`에서만 조합한다.

## Contract Rules
- 요청/응답 스키마는 `app/api/v1/schemas.py` 또는 feature 로컬 스키마에 둔다.
- 기존 프론트가 쓰는 응답 필드는 제거/타입 변경 전에 승인 필요.

## Verification
- 라우팅 변경 후 `pytest -q` 필수.
