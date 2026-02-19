# Handoff

## 마지막 업데이트
- Date: 2026-02-19
- Branch: `develop`
- Latest local commit: `cbc68db`

## 이번 세션 완료
- 로드맵 생성 비동기 파이프라인 구축:
  - ARQ + Redis 기반 Jobs API (`/api/v1/roadmaps/jobs`, 상태/결과 조회)
  - 워커 엔트리 추가(`app.workers.roadmap_worker`)
  - `docker-compose.dev.yml`에 `app-worker` 서비스 반영
- 로드맵 상세 데이터 모델/조회 확장:
  - `roadmap_step_details`, `roadmap_step_actions` 모델/리포지토리/마이그레이션 추가
  - `GET /api/v1/roadmaps/{id}/detail`, `GET /api/v1/roadmaps/latest/detail` 구현
- 입력 검증 강화:
  - `/api/v1/roadmaps/jobs/validate` 추가
  - 생성 API에서 서버 측 검증 강제(프론트 우회 차단)
- 실행형 로드맵 기능 구현:
  - Step 상태 전이 API: `PATCH /api/v1/roadmaps/tasks/{step_id}`
  - Action 완료 토글 API: `PATCH /api/v1/roadmaps/tasks/{step_id}/actions/{action_id}`
  - 체크리스트/문서 완료 시 step 자동 완료 + 다음 step 자동 진행
- 프론트 `/roadmap` 실행형 화면 전환:
  - 생성 전/생성 중/생성 후 상태 분리
  - phase/task/action 렌더 + 체크리스트/문서 토글
  - 로드맵 존재 시 생성 폼 우선 노출 버그 수정
- 대시보드 정합화:
  - roadmap 리스트를 phase 요약(`completed/current/locked`) 기준으로 계산
  - current phase 제목을 step detail phase와 동기화
- 문서 정비:
  - README/아키텍처/tech foundation 실행 명령 `docker compose -f docker-compose.dev.yml up -d --build` 기준으로 갱신
  - 실행형 로드맵 계획 문서 추가(`docs/planning/PLAN-roadmap-execution-screen.md`)

## 다음 세션 시작점
1. `/roadmap` 실행형 UI를 시안 기준으로 디테일 튜닝(타이포/간격/컴포넌트 스타일)
2. action 완료 규칙 최종 정책 확정(문서 필수 유지 여부, 법적근거 제외 유지)
3. 대시보드 카드(서류/일정)를 실제 roadmap action 데이터로 연동
4. OpenAPI 타입 재동기화(`app-frontend` `types:sync`) 및 프론트 타입 정리
5. 커밋 단위 분리(백엔드 기능, 프론트 UI, 문서) 후 푸시/PR

## 리스크/메모
- 로드맵 생성은 `app-worker` 미기동 시 `QUEUED`에서 진행 정지됨
- 인증 없는(guest) 상태에서 `/roadmap/latest/detail` 호출 시 401이므로, 프론트 상태 분기 유지 필요
- 현재 워킹트리에 변경 파일이 많아 커밋 전 논리적 단위 분리가 필요함
