# StepZero 프로젝트 운영 규칙 (v20260214)

## 1. 목적과 적용 범위
- 목적: 4주 MVP 기간에 병렬 개발 속도를 유지하면서 품질/안정성을 지키기 위한 운영 기준을 명확히 한다.
- 적용 범위: `step-zero` 모노레포 전체(`app-backend`, `app-frontend`, 루트 CI/훅/문서).

## 2. 운영 원칙
- 작은 PR, 빠른 리뷰, 빠른 통합을 기본 원칙으로 한다.
- 도메인 단위 ownership을 유지하고 공통 레이어 변경은 리드 승인 후 반영한다.
- 기능 추가보다 운영 리스크(오안내, 장애, 데이터 손상) 차단을 우선한다.

## 3. 브랜치/머지 규칙
- 기본 브랜치: `develop`
- 허용 흐름:
- `feature/*` -> `develop`
- `hotfix/*` -> `develop`
- `release/*` -> `develop`
- `develop` -> `main` (최종 릴리즈)
- 금지:
- `main` 직접 push
- `feature/*`에서 `main` 직접 PR
- 브랜치명 규칙:
- `feature/<issue-number>-<short-slug>`
- `hotfix/<issue-number>-<short-slug>`
- `release/<name>`

## 4. 커밋/PR 규칙
- 커밋 메시지: Conventional Commits (`feat|fix|docs|refactor|test|chore|perf|ci|build|revert`)
- 로컬 훅:
- `commit-msg`: commitlint 검사
- `pre-push`: backend 테스트 + frontend lint
- PR 작성:
- 제목/본문은 한글
- `요약`, `변경 사항`, `검증`, `영향 범위`, `참고 이슈`를 포함
- 터미널 원본 로그를 본문에 그대로 붙이지 않는다.

## 5. CI 기준 (현재 리포지토리 기준)
- PR 대상 브랜치: `main`, `develop`
- CI 필수 검사:
- 흐름 정책(`pr-flow-policy`)
- 브랜치명 규칙(`branch-name`)
- 커밋 메시지(`commitlint`)
- backend 테스트(`pytest -q`)
- frontend lint(`pnpm lint`)
- PR 본문 품질 검사는 현재 `warning only`로 운영한다.

## 6. 환경변수/시크릿 규칙
- 백엔드 로드 정책:
- 기본값은 `.env`
- 로컬 비밀값은 `.env.local`에서 override
- 최종 적용값 기준으로는 `.env.local`이 우선한다.
- `.env`에는 비밀값을 넣지 않는다.
- `.env.local`은 Git 추적 금지 상태를 유지한다.
- 시크릿 점검 시 값 전체 출력 금지:
- 존재 여부/길이/형식만 출력한다.

## 7. 백엔드 개발 규칙
- 새 기능 API는 `v2` 우선 구현, `v1`은 호환 유지한다.
- DB 스키마 변경 시 Alembic 마이그레이션 필수.
- 완료 전 최소 검증:
- `cd app-backend && uv run pytest -q`
- 설정 변경 시 필수 확인:
- `app/core/config.py` 환경변수 우선순위/기본값/placeholder 정규화 동작

## 8. 프론트엔드 개발 규칙
- 개발 서버: `pnpm dev` (`next dev --webpack`)
- OpenAPI 타입 동기화:
- `pnpm types:sync`
- 상태/렌더링 규칙:
- loading/error/empty 상태를 명시한다.
- SSR 하이드레이션 충돌을 유발하는 초기 렌더 불일치를 금지한다.
- 인증/권한 UI는 초기 서버 렌더와 클라이언트 렌더의 DOM 구조가 달라지지 않게 설계한다.
- 완료 전 최소 검증:
- `cd app-frontend && pnpm lint`

## 9. 테스트 및 품질 게이트
- 기능 PR 최소 조건:
- happy-path 1개 이상
- 권한/예외 케이스 1개 이상
- 회귀 방지:
- 버그 수정 시 재현 가능한 테스트를 함께 추가한다.
- 병합 전 체크 순서 권장:
- backend 테스트 -> frontend lint -> 수동 시나리오 확인

## 10. 데이터/마이그레이션 운영 규칙
- 마이그레이션 파일은 기능 브랜치에서 생성 가능하나, `develop` 머지 전 충돌 재정렬한다.
- 다운타임 유발 가능 변경(컬럼 삭제, 타입 강변환)은 사전 공지 후 배치한다.
- 운영 리스크가 큰 변경은 2단계 배포를 기본으로 한다.
- 1단계: nullable/additive 변경
- 2단계: 코드 전환 후 정리 변경

## 11. 장애 및 핫픽스 대응
- 우선순위:
- P0: 로그인 불가, 데이터 손상, 법령/정책 치명 오안내
- P1: 핵심 경로 성능/오류 증가
- P0 기본 절차:
- 신규 배포 중지
- 영향 기능 임시 비활성화(필요 시)
- 핫픽스 브랜치 생성 후 최소 수정
- 원인/대응/재발방지 기록
- 공지 원칙:
- 사용자 영향이 있는 경우, 원인 확정 전이라도 현상/임시조치 먼저 공지

## 12. 문서/기록 운영
- 기능 단위로 `docs/planning` 또는 `docs/operations`에 결정 사항을 남긴다.
- API/정책 변경 시 PR에 영향 범위를 명시한다.
- 릴리즈 전에는 변경 요약과 롤백 계획을 문서화한다.

## 13. 산출물/아티팩트 관리
- 디버그/측정 산출물은 `.temp/artifacts/` 하위에만 저장한다.
- 루트 경로에 임시 파일 생성 금지.
- 1회성 파일은 검증 후 정리하고, 장기 보관 필요 시 목적별 하위 폴더로 이동한다.

## 14. 주간 운영 리듬 (권장)
- 월요일:
- 주간 목표 확정, 담당자/우선순위 확정
- 화/목:
- 중간 점검(블로커/스코프 재조정)
- 금요일:
- 통합 테스트, 미해결 이슈 이월 기준 정리
- 매일:
- 작업 시작 전 `develop` 리베이스/동기화

## 15. Definition of Ready / Done
- Ready:
- 요구사항/수용기준/영향 범위가 이슈에 명시됨
- 선행 의존성(API/스키마/디자인) 확인 완료
- Done:
- 코드 + 테스트 + 문서 반영
- CI 통과
- 영향 범위와 롤백 방법이 PR에 기록됨

