# Backend Feature Rules

## Scope
- 이 문서는 `app-backend/app/features/` 하위 전체에 적용된다.

## Architectural Rules
- Feature 코드는 `features/<feature>/{domain,application}`에 둔다.
- HTTP 라우팅은 `app/api/v1/<feature>/`에서만 처리한다.
- API base path는 `/api/v1`만 사용한다.
- 모델은 `app/models`에서 관리하고 feature 내부에 테이블 모델을 중복 정의하지 않는다.
- 데이터 접근은 `app/repositories`를 통해서만 수행한다.

## Boundary Rules
- 다른 feature의 `application` 코드를 직접 import하지 않는다.
- 공용 접근은 `app/core`, `app/repositories`, `app/models`만 사용한다.
- 공용 변경이 필요하면 PR 본문에 이유를 명시한다.

## Required Verification
- 변경 후 `cd app-backend && .venv/bin/pytest -q` 실행.
- 인증/권한/API 변경 시 관련 테스트 케이스를 추가 또는 수정.
- 라우터 추가/수정 시 `app/api/v1/api.py` include_router 반영 여부를 확인한다.
