# 템플릿 버그 수정 + 인증 시스템 개선 계획

> Last Updated: 2026-03-02

---

## 1. Executive Summary

`feature/2-template-system` 브랜치에서 Phase 2+3 (템플릿 관리 시스템) 구현 이후 발견된 **런타임 버그 3건**과 **인증 시스템 구조적 결함 1건**을 수정하고, 보안 감사 결과 도출된 후속 개선 과제를 단계별로 진행하는 계획.

**이번 세션 성과:**
- 템플릿 단계 추가 저장 실패 버그 수정 (backend)
- 템플릿 단계 순서 변경 DnD UI 추가 (frontend)
- FastAPI 라우트 순서 충돌 해결 (backend)
- Silent Refresh 실패 시 UI 미갱신 버그 수정 (frontend)
- 인증 시스템 보안 감사 보고서 작성

---

## 2. Current State Analysis

### 2.1 수정 완료된 버그

| # | 버그 | 원인 | 수정 파일 | 상태 |
|---|------|------|----------|------|
| B1 | 템플릿 단계 추가 시 저장 안됨 | `data.get("step_order", next_order)`에서 None 키 존재 시 default 미적용 | `service.py:309` | **수정됨** |
| B2 | 단계 순서 변경 UI 없음 | 백엔드 API만 존재, 프론트엔드 DnD 미구현 | `template-detail-view.tsx`, `template-step-editor.tsx` | **수정됨** |
| B3 | 순서 변경 API 422 에러 | `/steps/{step_id}` 라우트가 `/steps/reorder`보다 먼저 등록 | `roadmap_templates.py:280-334` | **수정됨** |
| B4 | 세션 만료 후 UI 미갱신 | `suppressAuthEvent`가 AUTH_STORAGE_EVENT 발송 차단 | `api-client.ts:133-140` | **수정됨** |

### 2.2 테스트 현황

| 검증 항목 | 결과 |
|----------|------|
| Backend pytest | 179 passed, 19 skipped, 0 failed |
| Frontend ESLint | 0 errors, 0 warnings |
| 변경 파일 수 | 18 modified + 3 untracked |

### 2.3 보안 감사 결과 (후속 과제)

**보고서:** `docs/planning/completed/REPORT-auth-security-audit.md`

| 심각도 | 건수 | 요약 |
|--------|------|------|
| CRITICAL | 2 | SECRET_KEY 노출, localStorage XSS 취약 |
| HIGH | 4 | Rate limit 없음, 하드코딩 관리자, refresh token 무제한, 삭제완료(H4) |
| MEDIUM | 6 | JWT iss 미검증, jti 부재, DB cleanup, CORS, Google timeout, datetime |

**UX 개선 항목:**

| 심각도 | 건수 | 요약 |
|--------|------|------|
| HIGH | 1 | 세션 만료 시 자동 리디렉션/모달 없음 |
| MEDIUM | 2 | 만료 사전 경고 없음, 네트워크 오류 즉시 로그아웃 |
| LOW | 2 | 에러 메시지 통일성, 폼 데이터 유실 |

---

## 3. Proposed Future State

### 3.1 즉시 (이번 PR에 포함)
- 4건 버그 수정 커밋 + PR 생성
- 보안 감사 보고서 포함

### 3.2 단기 (1-2주, 별도 브랜치)
- 인증 만료 UX 개선 (리디렉션, 재시도, 토스트)
- Rate limiting 적용
- 하드코딩 관리자 이메일 제거

### 3.3 중기 (1개월)
- Proactive token refresh
- Refresh token DB cleanup
- JWT 클레임 강화

### 3.4 장기 (분기)
- HttpOnly 쿠키 전환
- CSP 헤더
- SECRET_KEY 로테이션

---

## 4. Implementation Phases

### Phase A: 이번 세션 완료 작업 커밋 및 PR [즉시]

**목표:** 4건 버그 수정 + 보안 감사 문서를 `feature/2-template-system` → `develop` PR에 포함

| Task | 내용 | Effort | 상태 |
|------|------|--------|------|
| A-1 | 변경사항 git add + commit | S | 대기 |
| A-2 | `develop` 대상 PR 생성 | S | 대기 |

### Phase B: 인증 만료 UX 개선 [단기 1-2주]

**목표:** 세션 만료 시 사용자에게 명확한 안내 제공

| Task | 내용 | Effort | 의존성 |
|------|------|--------|--------|
| B-1 | 글로벌 인증 만료 모달/토스트 컴포넌트 생성 | M | - |
| B-2 | 레이아웃에서 `isLoggedIn === false` 감지 → 리디렉션 또는 모달 표시 | M | B-1 |
| B-3 | 네트워크 오류 시 리프레시 재시도 로직 (2-3회) | M | - |
| B-4 | 리프레시 실패 시 `returnUrl` 저장 → 재로그인 후 복귀 | S | B-2 |

### Phase C: 백엔드 보안 강화 [단기 1-2주]

**목표:** 감사 보고서의 HIGH 이상 항목 해결

| Task | 내용 | Effort | 의존성 |
|------|------|--------|--------|
| C-1 | `/auth/login`, `/auth/refresh` Rate limiting 적용 (slowapi) | M | - |
| C-2 | 하드코딩 관리자 이메일 제거 → DB is_superuser 기반 | S | - |
| C-3 | 로그인 시 기존 refresh token 개수 제한 (최대 5개, FIFO 폐기) | S | - |
| C-4 | SECRET_KEY validator 강화 (dev 키 패턴 차단) | S | - |

### Phase D: 인증 시스템 고도화 [중기 1개월]

**목표:** 감사 보고서의 MEDIUM 항목 해결 + 품질 향상

| Task | 내용 | Effort | 의존성 |
|------|------|--------|--------|
| D-1 | Proactive token refresh (만료 5분 전 사전 갱신) | M | - |
| D-2 | 글로벌 토스트/스낵바 컴포넌트 통합 | M | B-1 |
| D-3 | Refresh token DB cleanup ARQ task | M | - |
| D-4 | JWT `iss` 클레임 검증 추가 | S | - |
| D-5 | `datetime.utcnow()` → `datetime.now(timezone.utc)` 통일 | S | - |
| D-6 | CORS `allow_headers` 명시화 | S | - |

### Phase E: 장기 보안 과제 [분기]

| Task | 내용 | Effort | 의존성 |
|------|------|--------|--------|
| E-1 | HttpOnly + Secure + SameSite 쿠키 전환 | XL | D 전체 |
| E-2 | CSP (Content-Security-Policy) 헤더 적용 | L | - |
| E-3 | SECRET_KEY 로테이션 메커니즘 | L | - |

---

## 5. Risk Assessment

| 위험 | 확률 | 영향 | 완화 |
|------|------|------|------|
| suppressAuthEvent 제거로 무한루프 발생 | **낮음** | 높음 | 3중 가드 검증 완료, 모든 테스트 통과 |
| DnD 라이브러리 SSR 비호환 | **낮음** | 중간 | `"use client"` 지시어 사용, 기존 actionkit에서 검증됨 |
| Rate limiting이 정상 사용자에 영향 | **낮음** | 중간 | 적절한 임계값 설정 (login 5/분, refresh 10/분) |
| 쿠키 전환 시 기존 세션 무효화 | **높음** | 높음 | 마이그레이션 기간 동안 dual-mode 지원 |

---

## 6. Success Metrics

| 지표 | 현재 | 목표 |
|------|------|------|
| 템플릿 단계 추가 성공률 | 0% (버그) | 100% |
| 단계 순서 변경 가능 여부 | 불가능 | DnD + API 연동 |
| 세션 만료 시 UI 갱신 | 미갱신 (버그) | 즉시 갱신 |
| Backend 테스트 통과 | 179/179 | 유지 |
| Frontend lint 에러 | 0 | 유지 |
