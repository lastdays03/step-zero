# Context: 프로젝트 감사 기반 개선 작업

> **Last Updated:** 2026-03-06

## 근거 문서

- `docs/plans/reports/REPORT-project-audit-2026-03-06.md` — 전수 감사 보고서 (항목 A~J)

## Key Files

### Phase 1 (프론트엔드 빌드 복구)

| 파일 | 역할 | 변경 내용 |
|------|------|-----------|
| `app-frontend/src/lib/env.ts` | API URL source of truth | `getApiBaseUrl` import/re-export 기준점 |
| `app-frontend/src/features/chat/hooks/useChat.ts:7` | SSE 채팅 hook | `getApiBaseUrl` import → `@/lib/env` |
| `app-frontend/src/features/chat/utils/api.ts:6` | 채팅 API 유틸 | `getApiBaseUrl` import → `@/lib/env` |
| `app-frontend/src/features/chat/index.ts:21-26` | Chat public entry | 깨진 `getApiBaseUrl` re-export 정리 |
| `app-frontend/src/features/chat/__tests__/sse.test.ts:1` | Chat SSE 테스트 | `getApiBaseUrl` import 소스 정정 |
| `app-frontend/src/features/chat/utils/sse.ts` | SSE 공통 유틸 | 변경 불필요 (이미 `@/lib/env` import) |
| `app-frontend/src/features/notifications/api/index.ts` | 알림 API (정본) | 유지 |
| `app-frontend/src/features/notifications/api/notifications.ts` | 알림 API (중복) | 삭제 후 참조 통합 |
| `app-frontend/src/features/notifications/hooks/useNotifications.ts` | 알림 hook | `notifications.ts` 의존 → `index.ts` 기준으로 통합 |

### Phase 2 (인증 안정화)

| 파일 | 역할 | 변경 내용 |
|------|------|-----------|
| `app-backend/app/features/auth/application/auth_service.py:86-114` | refresh token rotation | 중복 create 제거 |
| `app-backend/app/features/auth/application/auth_service.py:204-229` | `_build_auth_result` | 토큰 저장 로직 확인 |
| `app-backend/app/repositories/refresh_token_repository.py` | 토큰 CRUD | `token_hash` UNIQUE 검토 |
| `app-backend/app/models/refresh_token.py` | 토큰 모델 | UNIQUE 제약 추가 검토 |
| `app-frontend/src/features/auth/components/SocialAuthModal.tsx` | Google 로그인 모달 | Client ID 없을 때 fallback |
| `app-frontend/src/app/layout.tsx:22-49` | Root Layout | GoogleOAuthProvider 조건부 렌더링 확인 |

### Phase 3 (운영 UX)

| 파일 | 역할 | 변경 내용 |
|------|------|-----------|
| `app-frontend/src/features/ops/files/view.tsx:189-219` | Ops 파일 관리 | confirm/alert → Dialog |
| `app-frontend/src/features/ops/actionkit/{view.tsx,components/category-edit-modal.tsx}` | Ops 액션킷 | confirm → Dialog |
| `app-frontend/src/features/ops/announcements/view.tsx:170-177` | Ops 공지 | confirm → Dialog |
| `app-frontend/src/features/ops/roadmap-templates/**/*` | 템플릿 편집 UI | confirm → Dialog |
| `app-frontend/src/features/ops/growth-club/view.tsx` | Growth Club 운영 UI | confirm → Dialog |
| `app-frontend/src/features/ops/users/view.tsx:314` | Ops 유저 관리 | placeholder alert 제거 |
| `app-backend/app/api/deps.py:104-117` | 팀 의존성 | scalar_one_or_none → first |

### Phase 4 (CI/문서)

| 파일 | 역할 | 변경 내용 |
|------|------|-----------|
| `.github/workflows/ci.yml:157-176` | CI 파이프라인 | test + build 단계 추가 |
| `docs/context/decisions.md:8` | 결정 문서 | v2 → v1 정정 |
| `app-backend/app/features/roadmaps/application/roadmap_generation_service.py:207-217` | 템플릿 해석 | except 범위 축소 |

## Dependencies

```
Phase 1 (빌드 복구) ← 선행 필수
  ↓
Phase 2 (인증)  ← Phase 1과 독립 가능하나, 동일 PR로 묶으면 효율적
  ↓
Phase 3 (UX)   ← Phase 1 완료 후 (build 통과 필요)
  ↓
Phase 4 (CI)   ← Phase 1 완료 후 (test/build 통과해야 CI 추가 의미 있음)
```

## Decisions

- refresh token 중복 저장: Option A (build_auth_result 저장 유지, refresh_access_token의 중복 create 삭제) 추천
- notifications API: `index.ts` 기준으로 통합 (백엔드 HTTP method와 일치)
- 검증 명령은 루트가 아니라 각 앱 디렉터리 기준으로 실행 (`cd app-frontend && pnpm ...`, `cd app-backend && uv run pytest -q`)
- Phase별 PR 전략: Phase 1+2를 하나의 PR, Phase 3+4를 별도 PR 추천
