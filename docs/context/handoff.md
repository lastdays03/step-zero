# Handoff

> **크기 가이드**: 이 문서는 40줄 이내로 유지한다.

## 마지막 업데이트
- Date: 2026-03-10
- Branch: `develop` (clean)

## 이번 세션 요약
- `actionkit-analytics-tracking` 전체 구현 (Phase 1~4)
- PR #30 생성 → 머지, feature 브랜치 삭제 (원격+로컬)
- KPI 3번째 지표 반복 개선: conversion_rate → daily_average → per_user (인당 이용 건수)
- files.py 추적: flush→commit 버그 수정, view 이벤트 KPI 포함
- stats-dashboard 용어 통일: "다운로드" → "이용"

## Uncommitted Changes
- `docs/context/dev-status.md`, `handoff.md`, `decisions.md` — 세션 반영 갱신
- `docs/plans/active/actionkit-analytics-tracking/` — done/ 아카이브 이동 필요

## 다음 세션 시작점
1. 개발서버 마이그레이션: `docker compose exec app-backend uv run alembic upgrade head`
2. docs 아카이브 커밋 (actionkit-analytics-tracking → done/)
3. 다음 작업 선정 — `docs/plans/active/` 비어있음

## 핵심 주의사항
- 프로덕션 배포 시 `ADMIN_EMAILS` 환경변수 설정 필수
- `pnpm build`는 `next build --webpack` 사용 (Turbopack CSS panic 회피)
- 루트 `.gitignore`에 `test_*.py` 패턴 → 새 테스트 파일은 `git add -f` 필요
- `get_session()` auto-commit 안됨 → 명시적 `session.commit()` 필수

## 참조 문서
- 완료: `docs/plans/done/actionkit-analytics-tracking/` (아카이브 이동 후)
