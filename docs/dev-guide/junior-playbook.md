# Junior Playbook (Vibe Coding)

## 목적
- 4명의 주니어 개발자가 동일한 방식으로 빠르게 개발하고, 품질/경계 위반 없이 PR을 올리도록 표준화한다.

## 공통 작업 루프
1. 이슈 확인: 범위/완료조건(DoD) 3줄 요약
2. 브랜치 생성: `feature/<issue-number>-<slug>`
3. 구현: 담당 feature 폴더 내부부터 수정
4. 로컬 검증:
- 백엔드 변경: `cd app-backend && .venv/bin/pytest -q`
- 프론트 변경: `cd app-frontend && npm run lint`
5. PR 작성(한국어): `요약 / 변경 사항 / 검증`

## 백엔드 구현 순서 (필수)
1. 도메인 규칙 정리: `app-backend/app/features/<feature>/domain`
2. 유스케이스 구현: `app-backend/app/features/<feature>/application`
3. 라우터 구현: `app-backend/app/api/v1/<feature>/router.py`
4. 엔드포인트 등록: `app-backend/app/api/v1/api.py`에 `include_router`
5. 스키마 반영: `app-backend/app/api/v1/schemas.py` 또는 feature 로컬 스키마

## API 라우터 적용 규칙
- 엔드포인트 함수는 feature 라우터 파일에만 만든다.
- `api.py`에서는 prefix 조합과 include만 담당한다.
- prefix는 기능명 기준으로 고정한다.
- `Depends`는 라우터 계층에서만 선언하고 비즈니스 로직은 application 계층으로 넘긴다.

## 모델/리포지토리 적용 규칙
- DB 테이블 모델은 `app-backend/app/models`에서만 관리한다.
- DB 조회/저장은 `app-backend/app/repositories`에서만 수행한다.
- feature `application`은 repository를 주입받아 사용한다.
- 라우터에서 SQL 쿼리를 직접 작성하지 않는다.
- 공용 모델/리포지토리 변경 시 PR 본문에 영향 범위를 반드시 기록한다.

## 인증/권한 wiring 규칙
- 사용자 인증은 `app-backend/app/api/deps.py`의 의존성으로 처리한다.
- 팀 컨텍스트가 필요한 API는 `X-Team-Id` 처리 포함 여부를 확인한다.
- 운영자 전용 API는 `require_platform_admin` 의존성을 명시한다.

## Vibe Coding 규칙
- 작은 단위로 자주 커밋한다.
- 한 PR은 한 목적만 담는다.
- 동작 변경 시 테스트 또는 스냅샷 근거를 반드시 남긴다.
- 에러 핸들링은 사용자 메시지까지 포함한다.

## 금지 사항
- 담당 feature 경계를 넘는 무분별한 리팩터링
- 시크릿/토큰 원문 출력
- 로그 원문을 PR 본문에 붙여넣기
- CI 깨진 상태로 머지 요청

## PR 체크리스트
- [ ] 변경 범위가 담당 feature에 국한되는가
- [ ] API 경로가 `/api/v1` 기준인가
- [ ] 로컬 검증 결과를 PR 본문에 요약했는가
- [ ] 로딩/에러/빈 상태(UI) 또는 예외 처리(API)가 있는가

## 오류 대응
- 401/403: 인증/권한/팀 컨텍스트(`X-Team-Id`) 확인
- 500: 서버 로그에서 실제 예외 타입 확인 후 수정
- 503: 외부 서비스 또는 DB 연결 상태 확인
