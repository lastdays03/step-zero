# Dev Status

## Last Updated
- Date: 2026-03-01
- Branch: `feature/0-roadmap-improvement` (develop로 PR 완료)

## Sprint Focus
- Phase 0 로드맵 파이프라인 전면 수정 (링크 오류, source_url 통일, startup_method 추가, 파일 URL 접근성)

## Current State
- Phase 0 전체 구현 완료 및 개발 서버 배포 완료
- Backend pytest: 177 passed, 1 skipped
- Frontend lint + build: 통과
- `npm run types:sync`: `startup_method` 포함 타입 생성 확인
- `black` + `isort`: 변경 불필요 (이미 포맷 완료)
- 수동 검증: 기존 링크, 파일 뷰어, 새 로드맵 생성, 인테이크 폼 모두 확인 완료

## Completed (Phase 0)
- **Phase A**: LLM 참조 자동 복구, 다중 파일 매핑, FE 폴백/대안 링크
- **Phase B**: source_url item_id 기반 통일, DB 마이그레이션 (396건), 퍼지 매칭
- **Phase C**: startup_method DB→BE→FE 전 계층 추가
- **Phase D**: 이중 인코딩 StaticFiles, FE API_URL prefix, 아이템 뷰어 엔드포인트
- Git 커밋 & PR 생성 완료, 개발 서버 배포 완료

## In Progress
- (없음 — Phase 0 작업 완료)

## Risks And Blockers
- `types:sync`로 생성된 `openapi.json` + `api-types.ts` 변경분 커밋 필요

## Next 3 Actions
1. `types:sync` 결과물 (`openapi.json`, `api-types.ts`) 커밋
2. Phase 0 PR develop 머지
3. Phase 2 (템플릿 매칭) 또는 Ops 운영 고도화 착수

## Test Status
- Backend pytest (Docker): 177 passed, 1 skipped
- Frontend lint (Docker): 통과
- Frontend build (Docker): Next.js 16.1.6 Turbopack 성공
- `npm run types:sync`: 정상 생성

## Sync Notes
- 2026-03-01: Phase 0 전체 완료 — 로드맵 파이프라인 링크 오류 수정, source_url 통일, startup_method 추가, 파일 URL 접근성 개선
- 2026-03-01: DB 마이그레이션 009 적용 (startup_method 컬럼 + source_url 일괄 변환)
- 2026-03-01: `npm run types:sync` 실행으로 BE OpenAPI → FE 타입 동기화 확인
