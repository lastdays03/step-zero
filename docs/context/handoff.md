# Handoff

> **크기 가이드**: 이 문서는 40줄 이내로 유지한다.

## 마지막 업데이트
- Date: 2026-03-10
- Branch: `develop` (clean)

## 이번 세션 요약
- `exception-handler-integration` Phase A~D 전체 구현 + 코드 리뷰 + 수정
- PR #31 머지, feature 브랜치 삭제 (원격+로컬)
- GlitchTip 실서버 연동 검증 완료 (이벤트 전송/필터링 확인)
- 코드 리뷰에서 3건 수정: actionkit/detail.py 구체 Exception, problem_response error_code/timestamp 일관성
- pre-push 훅 백엔드+프론트엔드 병렬 실행 개선
- setup_sentry에 try/except 추가 (잘못된 DSN으로 앱 크래시 방지)

## Uncommitted Changes
- 없음 (모두 커밋/푸시 완료)

## 다음 세션 시작점
1. 개발서버 마이그레이션: `docker compose exec app-backend uv run alembic upgrade head`
2. 다음 작업 선정 — `docs/plans/active/` 비어있음
3. (선택) 프로덕션 SENTRY_DSN 설정

## 핵심 주의사항
- 프로덕션 배포 시 `ADMIN_EMAILS`, `SENTRY_DSN` 환경변수 설정 필수
- `pnpm build`는 `next build --webpack` 사용 (Turbopack CSS panic 회피)
- 루트 `.gitignore`에 `test_*.py` 패턴 → 새 테스트 파일은 `git add -f` 필요
- `get_session()` auto-commit 안됨 → 명시적 `session.commit()` 필수

## 참조 문서
- 완료: `docs/plans/done/exception-handler-integration/`
