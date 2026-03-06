# unified-doc-viewer 컨텍스트

Last Updated: 2026-03-05
Status: ALL TASKS COMPLETED - 커밋 대기 중

## Related Planning Doc

- `docs/planning/REPORT-unified-document-viewer.md` — 현황 분석 + 설계 보고서

## Key Files

### Backend (수정 대상)
| 파일 | 역할 | 수정 내용 |
|------|------|----------|
| `app-backend/app/api/v1/actionkit/files.py` | 뷰어/다운로드 엔드포인트 | 미지원 포맷 리다이렉트 + MD 템플릿 툴바 |

### Frontend (수정 대상)
| 파일 | 역할 | 수정 내용 |
|------|------|----------|
| `app-frontend/src/features/dashboard/components/DashboardView.tsx` | 대시보드 필요 서류 | URL `/view` 변경 + 라벨 변경 |
| `app-frontend/src/features/roadmap/components/TimelineStepItem.tsx` | 로드맵 타임라인 액션 링크 | `/download` → `/view` 통일 |
| `app-frontend/src/features/actionkit/components/ActionKitDetailModal.tsx` | 액션킷 상세 모달 | "문서 보기" 버튼 추가 |
| `app-frontend/src/features/actionkit/components/LawDetailPopup.tsx` | 법령 상세 팝업 | "문서 보기" 버튼 추가 |

### Backend (참조용)
| 파일 | 역할 |
|------|------|
| `app-backend/app/repositories/actionkit_repository.py` | `list_current_files()` — item_id→파일 조회 |
| `app-backend/app/models/actionkit.py` | ActionKitFile 모델 (object_key, mime_type 등) |
| `app-backend/app/features/actionkit/application/service.py` | `_to_public_path()` — path 생성 |
| `app-backend/alembic/versions/009_startup_method_and_source_urls.py` | source_url 자동 생성 마이그레이션 |

### Frontend (참조용)
| 파일 | 역할 |
|------|------|
| `app-frontend/src/features/actionkit/types/index.ts` | LawItem, ActionKitItem 타입 |
| `app-frontend/src/features/actionkit/components/ActionKitLibraryView.tsx` | handleDownload() 참조 패턴 |

## Key Decisions

1. **HWP/PPTX는 안내 페이지 없이 다운로드 직행** — 브라우저에서 볼 수 없으므로 리다이렉트만
2. **`/view`를 단일 진입 URL로 통일** — 포맷별 분기는 백엔드가 담당
3. **MD 뷰어 다운로드 = 원본 .md 파일** — PDF 변환은 `window.print()` (브라우저 위임)
4. **프론트에서 포맷 판단 불필요** — 백엔드 `/view`가 알아서 처리 (PDF=inline, MD=HTML, HWP=redirect)

## API Endpoints (정리)

```
GET /api/v1/actionkits/items/{id}          → 307 → /view (기존 유지)
GET /api/v1/actionkits/items/{id}/view     → 포맷별 분기 (개선)
GET /api/v1/actionkits/items/{id}/download → FileResponse attachment (기존 유지)
```

## Implementation Summary

### 추가 수정된 파일 (계획 외)
| 파일 | 이유 |
|------|------|
| `app-backend/app/api/v1/actionkit/schemas.py` | ActionKitItemResponse에 `id` 필드 추가 (프론트에서 view URL 구성에 필요) |
| `app-backend/app/features/actionkit/application/service.py` | `_to_public_path()` 결과에 id 포함하도록 수정 |
| `app-frontend/src/features/actionkit/types/index.ts` | LawItem/ActionKitItem 타입에 `id` 필드 추가 |
| `app-frontend/src/features/actionkit/components/ActionKitLibraryView.tsx` | handleDownload → handleView로 리팩토링 |
| `app-frontend/src/features/actionkit/components/LawGuideView.tsx` | 법령 가이드 뷰에서 view URL 연동 |

### 핵심 구현 패턴
- **백엔드 `/view` 분기**: `VIEWABLE_EXTENSIONS` 상수로 지원 포맷 판별, 미지원 시 302 → `/download`
- **MD 뷰어 툴바**: `_MD_HTML_TEMPLATE`에 `{item_id}` 플레이스홀더 추가, 다운로드/인쇄 버튼
- **프론트 URL 통일**: 모든 진입점에서 `/api/v1/actionkits/items/{id}/view`로 `window.open()`
- **LawItem path fallback**: LawItem에는 numeric id가 없어 `path` 기반 URL 사용

## Uncommitted Changes (10 files)
```
M app-backend/app/api/v1/actionkit/files.py
M app-backend/app/api/v1/actionkit/schemas.py
M app-backend/app/features/actionkit/application/service.py
M app-frontend/src/features/actionkit/components/ActionKitDetailModal.tsx
M app-frontend/src/features/actionkit/components/ActionKitLibraryView.tsx
M app-frontend/src/features/actionkit/components/LawDetailPopup.tsx
M app-frontend/src/features/actionkit/components/LawGuideView.tsx
M app-frontend/src/features/actionkit/types/index.ts
M app-frontend/src/features/dashboard/components/DashboardView.tsx
M app-frontend/src/features/roadmap/components/TimelineStepItem.tsx
```

## Next Steps
1. feature 브랜치 생성 (`feature/unified-doc-viewer` 등)
2. 코드 변경 + docs 커밋
3. PR 생성 → develop
4. 머지 후 이 디렉토리를 `docs/dev/done/unified-doc-viewer/`로 아카이브
5. `docs/planning/REPORT-unified-document-viewer.md` → `docs/planning/completed/`로 이동

## Dependencies

- marked.js CDN (`cdn.jsdelivr.net`) — MD 뷰어 클라이언트 렌더링
- 기존 ActionKitFile DB 레코드 — `_resolve_file()` 의존
