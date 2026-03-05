# REPORT: 통합 문서 뷰어/다운로드 개선

## 1. 현황 분석

### 1.1 파일 포맷별 현황

| 포맷 | 개수 | 뷰어 지원 | 다운로드 | 비고 |
|------|------|----------|---------|------|
| `.pdf` | 39개 | 브라우저 기본 뷰어 (inline) | OK | 법령/가이드 |
| `.md` | 6개 | marked.js HTML 변환 | OK (원본만) | 큐레이션 법령 |
| `.hwp` | 6개 | 미지원 → 다운로드 직행 | OK | 한글 양식 (근로계약서 등) |
| `.pptx` | 1개 | 미지원 → 다운로드 직행 | OK | 보조금 자료 |

### 1.2 진입점별 문제

#### A. 대시보드 "다운로드" 버튼 (`DashboardView.tsx:142-173`)
- `source_url` = `/api/v1/actionkits/items/{id}` (마이그레이션 009에서 생성)
- `GET /items/{id}`는 **307 → `/view`로 리다이렉트** (다운로드 아님)
- `<a download>` 속성이 있지만 리다이렉트 시 무시됨
- **결과: 다운로드 안 됨, /view 페이지가 새 탭에 열림**

#### B. 액션킷 라이브러리 (`ActionKitLibraryView.tsx`)
- `handleDownload()`는 `apiClient.get(/download, {responseType: 'blob'})` → 정상 동작
- 하지만 "미리보기" 클릭 시 `ActionKitDetailModal`은 **메타정보만 표시**
- 실제 MD/PDF 문서 내용을 모달 안에서 볼 수 없음
- `/view` 엔드포인트를 프론트에서 호출하는 곳이 **없음**

#### C. 법령 가이드 (`LawGuideView.tsx`)
- path 기반 다운로드만 사용 (`{baseURL}/{path}`)
- `item.id` 미사용 → DB 기반 다운로드 우회
- 클릭 시 `LawDetailPopup` 모달 → 메타정보만 표시 (문서 뷰어 없음)

#### D. 로드맵 타임라인 (`TimelineStepItem.tsx:266-302`)
- `actionkit_item_id` 있으면 `/download` 직접 호출 → 정상
- `source_url` 있으면 해당 URL 새 탭 → `/items/{id}` → `/view` 리다이렉트
- **일관성 없음**: 같은 문서인데 진입점에 따라 다운로드 또는 뷰어

#### E. MD 뷰어 (`_MD_HTML_TEMPLATE`)
- 순수 렌더링만 (스타일링된 HTML 페이지)
- **다운로드 버튼 없음** → 사용자가 원본 MD 또는 PDF로 받을 방법 없음
- 뒤로가기 버튼, 네비게이션 없음

### 1.3 백엔드 뷰어 엔드포인트 정리 (`files.py`)

```
GET /items/{id}          → 307 리다이렉트 → /view
GET /items/{id}/view     → 포맷별 인라인 표시 (MD→HTML, PDF→inline, 기타→binary)
GET /items/{id}/download → FileResponse (attachment 헤더)
```

---

## 2. 통합 설계: 일관된 뷰어 → 다운로드 흐름

### 2.1 핵심 원칙

1. **모든 진입점에서 동일한 흐름**: 클릭 → 뷰어 → (필요시) 다운로드
2. **포맷별 최적 처리**: PDF/이미지는 브라우저 기본, MD는 marked.js + 다운로드 버튼, HWP/PPTX는 다운로드 직행
3. **단일 URL 패턴**: `/api/v1/actionkits/items/{id}/view` (뷰어) + `/download` (다운로드)

### 2.2 포맷별 처리 전략

| 포맷 | `/view` 동작 | 다운로드 | 비고 |
|------|-------------|---------|------|
| `.pdf` | 브라우저 기본 PDF 뷰어 (inline) | 브라우저 내장 다운로드 | 추가 작업 불필요 |
| `.md` | marked.js HTML 렌더링 | **상단 툴바에 "원본 다운로드" + "인쇄" 버튼 추가** | 기존 템플릿 개선 |
| `.hwp`, `.pptx` 등 | **`/download`로 리다이렉트** | 즉시 다운로드 | 안내 페이지 불필요 |
| 이미지 | 브라우저 기본 (inline) | 브라우저 내장 | 추가 작업 불필요 |

### 2.3 변경 범위

#### 백엔드 (1 파일)

**`app-backend/app/api/v1/actionkit/files.py`**

1. `_MD_HTML_TEMPLATE` 개선
   - 상단 툴바: 제목 + "원본 다운로드(.md)" 버튼 + "인쇄(PDF)" 버튼
   - `@media print` 시 툴바 숨김

2. `view_item_current_file()` 분기 확장
   ```python
   if ext in (".md", ".markdown"):
       return HTMLResponse(...)       # 기존 + 툴바 추가
   elif ext in (".pdf", ".jpg", ...):
       return Response(inline)        # 기존 유지
   else:  # .hwp, .pptx, .docx 등
       return RedirectResponse(f"/api/v1/actionkits/items/{item_id}/download")
   ```

#### 프론트엔드 (4 파일)

**1. `DashboardView.tsx` — 다운로드 URL 수정**
- `source_url`이 `/items/{id}`면 → `/items/{id}/view`로 변경
- 라벨: "문서 보기" (뷰어로 이동)
- 별도 직접 다운로드 링크도 병행 가능

**2. `TimelineStepItem.tsx` — 링크 통일**
- `source_url`, `actionkit_item_id` 모두 → `/view`로 통일
- HWP/PPTX는 `/view`가 자동으로 `/download` 리다이렉트

**3. `ActionKitDetailModal.tsx` — "문서 보기" 버튼 추가**
- 기존 "원본 다운로드" 옆에 "문서 보기" 버튼 → 새 탭에서 `/view`

**4. `LawDetailPopup.tsx` — 동일 패턴 적용**
- "원문 다운로드" 옆에 "문서 보기" 버튼 추가

### 2.4 URL 흐름 (수정 후)

```
[모든 진입점] → "문서 보기" 클릭
    └─ 새 탭: /api/v1/actionkits/items/{id}/view
        ├─ PDF      → 브라우저 PDF 뷰어 (다운로드 내장)
        ├─ MD       → HTML 페이지 + 상단 다운로드/인쇄 버튼
        ├─ 이미지    → 브라우저 기본
        └─ HWP/PPTX → 302 리다이렉트 → /download → 즉시 다운로드
```

---

## 3. 구현 상세

### 3.1 MD 뷰어 템플릿 개선안

```html
<!-- 상단 고정 툴바 -->
<div class="toolbar">
  <span class="title">{title}</span>
  <div class="actions">
    <a href="/api/v1/actionkits/items/{item_id}/download" class="btn">
      원본 다운로드
    </a>
    <button onclick="window.print()" class="btn-outline">
      인쇄 / PDF 저장
    </button>
  </div>
</div>

<!-- 마크다운 콘텐츠 -->
<div id="content"></div>

<style>
  @media print { .toolbar { display: none; } }
</style>
```

### 3.2 미지원 포맷 처리 (view 엔드포인트)

```python
# .hwp, .pptx 등 뷰어 미지원 → 다운로드로 즉시 리다이렉트
VIEWABLE_EXTENSIONS = {".md", ".markdown", ".pdf", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}

if ext not in VIEWABLE_EXTENSIONS:
    return RedirectResponse(
        url=f"/api/v1/actionkits/items/{item_id}/download",
        status_code=302,
    )
```

### 3.3 DashboardView 수정안

```tsx
// Before (문제: /items/{id} → 307 → /view, download 속성 무시)
const downloadUrl = ... || doc.source_url || null;

// After (명시적 /view 경로)
const actionkitItemId = meta.actionkit_item_id as number | undefined;
const viewUrl = actionkitItemId
    ? `${API_URL}/api/v1/actionkits/items/${actionkitItemId}/view`
    : doc.source_url
        ? (doc.source_url.startsWith("/") ? `${API_URL}${doc.source_url}/view` : doc.source_url)
        : null;
```

---

## 4. 작업 목록

| # | 작업 | 파일 | 우선순위 |
|---|------|------|---------|
| 1 | MD 뷰어 템플릿에 다운로드/인쇄 툴바 추가 | `files.py` | P0 |
| 2 | 미지원 포맷 `/view` → `/download` 리다이렉트 | `files.py` | P0 |
| 3 | 대시보드 URL → `/view` 명시적 경로 사용 | `DashboardView.tsx` | P0 |
| 4 | 타임라인 링크 `/view`로 통일 | `TimelineStepItem.tsx` | P1 |
| 5 | 액션킷 모달에 "문서 보기" 버튼 추가 | `ActionKitDetailModal.tsx` | P1 |
| 6 | 법령 팝업에 "문서 보기" 버튼 추가 | `LawDetailPopup.tsx` | P1 |
