# Handoff

> **크기 가이드**: 이 문서는 40줄 이내로 유지한다.

## 마지막 업데이트
- Date: 2026-03-12
- Branch: `develop` (clean)

## 이번 세션 요약
- Playwright MCP 통합 디버깅 인프라 Phase 3 완료 + 전체 아카이브
  - social-mock 인증(`ENABLE_SOCIAL_MOCK=true`)으로 authenticated 시나리오 MCP 재현 성공
  - 5개 페이지 Core Web Vitals 베이스라인 측정 (모두 목표치 통과)
  - 성능 회귀 감지 기준 (Warning ≥80%, Fail ≥100%) 문서화
  - `/growth-club` 성능 이슈 발견: TTFB 838ms, 이미지 404 다수
- 커밋 & 푸시 완료 (`75d1409`)
- playwright-mcp-integration 계획 done/ 아카이브

## Uncommitted Changes
- 없음 (dev-docs-update 커밋 대기)

## 다음 세션 시작점
1. 다음 작업 선정 — `docs/plans/active/` 비어있음
2. (선택) `/growth-club` 성능 최적화 (TTFB 838ms, 이미지 리소스 404)
3. (선택) Playwright CLI spec 도입 (CI 회귀 테스트)
4. (선택) 프로덕션 SENTRY_DSN 설정

## 핵심 주의사항
- `ENABLE_SOCIAL_MOCK=true`로 변경됨 — 프로덕션 배포 전 반드시 `false` 확인
- 프로덕션 배포 시 `ADMIN_EMAILS`, `SENTRY_DSN` 환경변수 설정 필수
- `pnpm build`는 `next build --webpack` 사용 (Turbopack CSS panic 회피)
- `get_session()` auto-commit 안됨 → 명시적 `session.commit()` 필수

## 참조 문서
- 완료: `docs/plans/done/playwright-mcp-integration/`
- 성능 베이스라인: `docs/plans/done/playwright-mcp-integration/playwright-mcp-integration-context.md` (Performance Baseline 섹션)
