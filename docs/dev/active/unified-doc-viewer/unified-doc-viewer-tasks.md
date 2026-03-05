# unified-doc-viewer 태스크

Last Updated: 2026-03-05

## Phase 1: 백엔드 뷰어 엔드포인트 개선

- [x] **1-1** 미지원 포맷 `/view` → `/download` 리다이렉트 (`files.py`) [S]
  - VIEWABLE_EXTENSIONS 상수 정의
  - view_item_current_file()에 리다이렉트 분기 추가
  - AC: HWP `/view` → 302 → `/download`

- [x] **1-2** MD 뷰어 템플릿 툴바 추가 (`files.py`) [M]
  - _MD_HTML_TEMPLATE에 상단 고정 툴바 (제목 + 원본 다운로드 + 인쇄)
  - item_id 플레이스홀더 추가 + format() 호출 수정
  - @media print 시 툴바 숨김
  - AC: MD 뷰어에 다운로드/인쇄 버튼 표시

## Phase 2: 프론트엔드 URL 통일

- [x] **2-1** DashboardView URL 수정 (`DashboardView.tsx`) [S]
  - documentActions의 downloadUrl → viewUrl 변경 (/view 경로)
  - 라벨 "다운로드" → "문서 보기"
  - AC: 대시보드에서 문서 보기 → 뷰어 열림

- [x] **2-2** TimelineStepItem 링크 통일 (`TimelineStepItem.tsx`) [S]
  - source_url 분기: /items/{id} 패턴이면 /view 추가
  - actionkit_item_id 분기: /download → /view
  - AC: 타임라인 문서 링크 → /view 통일

- [x] **2-3** ActionKitDetailModal "문서 보기" 버튼 (`ActionKitDetailModal.tsx`) [S]
  - Footer에 "문서 보기" 버튼 추가 (새 탭 /view)
  - AC: 모달에서 문서 내용 확인 가능

- [x] **2-4** LawDetailPopup "문서 보기" 버튼 (`LawDetailPopup.tsx`) [S]
  - Footer에 "문서 보기" 버튼 추가 (새 탭, path 기반 URL)
  - LawItem에 id 없음 → path 기반 fallback 적용
  - AC: 법령 팝업에서 문서 내용 확인 가능

## Phase 3: 검증

- [x] **3-1** 백엔드 테스트 통과 [M]
  - 398 passed (기존 LLM 의존 테스트 10개 실패 — 변경 무관)
  - AC: `make test` 기존 테스트 깨지지 않음

- [x] **3-2** 프론트엔드 lint 통과 [S]
  - AC: `pnpm lint` 에러 0개
