# CONTEXT: 목업 데이터 및 하드코딩 제거

## 발견 경위
2026-03-06 프로젝트 전수조사를 통해 발견. 백엔드/프론트엔드/인프라 3개 영역을 병렬 탐색하여 13건의 이슈를 식별함.

## 핵심 파일 맵

### Phase A (보안)
| 파일 | 수정 내용 |
|------|-----------|
| `app-backend/app/core/config.py` | `ADMIN_EMAILS` 추가, `validate_security()` 강화 |
| `app-backend/app/repositories/user_repository.py:22` | 하드코딩 이메일 → `settings.admin_email_set` |
| `app-backend/app/api/v1/auth/router.py:172-174` | mock fallback에 ENVIRONMENT 이중 검증 |

### Phase B (가짜 데이터)
| 파일 | 수정 내용 |
|------|-----------|
| `app-frontend/src/features/ops/actionkit/components/stats-dashboard.tsx` | POPULAR_DOCS/SEARCH_KEYWORDS 제거, summary 활용 |
| `app-backend/app/features/ops/application/growth_club/service.py` | stub → 실제 DB 쿼리 |
| `app-frontend/src/features/roadmap/components/roadmap-constants.ts:55-63` | 가짜 통계 수치 제거 |

### Phase C (프론트엔드)
| 파일 | 수정 내용 |
|------|-----------|
| `app-frontend/src/lib/env.ts` | 신규 — API URL 유틸리티 |
| `app-frontend/src/lib/api-client.ts:11` | env.ts import |
| `app-frontend/src/features/chat/utils/sse.ts:15` | env.ts import |
| `app-frontend/src/features/shared/file/utils/url.ts:16` | env.ts import |
| `app-frontend/src/features/actionkit/components/ActionKitLibraryView.tsx:173` | env.ts import |
| `app-frontend/src/features/dashboard/components/Sidebar.tsx:80` | DiceBear 제거 |

### Phase D (코드 품질)
| 파일 | 수정 내용 |
|------|-----------|
| `app-backend/app/api/v1/ops/growth_club.py:155,259` | `datetime.now()` → `utc_now()` |
| `app-backend/app/models/audit_log.py:18` | `datetime.now()` → `utc_now` |
| `app-backend/alembic.ini:4` | DB URL placeholder |
| `app-backend/app/core/config.py:17` | CORS 5173 제거 |
| `app-frontend/src/features/dashboard/components/ColdStartHero.tsx:8` | 중복 상수 제거 |

## 의존 관계
- A-1, A-2는 독립적으로 실행 가능
- B-2는 Growth Club 모델의 `report_count`, `is_blinded` 필드 확인 필요
- C-1은 기존 테스트에 영향 (import 경로 변경)
- D-1 ~ D-4는 모두 독립적

## 주의사항
- `user_repository.py` 수정 시 기존 Google OAuth 로그인 플로우 반드시 수동 테스트
- `stats-dashboard.tsx`는 가짜 데이터를 제거하면 빈 화면이 되므로, 대체 UI 필수
- `alembic.ini` 수정 후 `alembic upgrade head` 정상 동작 확인 필요
