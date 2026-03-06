# unified-doc-viewer 구현 계획

Last Updated: 2026-03-05

## Executive Summary

액션킷 문서의 뷰어/다운로드 흐름을 통합한다. 현재 5개 진입점(대시보드, 타임라인, 액션킷 모달, 법령 팝업, MD 뷰어)에서 URL 구성이 제각각이고 일부는 동작하지 않는다. 모든 진입점이 `/items/{id}/view`를 단일 진입 URL로 사용하도록 통일하고, 포맷별로 최적 처리(PDF=inline, MD=HTML+툴바, HWP/PPTX=다운로드 직행)를 적용한다.

## Current State

### 문제 요약
1. **대시보드**: `source_url=/items/{id}` → 307 리다이렉트 → `/view`, `<a download>` 무시됨 → 다운로드 안 됨
2. **타임라인**: `source_url` 경로는 `/view`로, `actionkit_item_id` 경로는 `/download`로 → 비일관
3. **액션킷 모달/법령 팝업**: "문서 보기" 버튼 없음 → 메타정보만 표시, 문서 내용 확인 불가
4. **MD 뷰어**: 다운로드/인쇄 버튼 없음 → 사용자가 파일을 받을 방법 없음
5. **HWP/PPTX**: `/view` 호출 시 바이너리 그대로 전송 → 브라우저에서 깨짐

### 파일 포맷 현황
- PDF 39개, MD 6개, HWP 6개, PPTX 1개 (총 52개)

## Proposed Future State

```
[모든 진입점] → /api/v1/actionkits/items/{id}/view
    ├─ PDF/이미지  → 브라우저 기본 뷰어 (다운로드 내장)
    ├─ MD          → HTML 렌더링 + 상단 툴바 (원본 다운로드 + 인쇄)
    └─ HWP/PPTX 등 → 302 → /download → 즉시 파일 다운로드
```

## Implementation Phases

### Phase 1: 백엔드 뷰어 엔드포인트 개선 (files.py)

#### Task 1-1: 미지원 포맷 다운로드 리다이렉트 [S]
- `view_item_current_file()`에서 뷰어 불가 확장자를 `/download`로 302 리다이렉트
- `VIEWABLE_EXTENSIONS` 상수 정의: `.md`, `.markdown`, `.pdf`, `.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`, `.svg`
- 나머지(`.hwp`, `.pptx`, `.docx`, `.xlsx` 등)는 즉시 리다이렉트
- **수정 위치**: `files.py:116-149` `view_item_current_file()` 함수
- **AC**: HWP 파일의 `/view` 호출 시 `/download`로 리다이렉트되어 파일 다운로드

#### Task 1-2: MD 뷰어 템플릿에 툴바 추가 [M]
- `_MD_HTML_TEMPLATE`에 상단 고정 툴바 삽입
  - 문서 제목 표시
  - "원본 다운로드" 버튼 → `/items/{item_id}/download` 링크
  - "인쇄 / PDF 저장" 버튼 → `window.print()`
- `@media print` 시 툴바 숨김
- 브랜드 컬러 `#36a4f2` 유지
- 템플릿에 `{item_id}` 플레이스홀더 추가, `format()` 호출부 수정
- **수정 위치**: `files.py:62-90` 템플릿 + `files.py:131-134` format 호출
- **AC**: MD 뷰어 페이지 상단에 다운로드/인쇄 버튼 표시, 인쇄 시 툴바 미포함

### Phase 2: 프론트엔드 URL 통일

#### Task 2-1: DashboardView 다운로드 URL 수정 [S]
- `documentActions` useMemo에서 URL 구성 변경
- `source_url`이 `/api/v1/actionkits/items/{id}` 패턴이면 → `/view` 추가
- `meta.actionkit_item_id`가 있으면 `API_URL + /api/v1/actionkits/items/{id}/view`
- "다운로드" 라벨 → "문서 보기"로 변경
- **수정 위치**: `DashboardView.tsx:142-173` (URL 구성) + `DashboardView.tsx:259-274` (렌더링)
- **AC**: 대시보드 "문서 보기" 클릭 → 새 탭에서 문서 뷰어 열림 (PDF=기본뷰어, MD=HTML뷰어, HWP=다운로드)

#### Task 2-2: TimelineStepItem 링크 /view로 통일 [S]
- `source_url` 분기: `/items/{id}` 패턴이면 `/view` 붙이기
- `actionkit_item_id` 분기: `/download` → `/view`로 변경
- 라벨은 "원문 보기" 유지
- **수정 위치**: `TimelineStepItem.tsx:266-302`
- **AC**: 타임라인에서 모든 문서 링크가 `/view`로 연결

#### Task 2-3: ActionKitDetailModal에 "문서 보기" 버튼 추가 [S]
- Footer에 "원본 다운로드" 왼쪽에 "문서 보기" 버튼 추가
- `item.id`가 있으면 `API_URL + /api/v1/actionkits/items/{id}/view`로 새 탭
- **수정 위치**: `ActionKitDetailModal.tsx:304-328` Footer 영역
- **의존**: ActionKitDetailModal props에 `item.id` 이미 존재 확인
- **AC**: 모달 하단에 "문서 보기" 버튼 → 새 탭에서 뷰어 열림

#### Task 2-4: LawDetailPopup에 "문서 보기" 버튼 추가 [S]
- Footer에 "원문 다운로드" 왼쪽에 "문서 보기" 버튼 추가
- LawItem에 `id` 필드가 있는지 확인 필요 → 없으면 path 기반 fallback
- **수정 위치**: `LawDetailPopup.tsx:170-191` Footer 영역
- **AC**: 법령 팝업 하단에 "문서 보기" 버튼 → 새 탭에서 뷰어 열림

### Phase 3: 검증

#### Task 3-1: 백엔드 테스트 [M]
- `tests/api/` 에 view 엔드포인트 테스트 추가
  - MD 파일 → HTMLResponse (marked.js 포함, 툴바 포함)
  - PDF 파일 → inline Response
  - HWP 파일 → 302 RedirectResponse → `/download`
- **AC**: `make test` 통과

#### Task 3-2: 프론트엔드 lint [S]
- `pnpm lint` 통과 확인
- **AC**: lint 에러 0개

## Risk Assessment

| 리스크 | 영향 | 완화 |
|--------|------|------|
| LawItem에 `id` 필드 없음 | 법령 팝업 "문서 보기" 불가 | path 기반 static file URL fallback |
| source_url 패턴이 예상과 다름 | 대시보드 URL 깨짐 | 정규식으로 `/actionkits/items/\d+$` 패턴 매칭 |
| CDN(marked.js) 접근 불가 | MD 뷰어 렌더링 실패 | 이미 기존 문제, 별도 이슈로 분리 |

## Success Metrics

1. 모든 진입점에서 "문서 보기" → 뷰어 정상 표시
2. PDF: 브라우저 기본 뷰어, MD: HTML+툴바, HWP/PPTX: 즉시 다운로드
3. `make test` + `pnpm lint` 통과
