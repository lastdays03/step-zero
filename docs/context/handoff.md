# Handoff

## 마지막 업데이트
- Date: 2026-02-16
- Branch: `develop`
- Latest pushed commit: `32ca234`

## 이번 세션 완료
- `/ops` 권한 모델을 팀 단위가 아닌 플랫폼 운영자(`User.is_superuser`) 단일 모델로 확정
- 백엔드 `/api/v2/ops/*` 공통 가드(`require_platform_admin`) 적용
- 운영콘솔 MVP 화면 추가:
  - `/ops`
  - `/ops/users`
  - `/ops/reports`
- 운영 API 최소 구현:
  - `GET /api/v2/ops/users`
  - `GET /api/v2/ops/reports/summary`
- 프론트 인증 상태에 `canAccessOps` 추가 및 메뉴 노출 제어 반영
- `app-backend/scripts/setup_dev.sh` 개선:
  - Python 3.11 미만 환경 즉시 실패 처리
  - macOS에서 `python3.11`이 없고 `uv`가 있으면 `uv` 자동 사용
- 환경 템플릿/경로 복구:
  - `app-backend/.env.example` 추가
  - `app-frontend/src/lib` 복구(`api-client.ts`, `api-types.ts`, `utils.ts`)
  - `.gitignore` 예외 규칙 보정(`app-frontend/src/lib`, `app-backend/.env.example`)

## 다음 세션 시작점
1. `/ops/users`, `/ops/reports` 실제 운영 지표/필드 확정 및 데이터 연동
2. `roadmap`/`actionkit` placeholder를 실제 데이터 로딩 화면으로 교체
3. 백엔드/프론트 품질 게이트 재실행(환경 준비 후 `pytest`, `lint`)
4. Context memory 운영 검증 Day 2~7 기록 누적

## 리스크/메모
- 로컬 실행 시 백엔드 미기동(`DATABASE_URL`, `SECRET_KEY` 누락 또는 DB 미기동)일 때 프론트 `Network Error` 발생
- Google Font fetch 실패 시 네트워크 제한 환경에서 `next build` 실패 가능
