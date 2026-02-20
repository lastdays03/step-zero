# Handoff

## 마지막 업데이트
- Date: 2026-02-20
- Branch: `feature/0-community-integration`
- Latest pushed commit: `7bef0aa`

## 이번 세션 완료
- 커뮤니티 통합 리팩터링 플랜 완료:
  - `PLAN-temp-community-refactor` 4~8번 완료 후 `docs/planning/completed/`로 아카이브
- 로드맵 입력값 구조화 저장:
  - `description` 단일 저장에서 분리 필드 저장(`startup_type`, `open_timeline`, `budget_range`, `additional_notes`)으로 전환
  - 모델/스키마/API/서비스/마이그레이션(`20260220_06`) 반영
- 파일 저장 정합성 보강:
  - 그로스클럽 게시글 생성 중 DB 실패 시 파일 롤백
  - 게시글 삭제 시 첨부 파일 물리 삭제
- API 레이어 정리:
  - 그로스클럽 생성/삭제 비즈니스 로직을 `features/growth_club/application/post_service.py`로 분리
- 레거시 placeholder 경로 정리:
  - `app-backend/app/api/v1/community/*`, `app-backend/app/features/community/*`, `app-frontend/src/features/community/*` 제거
  - 프론트 업로드 URL 해석 유틸 공통화(`features/growth-club/utils/upload-url.ts`)
- Ops 기획/화면 시작:
  - 신규 플랜: `docs/planning/PLAN-ops-growth-club-moderation.md`
  - Ops 메인 카드 추가 + `/ops/growth-club` 페이지 추가

## 검증
- Backend: `cd app-backend && .venv/bin/pytest -q` 통과 (`24 passed`)
- Backend: `cd app-backend && ./scripts/check_migrations.sh` 통과 (head: `20260220_06`)
- Frontend: `cd app-frontend && npm run lint` 통과 (경고 2건: `no-img-element`)

## 다음 세션 시작점
1. `/ops/growth-club` 실제 신고 큐/조치 API 및 화면 구현
2. Ops IA 재정의(운영 리포트 명칭/카드 구성 확정)
3. 남은 문서의 v1/v2 경로 표기 일관성 정리

## 리스크/메모
- 워킹트리에 기존 변경(`.env.example`, `core/config.py`, `CreatePostForm.tsx` 등) 포함된 상태로 커밋 예정
- `app-backend/uploads/profile`는 런타임 자동 생성되며 현재 경로 정책과 일치
