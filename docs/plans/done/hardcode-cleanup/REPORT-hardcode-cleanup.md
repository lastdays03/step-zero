# 변경 내역 보고서: 목업 데이터 및 하드코딩 제거

> **브랜치:** `feature/0-hardcode-cleanup`
> **커밋:** `db4857e`
> **작업일:** 2026-03-06
> **영향 범위:** Backend 8개 파일, Frontend 10개 파일, 문서 3개 파일 (신규 1개)
> **테스트 결과:** Backend 421 passed / Frontend lint 0 errors

---

## 1. 요약

프로젝트 전수조사를 통해 발견된 **13건의 목업 데이터·하드코딩 이슈**를 4개 Phase로 나누어 전량 수정 완료하였다. 보안 취약점(하드코딩 관리자 이메일, 프로덕션 Mock 인증 미차단), 가짜 통계 데이터, 분산된 localhost fallback URL, 타임존 미지정 등의 문제를 해소하였다.

---

## 2. Phase A — 보안 및 인증 정비

### A-1. 하드코딩 관리자 이메일 제거

**문제:**
Google OAuth 가입 시 관리자 권한 부여 로직에 개인 이메일이 소스코드에 하드코딩되어 있었다.

```python
# 수정 전 — user_repository.py:22
is_superuser = email == "dojyu1928@gmail.com"
```

**수정 내용:**

| 파일 | 변경 |
|------|------|
| `app/core/config.py:46-55` | `ADMIN_EMAILS: str` 필드 + `admin_email_set` 프로퍼티 추가 |
| `app/repositories/user_repository.py:23` | `get_settings().admin_email_set` 조회로 변경 |
| `.env` | `ADMIN_EMAILS=dojyu1928@gmail.com` 추가 |
| `.env.example` | `ADMIN_EMAILS=` 추가 (빈 값 + 설명 주석) |

**수정 후 동작:**
```python
# config.py — 쉼표 구분 환경변수를 FrozenSet으로 변환
ADMIN_EMAILS: str = ""

@property
def admin_email_set(self) -> FrozenSet[str]:
    return frozenset(
        e.strip().lower()
        for e in self.ADMIN_EMAILS.split(",")
        if e.strip()
    )

# user_repository.py — 환경변수 기반 동적 조회
is_superuser = email.lower() in get_settings().admin_email_set
```

**설계 결정:**
- `FrozenSet`으로 반환하여 불변성 보장 + O(1) lookup 성능
- `.lower()` 정규화로 대소문자 무시 비교
- 환경변수가 비어있으면 빈 set → 어떤 이메일도 superuser가 되지 않음

---

### A-2. Mock 인증 프로덕션 차단 이중 안전장치

**문제:**
`ENABLE_SOCIAL_MOCK=true` 설정이 프로덕션에서도 동작할 수 있었다. Mock 인증은 임의 사용자를 고정 비밀번호(`"SOCIAL_AUTH_MOCK"`)로 생성하므로 프로덕션 노출 시 심각한 보안 취약점이 된다.

**수정 내용:**

| 파일 | 변경 |
|------|------|
| `app/core/config.py:112-115` | `validate_security()`에 프로덕션 환경 `ENABLE_SOCIAL_MOCK` 차단 추가 |
| `app/api/v1/auth/router.py:173` | Google 인증 fallback에 `ENVIRONMENT != production` 이중 검증 |

**수정 후 동작:**
```python
# config.py — 앱 시작 시 자동 검증
if self.ENVIRONMENT.lower() == "production":
    if self.ENABLE_SOCIAL_MOCK:
        raise ValueError("ENABLE_SOCIAL_MOCK must be disabled in production")

# router.py — 런타임 이중 검증
except GoogleAuthError:
    if settings.ENABLE_SOCIAL_MOCK and settings.ENVIRONMENT.lower() != "production":
        return await _login_social_mock_user("google", session)
```

**방어 레이어:**
1. **앱 기동 시점:** `validate_security()` model validator에서 `ValueError` 발생 → 서버 시작 차단
2. **런타임:** Google 인증 실패 fallback에서 `ENVIRONMENT` 추가 확인 → 설정 누락 시에도 이중 방어

---

## 3. Phase B — 가짜 데이터 제거

### B-1. ActionKit 통계 대시보드 전면 교체

**문제:**
운영자 콘솔의 액션 키트 통계 대시보드가 완전히 가짜 데이터로 구성되어 있었다.

| 가짜 데이터 | 위치 |
|-------------|------|
| `POPULAR_DOCS` (5개 서류 + 다운로드/찜/트렌드 수치) | 상수 선언 |
| `SEARCH_KEYWORDS` (6개 고정 검색어) | 상수 선언 |
| "4,520건" 다운로드 / "1,284명" 활성 유저 / "42%" 다운로드율 | KPI 카드 |
| "주주간계약서 24% 급증" 인사이트 텍스트 | 인사이트 패널 |

**수정 전:** 204줄 (가짜 데이터 + 가짜 UI 컴포넌트 전체)
**수정 후:** 105줄 (실데이터 기반 UI)

**수정 내용:**

| 파일 | 변경 |
|------|------|
| `stats-dashboard.tsx` | 전면 재작성 — summary API 데이터 기반 5개 카드 |
| `view.tsx:249` | `summary` prop 전달 추가 |
| `api.ts:3-6` | 타입 정의를 백엔드 응답과 일치시킴 |

**수정 전 API 타입 불일치:**
```typescript
// 수정 전 — 백엔드에 없는 필드
export interface ActionKitOpsSummary {
    total_items: number;
    pending_reviews: number;  // ← 백엔드에 존재하지 않음
}

// 수정 후 — 백엔드 응답과 정확히 일치
export interface ActionKitOpsSummary {
    total_items: number;
    items_with_files: number;
    inactive_items: number;
    total_related_laws: number;
    total_highlights: number;
}
```

**수정 후 대시보드 구성:**
- 기존 `view.tsx`에서 이미 fetch하고 있던 `summary` 데이터를 props로 전달
- 5개 실데이터 카드: 전체 항목 / 파일 첨부 / 미공개 / 관련 법령 / 하이라이트
- summary가 null일 때 "데이터를 불러오는 중..." 로딩 표시
- 노후 서류 경고 배너는 유지 (실데이터 기반이므로)

**제거된 가짜 요소:**
- 시간대별 필터 UI (week/month/year) — 데이터 없이 UI만 존재
- 인기 다운로드 서류 TOP 5 랭킹 — 완전한 가짜 데이터
- 실시간 검색어 패널 — 고정 상수값
- 인사이트 텍스트 — 근거 없는 수치 포함

---

### B-2. Growth Club 모더레이션 큐 실제 DB 쿼리 구현

**문제:**
운영자 콘솔에서 "신고 대기 게시글/댓글" 건수를 조회하는 API가 항상 0을 반환하는 stub 함수였다.

```python
# 수정 전 — 하드코딩 0 반환
def get_queue_summary() -> GrowthClubQueueSummary:
    # TODO: connect to moderation queue repository
    return {"pending_posts": 0, "pending_comments": 0}
```

**수정 내용:**

| 파일 | 변경 |
|------|------|
| `growth_club/service.py` | 전면 재작성 — 실제 DB 쿼리 |
| `ops/growth_club.py:36-39` | session 의존성 주입 + await 추가 |

**수정 후 동작:**
```python
async def get_queue_summary(session: AsyncSession) -> GrowthClubQueueSummary:
    post_stmt = select(func.count()).where(
        GrowthClubPost.report_count > 0,
        GrowthClubPost.is_blinded.is_(False),
    )
    comment_stmt = select(func.count()).where(
        GrowthClubComment.report_count > 0,
        GrowthClubComment.is_blinded.is_(False),
    )
    # ... 실제 count 반환
```

**쿼리 로직:**
- `report_count > 0`: 1건 이상 신고된 콘텐츠
- `is_blinded = False`: 아직 블라인드 처리되지 않은 콘텐츠
- → **운영자가 검토해야 할 대기 건수**를 정확히 반환

**호출부 변경:**
```python
# 수정 전
async def get_growth_club_queue_summary() -> dict[str, int]:
    return get_queue_summary()

# 수정 후
async def get_growth_club_queue_summary(
    session: AsyncSession = Depends(get_session),
) -> dict[str, int]:
    return await get_queue_summary(session)
```

---

### B-3. 로드맵 가짜 통계 수치 제거

**문제:**
마일스톤 완료 시 표시되는 동기부여 메시지에 근거 없는 통계 수치가 포함되어 있었다.

**수정 내용:**

| 수정 전 (가짜 수치) | 수정 후 (일반 메시지) |
|---------------------|---------------------|
| "이 단계를 완료한 창업자의 **87%**가 1주 내 다음 단계도 완료했습니다." | "한 단계를 끝내면 다음 단계가 훨씬 수월해집니다. 계속 진행해보세요!" |
| "같은 업종 창업자 **평균보다 빠른** 속도로 진행 중입니다." | "꾸준히 진행 중이시네요. 이 기세를 이어가세요!" |
| "다음 단계는 보통 **2-3일**이면 충분합니다. 이 기세를 이어가세요!" | "다음 단계도 곧 완료할 수 있습니다. 화이팅!" |

**유지된 메시지 (가짜 수치 없음):**
- "지금까지의 진행 속도라면, 목표보다 빠르게 준비를 마칠 수 있습니다."
- "창업 준비의 가장 어려운 부분은 '시작'입니다. 이미 해내고 있습니다!"

---

## 4. Phase C — 프론트엔드 설정 정리

### C-1. localhost fallback URL 공통 유틸리티 추출

**문제:**
API 서버 URL을 결정하는 동일한 로직이 4개 파일에 분산 중복되어 있었다.

```
동일한 localhost:8000 fallback 패턴이 반복되는 파일:
1. api-client.ts:10-11
2. sse.ts:8-16  (getApiBaseUrl 함수 자체 정의)
3. url.ts:13-17
4. ActionKitLibraryView.tsx:173
```

**수정 내용:**

| 파일 | 변경 |
|------|------|
| `src/lib/env.ts` | **신규 생성** — `getApiBaseUrl()`, `getApiHost()` |
| `src/lib/api-client.ts:1-3` | 자체 URL 로직 제거 → `env.ts` import |
| `src/features/chat/utils/sse.ts:1-3` | 자체 `getApiBaseUrl()` 함수 제거 → `env.ts` import |
| `src/features/shared/file/utils/url.ts:1,13-14` | 자체 URL 로직 제거 → `env.ts` import |
| `ActionKitLibraryView.tsx:5,173` | 환경변수 직접 참조 → `env.ts` import |

**`src/lib/env.ts` (신규):**
```typescript
const explicitBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
const apiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();

export function getApiBaseUrl(): string {
  return (
    explicitBaseUrl ||
    (apiUrl ? `${apiUrl.replace(/\/$/, "")}/api/v1` : "http://localhost:8000/api/v1")
  );
}

export function getApiHost(): string {
  return (
    apiUrl?.replace(/\/$/, "") ||
    explicitBaseUrl?.replace(/\/api\/v1\/?$/, "") ||
    "http://localhost:8000"
  );
}
```

**설계 결정:**
- 모듈 레벨에서 환경변수를 1회 읽어 캐싱 → 함수 호출마다 읽지 않음
- `getApiBaseUrl()`: API 엔드포인트 기본 URL (e.g., `http://…/api/v1`)
- `getApiHost()`: API 호스트만 (e.g., `http://…:8000`) — 파일 업로드 URL 구성용
- `localhost:8000` fallback은 개발 환경 편의를 위해 유지 (환경변수 미설정 시)

---

### C-2. DiceBear 외부 URL 제거

**문제:**
사이드바 아바타에서 프로필 이미지가 없을 때 DiceBear 외부 API를 호출하고 있었다.

```tsx
// 수정 전
<AvatarImage src={user?.profile_img
  ? resolveUploadUrl(user.profile_img)
  : `https://api.dicebear.com/7.x/avataaars/svg?seed=${user?.username || 'Guest'}`}
/>
<AvatarFallback>...</AvatarFallback>

// 수정 후
<AvatarImage src={user?.profile_img ? resolveUploadUrl(user.profile_img) : undefined} />
<AvatarFallback>...</AvatarFallback>
```

**개선 효과:**
- 외부 서비스 의존성 제거 (DiceBear API 장애 시 아바타 깨짐 방지)
- 불필요한 외부 네트워크 요청 제거
- 이미 존재하는 `<AvatarFallback>`이 사용자 이니셜(`U`)을 표시하므로 UX 변화 없음

---

## 5. Phase D — 코드 품질

### D-1. `datetime.now()` → `utc_now()` (3곳)

**문제:**
`datetime.now()`는 서버 로컬 타임존을 사용하므로 타임존 불일치 위험이 있었다. 프로젝트의 다른 모든 곳은 이미 `utc_now()`를 사용 중이었다.

| 파일 | 위치 | 용도 |
|------|------|------|
| `ops/growth_club.py:157` | 게시글 블라인드 해제 감사 로그 timestamp | `utc_now()` |
| `ops/growth_club.py:261` | 댓글 블라인드 해제 감사 로그 timestamp | `utc_now()` |
| `models/audit_log.py:18` | AuditLog 모델 `default_factory` | `utc_now` |

---

### D-2. `alembic.ini` DB 자격증명 제거

**문제:**
Git에 추적되는 `alembic.ini`에 DB 사용자명과 비밀번호가 하드코딩되어 있었다.

```ini
# 수정 전
sqlalchemy.url = postgresql+asyncpg://stepzero_admin:stepzero_password@localhost:5432/stepzero_db

# 수정 후
sqlalchemy.url = driver://user:pass@localhost/dbname
```

**영향 없음:** `alembic/env.py:47`에서 `config.set_main_option("sqlalchemy.url", SYNC_DATABASE_URL)`로 `.env`의 `DATABASE_URL`을 사용하여 override하고 있으므로, `alembic.ini`의 값은 실제로 사용되지 않는다.

---

### D-3. CORS `localhost:5173` 제거

**문제:**
CORS 기본값에 Vite 개발 서버 포트(`5173`)가 포함되어 있었으나, 프로젝트는 Next.js(포트 `3000`)를 사용하며 Vite를 사용하지 않는다.

```python
# 수정 전
BACKEND_CORS_ORIGINS_STR: str = (
    "http://localhost:3000,http://127.0.0.1:3000,"
    "http://localhost:5173,http://127.0.0.1:5173"
)

# 수정 후
BACKEND_CORS_ORIGINS_STR: str = "http://localhost:3000,http://127.0.0.1:3000"
```

**참고:** 프로덕션 `.env`에서는 `BACKEND_CORS_ORIGINS_STR`이 실제 도메인으로 override되므로, 이 기본값은 로컬 개발에서만 사용된다.

---

### D-4. `ColdStartHero.tsx` 중복 상수 제거

**문제:**
대시보드 ColdStartHero 컴포넌트에 로컬 `SUGGESTED_TAGS` 상수가 선언되어 있었으나, 동일한 목적의 `HERO_SUGGESTIONS` 상수가 이미 `roadmap-constants.ts`에 존재했다.

```typescript
// 수정 전 — ColdStartHero.tsx 내부 선언
const SUGGESTED_TAGS = ["카페 프랜차이즈", "SaaS 스타트업", "온라인 쇼핑몰", "샐러드 전문점"];

// 수정 후 — roadmap-constants.ts에서 import
import { HERO_SUGGESTIONS } from "@/features/roadmap/components/roadmap-constants";
// HERO_SUGGESTIONS = ["카페 프랜차이즈", "SaaS 스타트업", "온라인 의류 쇼핑몰", "샐러드 배달 전문점"]
```

**참고:** 값이 약간 다름 (`"온라인 쇼핑몰"` vs `"온라인 의류 쇼핑몰"`). `HERO_SUGGESTIONS`의 더 구체적인 값으로 통일하였다.

---

## 6. 변경 파일 전체 목록

### Backend (8개)

| # | 파일 | Phase | 변경 요약 |
|---|------|-------|-----------|
| 1 | `app/core/config.py` | A-1, A-2, D-3 | ADMIN_EMAILS 추가, SOCIAL_MOCK 프로덕션 차단, CORS 5173 제거 |
| 2 | `app/repositories/user_repository.py` | A-1 | 하드코딩 이메일 → `admin_email_set` 조회 |
| 3 | `app/api/v1/auth/router.py` | A-2 | Google fallback ENVIRONMENT 이중 검증 |
| 4 | `app/features/ops/application/growth_club/service.py` | B-2 | stub → 실제 DB 쿼리 |
| 5 | `app/api/v1/ops/growth_club.py` | B-2, D-1 | session 주입 + datetime.now() → utc_now() |
| 6 | `app/models/audit_log.py` | D-1 | default_factory datetime.now() → utc_now |
| 7 | `alembic.ini` | D-2 | DB 자격증명 제거 |
| 8 | `.env.example` | A-1 | ADMIN_EMAILS 항목 추가 |

### Frontend (10개)

| # | 파일 | Phase | 변경 요약 |
|---|------|-------|-----------|
| 9 | `src/lib/env.ts` | C-1 | **신규** — API URL 공통 유틸리티 |
| 10 | `src/lib/api-client.ts` | C-1 | env.ts import로 교체 |
| 11 | `src/features/chat/utils/sse.ts` | C-1 | 자체 getApiBaseUrl 제거, env.ts import |
| 12 | `src/features/shared/file/utils/url.ts` | C-1 | env.ts import로 교체 |
| 13 | `src/features/actionkit/components/ActionKitLibraryView.tsx` | C-1 | env.ts import로 교체 |
| 14 | `src/features/ops/actionkit/components/stats-dashboard.tsx` | B-1 | 가짜 데이터 전면 제거, summary 기반 재작성 |
| 15 | `src/features/ops/actionkit/view.tsx` | B-1 | summary prop 전달 |
| 16 | `src/features/ops/actionkit/api.ts` | B-1 | 타입 정의 백엔드 일치 |
| 17 | `src/features/roadmap/components/roadmap-constants.ts` | B-3 | 가짜 통계 수치 제거 |
| 18 | `src/features/dashboard/components/ColdStartHero.tsx` | D-4 | 중복 상수 → import |
| 19 | `src/features/dashboard/components/Sidebar.tsx` | C-2 | DiceBear 외부 URL 제거 |

### 문서 (3개)

| # | 파일 | 내용 |
|---|------|------|
| 20 | `docs/plans/active/hardcode-cleanup/hardcode-cleanup-plan.md` | 상세 개선 계획서 |
| 21 | `docs/plans/active/hardcode-cleanup/hardcode-cleanup-context.md` | 파일 맵 + 의존 관계 |
| 22 | `docs/plans/active/hardcode-cleanup/hardcode-cleanup-tasks.md` | 태스크 체크리스트 (전체 완료) |

---

## 7. 테스트 결과

### Backend
```
421 passed, 10 skipped, 185 warnings in 27.43s
```
- 기존 테스트 전량 통과
- `user_repository.py` 변경이 테스트에 영향 없음 (테스트 환경에서 `ADMIN_EMAILS`는 빈 값)
- `growth_club/service.py` async 전환이 기존 테스트와 충돌 없음

### Frontend
```
✖ 1 problem (0 errors, 1 warning)
  — @next/next/no-img-element (기존 경고, 이번 변경과 무관)
```
- 0 errors
- 유일한 warning은 `ops/files/view.tsx`의 기존 `<img>` 태그 (이번 작업 범위 외)

---

## 8. 위험 요소 및 주의사항

### 배포 시 필수 확인

| 항목 | 조치 |
|------|------|
| `ADMIN_EMAILS` 환경변수 | 프로덕션 `.env`에 관리자 이메일 설정 필요 (미설정 시 신규 가입자에 superuser 부여 안 됨) |
| 기존 superuser | 이미 DB에 `is_superuser=True`로 저장된 사용자는 영향 없음 (가입 시점에만 적용) |
| `alembic.ini` | `alembic/env.py`가 `DATABASE_URL` 환경변수로 override하므로 영향 없음 |

### 기능적 영향

| 영향 | 상세 |
|------|------|
| Ops 통계 대시보드 | 가짜 KPI 카드 제거 → summary 기반 실데이터 카드로 교체. 다운로드 수/활성 유저 등의 지표는 현재 추적하지 않으므로 표시하지 않음 |
| 모더레이션 큐 수치 | 실제 DB 쿼리 결과를 반환하므로, 신고 게시글이 있으면 0이 아닌 실제 건수가 표시됨 |
| 로드맵 동기부여 메시지 | 가짜 통계 수치가 없는 일반적인 응원 메시지로 변경 |
| 아바타 | 프로필 이미지 미설정 사용자는 이니셜 fallback 표시 (SVG 아바타 대신) |
| ColdStartHero 추천 태그 | "온라인 쇼핑몰" → "온라인 의류 쇼핑몰" 등 약간 더 구체적인 텍스트로 통일 |

---

## 9. 후속 과제

이번 작업에서 식별되었으나 범위 외로 분류된 항목:

| 항목 | 설명 | 우선순위 |
|------|------|----------|
| 다운로드/조회 통계 수집 | 액션 키트 다운로드·조회 이벤트 로깅 인프라 구축 | 낮음 |
| `settings/page.tsx`, `billing/page.tsx` | "준비 중인 페이지" placeholder — 기능 미구현 | 낮음 |
| ActionKit 스타터 팩 하드코딩 | 스타터 팩 구성이 코드에 하드코딩 (DB 기반 전환 가능) | 낮음 |
