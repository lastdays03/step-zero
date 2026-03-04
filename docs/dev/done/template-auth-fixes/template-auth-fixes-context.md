# 템플릿 버그 수정 + 인증 시스템 개선 — 컨텍스트

> Last Updated: 2026-03-02

---

## 1. 핵심 변경 파일

### 1.1 Backend

| 파일 | 변경 내용 | 라인 |
|------|----------|------|
| `app/features/ops/application/roadmap_templates/service.py` | `step_order` None 버그 수정: `data.get("step_order", next_order)` → `data.get("step_order") or next_order` | 309 |
| `app/api/v1/ops/roadmap_templates.py` | reorder 엔드포인트를 `{step_id}` 라우트 위로 이동 (422 해결), 응답에 `_serialize_step` 적용 | 280-334 |

### 1.2 Frontend

| 파일 | 변경 내용 |
|------|----------|
| `src/features/ops/roadmap-templates/template-detail-view.tsx` | `@hello-pangea/dnd` DragDropContext/Droppable/Draggable 추가, `handleDragEnd` 핸들러 (optimistic update + reorderTemplateSteps API), `reorderTemplateSteps` import 추가 |
| `src/features/ops/roadmap-templates/components/template-step-editor.tsx` | `dragHandleProps` prop 추가, GripVertical 드래그 핸들 아이콘 |
| `src/lib/api-client.ts` | `suppressAuthEvent` 변수 및 관련 로직 완전 제거, `clearAuthState()`가 항상 `AUTH_STORAGE_EVENT` 발송 |

### 1.3 문서

| 파일 | 내용 |
|------|------|
| `docs/research/auth-security-audit-report.md` | 인증 시스템 보안 감사 + UX 검토 종합 보고서 |

---

## 2. 핵심 기술 결정

### D1: `step_order` None 처리 방식

**결정:** `data.get("step_order") or next_order`
**대안:** `data.get("step_order") if data.get("step_order") is not None else next_order`
**사유:** `step_order`가 0인 경우는 없음 (1부터 시작), `or` 연산자로 충분

### D2: FastAPI 라우트 순서

**결정:** `/steps/reorder` (리터럴)를 `/steps/{step_id}` (파라미터)보다 먼저 등록
**사유:** FastAPI/Starlette는 등록 순서대로 매칭. `{step_id: int}`가 먼저 오면 "reorder" 문자열을 int로 파싱 시도 → 422

### D3: suppressAuthEvent 제거

**결정:** `suppressAuthEvent` 변수 및 조건부 이벤트 발송 로직 완전 제거
**사유:**
1. 무한루프 방지는 기존 3중 가드로 충분
2. `clearAuthState()` → token 삭제 → 이후 401에서 `!localStorage.getItem("token")` → 즉시 reject
3. `suppressAuthEvent`가 오히려 UI 미갱신 버그의 원인

### D4: DnD 구현 패턴

**결정:** `@hello-pangea/dnd` 사용, 기존 actionkit/view.tsx 패턴 답습
**구현:**
- `DragDropContext` → `Droppable` → `Draggable` 3계층
- `dragHandleProps`를 TemplateStepEditor에 전달 (GripVertical 아이콘)
- Optimistic update → API 호출 → load() 새로고침
- editable 모드에서만 DnD 활성화, 비편집 시 일반 렌더링

---

## 3. 의존성 관계

```
B1 (step_order fix) ← 독립
B2 (DnD UI) ← B3 (route fix) — DnD UI가 reorder API를 호출하므로 route fix 필수
B3 (route fix) ← 독립
B4 (auth fix) ← 독립

Phase B (UX 개선) ← B4 완료 후
Phase C (보안 강화) ← 독립
Phase D (고도화) ← Phase B, C 일부 완료 후
Phase E (장기) ← Phase D 완료 후
```

---

## 4. 인증 시스템 참조 파일

| 용도 | 파일 경로 |
|------|----------|
| JWT 설정 | `app-backend/app/core/config.py` (ACCESS_TOKEN_EXPIRE_MINUTES=30, REFRESH_TOKEN_EXPIRE_DAYS=7) |
| 토큰 생성 | `app-backend/app/core/security.py` (HS256, SHA-256 hash) |
| 리프레시 엔드포인트 | `app-backend/app/api/v1/auth/router.py:230-257` |
| AuthService | `app-backend/app/features/auth/application/auth_service.py` (로테이션, 재사용 감지) |
| RefreshToken 모델 | `app-backend/app/models/refresh_token.py` (id, user_id, token_hash, expires_at, revoked, replaced_by) |
| Refresh Token Repository | `app-backend/app/repositories/refresh_token_repository.py` |
| JWT 검증 | `app-backend/app/api/deps.py:23-72` (get_current_user, algorithms=[...]) |
| CORS 미들웨어 | `app-backend/app/main.py:57-64` |
| Axios Silent Refresh | `app-frontend/src/lib/api-client.ts:65-142` |
| AuthProvider | `app-frontend/src/providers/AuthProvider.tsx` |
| .env CORS 설정 | `app-backend/.env` → BACKEND_CORS_ORIGINS_STR |

---

## 5. 테스트 전략

### 5.1 이번 수정 검증 완료

| 테스트 | 결과 |
|--------|------|
| `pytest tests/services/test_template_resolver.py` | 11 passed |
| `pytest` (전체) | 179 passed, 19 skipped |
| `eslint template-detail-view.tsx template-step-editor.tsx` | 0 errors |
| `eslint api-client.ts` | 0 errors |

### 5.2 후속 과제 테스트 계획

| Phase | 테스트 |
|-------|--------|
| B (UX 개선) | 수동 E2E: 30분 방치 후 복귀, 네트워크 차단 후 복구, 다중탭 동기화 |
| C (보안 강화) | Rate limit: 연속 6회 로그인 시 429 확인, refresh 11회 시 429 확인 |
| D (고도화) | Proactive refresh: access token 만료 5분 전 갱신 확인 |
