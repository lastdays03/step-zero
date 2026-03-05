# Dev Status

> **크기 가이드**: 이 문서는 50줄 이내로 유지한다.

## Last Updated
- Date: 2026-03-05
- Branch: `develop` (uncommitted 10 files + untracked 3 files)

## Sprint Focus
- Unified Document Viewer (액션킷 문서 뷰어/다운로드 통합)

## Current State
- Phase 0~4: 전체 완료 (develop 머지 완료)
- Runtime Upgrade: PR #20 머지 완료
- **Unified Doc Viewer: 구현 완료, 커밋/PR 대기**

## Completed (최근)
- Unified Doc Viewer Phase 1~3: 백엔드 뷰어 개선 + 프론트 URL 통일 + 검증
- 백엔드 files.py: VIEWABLE_EXTENSIONS 분기, MD 툴바, 미지원 포맷 리다이렉트
- 프론트 5개 파일: /view URL 통일, "문서 보기" 버튼 추가

## In Progress
- Unified Doc Viewer: 커밋 + feature 브랜치 + PR 생성 필요
- R2 Storage Migration (docs/dev/active/r2-storage-migration/)

## Risks And Blockers
- 없음

## Next 3 Actions
1. feature 브랜치 생성 + 10개 파일 커밋 (feat: unified document viewer)
2. PR 생성: feature branch → develop
3. 머지 후 unified-doc-viewer 문서 아카이브

## Test Status
- Backend pytest: 398 passed (LLM 의존 10개 기존 실패 — 변경 무관)
- Frontend lint: 0 errors
