# CONTEXT: 목업 데이터 및 하드코딩 제거

## Last Updated: 2026-03-06

## 상태: 전체 완료 (아카이브 대기)

Phase A~D 전량 구현 완료. 커밋: `db4857e` on `feature/0-hardcode-cleanup`.
테스트: Backend 421 passed, Frontend lint 0 errors.
PR 생성 후 `done/`으로 아카이브 예정.

## 핵심 파일 맵

### Phase A (보안) — 완료
| 파일 | 수정 내용 |
|------|-----------|
| `app-backend/app/core/config.py` | `ADMIN_EMAILS` 추가, `validate_security()` SOCIAL_MOCK 차단, CORS 5173 제거 |
| `app-backend/app/repositories/user_repository.py:23` | `settings.admin_email_set` 조회 |
| `app-backend/app/api/v1/auth/router.py:173` | ENVIRONMENT 이중 검증 |

### Phase B (가짜 데이터) — 완료
| 파일 | 수정 내용 |
|------|-----------|
| `app-frontend/src/features/ops/actionkit/components/stats-dashboard.tsx` | 전면 재작성 — summary 기반 |
| `app-frontend/src/features/ops/actionkit/api.ts` | 타입 백엔드 일치 |
| `app-backend/app/features/ops/application/growth_club/service.py` | 실제 DB 쿼리 |
| `app-frontend/src/features/roadmap/components/roadmap-constants.ts` | 가짜 수치 제거 |

### Phase C (프론트엔드) — 완료
| 파일 | 수정 내용 |
|------|-----------|
| `app-frontend/src/lib/env.ts` | **신규** — `getApiBaseUrl`, `getApiHost` |
| `api-client.ts`, `sse.ts`, `url.ts`, `ActionKitLibraryView.tsx` | env.ts import |
| `Sidebar.tsx` | DiceBear 제거 |

### Phase D (코드 품질) — 완료
| 파일 | 수정 내용 |
|------|-----------|
| `growth_club.py:155,259` + `audit_log.py:18` | `utc_now()` |
| `alembic.ini:4` | DB URL placeholder |
| `ColdStartHero.tsx:8` | HERO_SUGGESTIONS import |

## 배포 주의사항
- 프로덕션 `.env`에 `ADMIN_EMAILS` 반드시 설정
- 기존 DB의 `is_superuser=True` 유저는 영향 없음 (가입 시점에만 적용)
