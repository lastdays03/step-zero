# Handoff

> **크기 가이드**: 이 문서는 40줄 이내로 유지한다.

## 마지막 업데이트
- Date: 2026-03-05
- Branch: `develop` (uncommitted 10 files, untracked 3 files)

## 이번 세션 요약
- Unified Document Viewer 전체 구현 완료 (백엔드 + 프론트엔드 + 검증)
- 백엔드: `/view` 엔드포인트 포맷별 분기, MD 뷰어 툴바, HWP 리다이렉트
- 프론트: 5개 진입점 URL `/view` 통일, "문서 보기" 버튼 추가
- pytest 398 passed, pnpm lint 0 errors

## Uncommitted Changes (develop 브랜치)
- 백엔드 3파일: files.py, schemas.py, service.py
- 프론트 7파일: DetailModal, LibraryView, LawDetailPopup, LawGuideView, types, DashboardView, TimelineStepItem
- docs 3파일: unified-doc-viewer/ 디렉토리 + REPORT

## 다음 세션 시작점
1. feature 브랜치 생성 (예: `feature/unified-doc-viewer`)
2. 코드 10파일 + docs 3파일 커밋
3. PR 생성 → develop
4. 머지 후 `docs/dev/active/unified-doc-viewer/` → `docs/dev/done/`
5. `docs/planning/REPORT-unified-document-viewer.md` → `docs/planning/completed/`
6. R2 Storage Migration 계속

## 참조 문서
- Unified Doc Viewer: `docs/dev/active/unified-doc-viewer/`
- R2 Migration: `docs/dev/active/r2-storage-migration/`

## 커밋 시 주의사항
- subject는 소문자 시작 (commitlint subject-case 규칙)
- `Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>` 포함
- **develop에 직접 커밋 X** → feature 브랜치 생성 필요
