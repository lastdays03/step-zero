# API v1 Rules

## Scope
- 이 문서는 `app-backend/app/api/v1/` 하위 라우팅 코드에 적용된다.

## Routing Rules
- 엔드포인트는 feature 단위 폴더(`auth`, `dashboard`, `roadmaps`...)에 둔다.
- 각 feature는 `router.py`를 진입점으로 사용한다.
- 경로 prefix는 `api.py`에서만 조합한다.
- 신규 feature 라우터를 추가할 때 `api.py` include 누락이 없는지 확인한다.
- 라우터 계층은 `Depends` + 요청/응답 변환만 담당하고 도메인 규칙은 feature `application`으로 위임한다.

## Contract Rules
- 요청/응답 스키마는 `app/api/v1/schemas.py` 또는 feature 로컬 스키마에 둔다.
- 기존 프론트가 쓰는 응답 필드는 제거/타입 변경 전에 승인 필요.
- `response_model`은 필수로 선언하고, 실제 반환 shape가 스키마와 일치해야 한다.

## Data Access Rules
- 라우터에서 DB 쿼리를 직접 작성하지 않는다.
- DB 접근은 repository를 통해 수행하고, application 계층에서 orchestration 한다.
- 인증/권한은 `app/api/deps.py` 의존성으로만 처리한다.

## Verification
- 라우팅 변경 후 `pytest -q` 필수.
