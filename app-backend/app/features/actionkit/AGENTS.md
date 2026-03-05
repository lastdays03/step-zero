# actionkit Feature Rules

## Scope
- 이 문서는 \'app-backend/app/features/actionkit/\' 하위에 적용된다.

## Allowed Changes
- \'features/actionkit/domain\'와 \'features/actionkit/application\' 내부 구현
- \'app/api/v1/actionkit/\' 라우팅/스키마 매핑

## Do Not
- 다른 feature 폴더의 코드 수정(긴급 버그 제외)
- 공용 모듈 대규모 리팩터링
- 인증/권한 로직 우회 구현

## Implementation Checklist
- 입력 검증, 예외 처리, 에러 메시지를 포함한다.
- API 응답 형식은 기존 클라이언트 호환을 유지한다.
- DB 접근은 repository 계층을 사용한다.

## Verification
- \'cd app-backend && uv run pytest -q\' 통과
- 이 feature 관련 테스트 1개 이상 확인/보강
