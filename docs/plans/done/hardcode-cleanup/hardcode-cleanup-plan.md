# PLAN: 목업 데이터 및 하드코딩 제거 — 종합 개선 방안

> 작성일: 2026-03-06
> 상태: draft
> 범위: 백엔드 + 프론트엔드 전수조사 기반

---

## 1. 현황 요약

전수조사 결과 **13건**의 목업/하드코딩 이슈를 발견했으며, 이 중 4건이 즉시 조치가 필요한 높은 심각도입니다.

| 심각도 | 건수 | 핵심 항목 |
|--------|------|-----------|
| 높음 | 4 | 관리자 이메일 하드코딩, Mock 인증 시스템, 가짜 통계 대시보드, Growth Club stub |
| 중간 | 6 | alembic.ini DB URL, localhost fallback(4곳), DiceBear 외부 의존, datetime 타임존, CORS 잔여, Placeholder 페이지 |
| 낮음 | 3 | 가짜 인사이트 숫자, 추천칩 중복, .env 기본값 |

---

## 2. Phase 구성

### Phase A — 보안 및 인증 정비 (P0)
### Phase B — 가짜 데이터 제거 및 API 연동 (P0~P1)
### Phase C — 프론트엔드 설정 정리 (P2)
### Phase D — 코드 품질 개선 (P3)

---

## 3. Phase A — 보안 및 인증 정비

### A-1. 관리자 이메일 하드코딩 제거

**현재 문제:**
```python
# app-backend/app/repositories/user_repository.py:22
is_superuser = email == "dojyu1928@gmail.com"
```
- 특정 개인 이메일이 소스코드에 직접 기재되어 git 이력에 영구 잔존
- 관리자 추가/변경 시 코드 수정+배포가 필요
- 이 이메일 계정이 탈취되면 전체 시스템 superuser 권한 획득 가능

**개선 방안:**

(1) `config.py`에 환경변수 추가:
```python
# app/core/config.py — Settings 클래스에 추가
ADMIN_EMAILS: str = ""  # 쉼표 구분. 예: "admin1@company.com,admin2@company.com"

@property
def admin_email_set(self) -> set[str]:
    return {e.strip().lower() for e in self.ADMIN_EMAILS.split(",") if e.strip()}
```

(2) `user_repository.py` 수정:
```python
# app/repositories/user_repository.py
from app.core.config import get_settings

async def create_google_user(self, email: str, full_name: str, hashed_password: str) -> User:
    settings = get_settings()
    is_superuser = email.lower() in settings.admin_email_set
    user = User(email=email, full_name=full_name, hashed_password=hashed_password, is_superuser=is_superuser)
    ...
```

(3) `.env`, `.env.example` 업데이트:
```env
# Admin emails (comma-separated)
ADMIN_EMAILS=
```

**수정 대상 파일:**
- `app-backend/app/core/config.py` — `ADMIN_EMAILS` 필드 + `admin_email_set` 프로퍼티
- `app-backend/app/repositories/user_repository.py` — `create_google_user()` 메서드
- `app-backend/.env` / `.env.example` — 새 환경변수
- `app-backend/.env.local` — 실제 관리자 이메일 설정

**테스트:**
- `tests/` 내 user_repository 관련 기존 테스트 업데이트
- `ADMIN_EMAILS` 빈 문자열일 때 superuser 없음 확인
- 쉼표 구분 다수 이메일 정상 파싱 확인

---

### A-2. 소셜 Mock 인증 프로덕션 차단

**현재 문제:**
```python
# app-backend/app/api/v1/auth/router.py:55-107
async def _login_social_mock_user(provider, session):
    email = f"social_{provider}_user@example.com"
    hashed_password = security.get_password_hash("SOCIAL_AUTH_MOCK")
    ...
```
- `ENABLE_SOCIAL_MOCK=true` 시 비밀번호 "SOCIAL_AUTH_MOCK"으로 누구나 로그인 가능
- Google 인증 실패 시 자동 fallback (`:173-174`)
- 별도 `/login/social/{provider}` mock 엔드포인트 존재

**개선 방안:**

(1) `config.py`의 `validate_security()`에 프로덕션 차단 추가:
```python
# app/core/config.py — validate_security() 내
@model_validator(mode="after")
def validate_security(self) -> "Settings":
    ...
    if self.ENVIRONMENT.lower() == "production" and self.ENABLE_SOCIAL_MOCK:
        raise ValueError("ENABLE_SOCIAL_MOCK must be false in production")
    return self
```

(2) Google 인증 fallback에서 mock 분기 제거를 검토:
```python
# router.py:172-174 — 현재:
except GoogleAuthError:
    if settings.ENABLE_SOCIAL_MOCK:
        return await _login_social_mock_user("google", session)
    raise HTTPException(...)

# 대안: ENVIRONMENT != "production" 이중 검증 추가
except GoogleAuthError:
    if settings.ENABLE_SOCIAL_MOCK and settings.ENVIRONMENT != "production":
        return await _login_social_mock_user("google", session)
    raise HTTPException(...)
```

(3) mock 엔드포인트의 OpenAPI docs에서 제외:
```python
@router.post("/login/social/{provider}", include_in_schema=False, ...)
```

**수정 대상 파일:**
- `app-backend/app/core/config.py` — `validate_security()` 강화
- `app-backend/app/api/v1/auth/router.py` — mock fallback 이중 검증

**테스트:**
- `ENVIRONMENT=production` + `ENABLE_SOCIAL_MOCK=true` 시 서버 시작 실패 확인
- 기존 mock 로그인 테스트는 `ENVIRONMENT=development`에서만 동작 확인

---

## 4. Phase B — 가짜 데이터 제거 및 API 연동

### B-1. Ops 통계 대시보드 실데이터 연동

**현재 문제:**
```typescript
// app-frontend/src/features/ops/actionkit/components/stats-dashboard.tsx:7-15
const POPULAR_DOCS = [
    { title: "근로계약서 (정규직)", downloads: 1250, saves: 430, trend: "+12%" },
    ...
];
// Lines 95, 109, 123: "4,520건", "1,284명", "42%" — 전부 하드코딩
```

**현황 분석:**
- 백엔드 `/ops/actionkit/summary` API가 이미 존재 → `total_items`, `items_with_files`, `inactive_items`, `total_related_laws`, `total_highlights` 반환
- 하지만 다운로드 수, 활성 유저, 인기 서류 등의 통계 API는 **존재하지 않음**
- 현재 ActionKit에는 다운로드 추적 기능 자체가 없음

**개선 방안 — 2가지 옵션:**

**옵션 1 (권장): "Coming Soon" 상태로 전환**
- 가짜 데이터를 제거하고, 통계 대시보드를 "데이터 수집 중" 상태로 표시
- 기존 `summary` API 데이터(전체 항목, 파일 첨부, 미공개 등)만 활용
- 다운로드/활성유저 카드는 "준비 중" 표시

```typescript
// stats-dashboard.tsx 수정 방향
// POPULAR_DOCS, SEARCH_KEYWORDS 상수 제거
// "총 다운로드 수", "활성 유저", "다운로드율" 카드 → 회색 처리 + "데이터 수집 중" 표시
// 인사이트 패널 → summary 데이터 기반 실제 인사이트로 교체
//   예: "미공개 항목 {inactive_items}건이 있습니다", "파일 미첨부 항목 {total - with_files}건"
```

**옵션 2 (향후): 다운로드 추적 시스템 구축**
- `actionkit_download_logs` 테이블 생성 (user_id, item_id, downloaded_at)
- 파일 다운로드 API에서 로그 기록
- `/ops/actionkit/stats` 집계 API 신규 생성
- 이 옵션은 별도 기획이 필요하므로 현 Phase에서는 옵션 1 적용

**수정 대상 파일:**
- `app-frontend/src/features/ops/actionkit/components/stats-dashboard.tsx` — 가짜 데이터 제거, summary props 활용

---

### B-2. Growth Club 관리 큐 stub 제거

**현재 문제:**
```python
# app-backend/app/features/ops/application/growth_club/service.py:9-11
def get_queue_summary() -> GrowthClubQueueSummary:
    # TODO: connect to moderation queue repository
    return {"pending_posts": 0, "pending_comments": 0}
```

**현황 분석:**
- Growth Club 모델: `GrowthClubPost`에 `is_blinded` 필드가 있음
- 신고 기능은 `report_count` 필드로 추적 중
- "모더레이션 큐"는 `report_count > 0 AND is_blinded = False`인 게시글/댓글

**개선 방안:**
```python
# app/features/ops/application/growth_club/service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select, func
from app.models.growth_club import GrowthClubPost, GrowthClubComment

async def get_queue_summary(session: AsyncSession) -> GrowthClubQueueSummary:
    # 신고접수 + 미처리(블라인드 안 된) 게시글
    post_count = await session.execute(
        select(func.count(GrowthClubPost.id)).where(
            GrowthClubPost.report_count > 0,
            GrowthClubPost.is_blinded.is_(False),
        )
    )
    # 신고접수 + 미처리 댓글
    comment_count = await session.execute(
        select(func.count(GrowthClubComment.id)).where(
            GrowthClubComment.report_count > 0,
            GrowthClubComment.is_blinded.is_(False),
        )
    )
    return {
        "pending_posts": post_count.scalar_one(),
        "pending_comments": comment_count.scalar_one(),
    }
```

**호출부 수정:**
- 이 함수의 호출부(ops home API 등)에서 `session` 파라미터 전달 필요
- 함수 시그니처가 `def → async def`로 변경되므로 호출부도 `await` 추가

**수정 대상 파일:**
- `app-backend/app/features/ops/application/growth_club/service.py` — 실제 쿼리 구현
- 이 함수를 호출하는 곳 (ops home 등) — `await` 및 `session` 전달
- `app-backend/app/models/growth_club.py` 확인 — `report_count`, `is_blinded` 필드 존재 확인

---

### B-3. 가짜 인사이트 숫자 제거

**현재 문제:**
```typescript
// roadmap-constants.ts:56-62
MILESTONE_INSIGHTS: {
    default: [
        "이 단계를 완료한 창업자의 87%가 1주 내 다음 단계도 완료했습니다.",
        "같은 업종 창업자 평균보다 빠른 속도로 진행 중입니다.",
        ...
    ]
}
```
- "87%", "평균보다 빠른 속도" 등 — 근거 없는 통계
- 사용자에게 거짓 정보를 전달하여 신뢰 저하 가능

**개선 방안:**
```typescript
// roadmap-constants.ts — 수정 방향
export const MILESTONE_INSIGHTS: Record<string, string[]> = {
    default: [
        "한 단계씩 차근차근 진행하고 있습니다. 잘하고 계세요!",
        "지금까지의 진행 상황이 인상적입니다. 이 기세를 이어가세요!",
        "창업 준비의 가장 어려운 부분은 '시작'입니다. 이미 해내고 있습니다!",
        "다음 단계도 충분히 해낼 수 있습니다. 화이팅!",
        "꾸준히 진행하는 것이 가장 중요합니다. 훌륭합니다!",
    ],
};
```
- 구체적 통계 수치를 모두 제거하고 동기부여 메시지만 유지
- "87%", "평균보다 빠른" 등 비교 표현 삭제

**수정 대상 파일:**
- `app-frontend/src/features/roadmap/components/roadmap-constants.ts` — `MILESTONE_INSIGHTS` 수정

---

## 5. Phase C — 프론트엔드 설정 정리

### C-1. localhost fallback URL 통합 및 경고

**현재 문제 (4곳):**
| 파일 | 줄 | fallback |
|------|-----|----------|
| `src/lib/api-client.ts` | `:11` | `"http://localhost:8000/api/v1"` |
| `src/features/chat/utils/sse.ts` | `:15` | `"http://localhost:8000/api/v1"` |
| `src/features/shared/file/utils/url.ts` | `:16` | `"http://localhost:8000"` |
| `src/features/actionkit/components/ActionKitLibraryView.tsx` | `:173` | `"http://localhost:8000/api/v1"` |

**개선 방안:**

(1) 공통 유틸리티로 추출:
```typescript
// src/lib/env.ts (신규)
export function getApiBaseUrl(): string {
    const explicit = process.env.NEXT_PUBLIC_API_BASE_URL?.trim();
    const apiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
    const result = explicit
        || (apiUrl ? `${apiUrl.replace(/\/$/, "")}/api/v1` : "http://localhost:8000/api/v1");

    if (process.env.NODE_ENV === "production" && result.includes("localhost")) {
        console.error("[ENV] API URL이 localhost입니다. NEXT_PUBLIC_API_BASE_URL을 설정하세요.");
    }
    return result;
}

export function getApiHost(): string {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
    return apiUrl?.replace(/\/$/, "") || "http://localhost:8000";
}
```

(2) 4곳 모두 이 유틸리티 import로 교체:
- `api-client.ts` → `import { getApiBaseUrl } from "@/lib/env"`
- `sse.ts` → 기존 `getApiBaseUrl()` 함수를 `@/lib/env`에서 가져오도록 변경
- `url.ts` → `import { getApiHost } from "@/lib/env"`
- `ActionKitLibraryView.tsx` → `import { getApiBaseUrl } from "@/lib/env"`

**수정 대상 파일:**
- `app-frontend/src/lib/env.ts` — 신규 생성
- `app-frontend/src/lib/api-client.ts` — import 변경
- `app-frontend/src/features/chat/utils/sse.ts` — import 변경
- `app-frontend/src/features/shared/file/utils/url.ts` — import 변경
- `app-frontend/src/features/actionkit/components/ActionKitLibraryView.tsx` — import 변경

---

### C-2. DiceBear 외부 의존 제거

**현재 문제:**
```tsx
// Sidebar.tsx:80
`https://api.dicebear.com/7.x/avataaars/svg?seed=${user?.username || 'Guest'}`
```
- 외부 API에 런타임 의존 (서비스 다운 시 아바타 깨짐)
- GDPR/개인정보 이슈 (사용자 이름이 외부 서버로 전송)

**개선 방안:**
- `<AvatarFallback>`이 이미 존재하므로, DiceBear URL 대신 fallback만 사용:
```tsx
<AvatarImage
    src={user?.profile_img ? resolveUploadUrl(user.profile_img) : undefined}
/>
<AvatarFallback className="bg-primary/10 text-primary">
    {user?.username?.[0]?.toUpperCase() || 'U'}
</AvatarFallback>
```
- 프로필 이미지가 없으면 이니셜 아바타(AvatarFallback)가 자동 표시됨
- 외부 API 의존 완전 제거

**수정 대상 파일:**
- `app-frontend/src/features/dashboard/components/Sidebar.tsx` — `:80` AvatarImage src 수정

---

### C-3. Placeholder 페이지 정리

**현재 문제:**
- `/settings`, `/billing` — "준비 중인 페이지" 텍스트만 표시
- 사이드바에서 직접 링크는 없지만 URL 직접 접근 가능

**현황 분석:**
- `nav-config.ts`에 settings/billing 메뉴가 **없음** (사이드바에 표시 안 됨)
- URL 직접 접근 시에만 보이는 페이지

**개선 방안:**
- 현재 사이드바에 노출되지 않으므로 **유지해도 무방**
- 다만 "준비 중" 텍스트를 좀 더 명확하게 개선:
```tsx
export default function PlaceholderPage() {
    return (
        <section className="rounded-2xl border border-slate-200 bg-white p-8">
            <h1 className="text-2xl font-bold text-slate-900">준비 중</h1>
            <p className="mt-2 text-sm text-slate-600">
                이 기능은 현재 개발 중입니다. 빠른 시일 내 제공할 예정입니다.
            </p>
        </section>
    );
}
```
- **우선순위 낮음** — 다른 작업 완료 후 처리

**수정 대상 파일:**
- `app-frontend/src/app/(dashboard)/settings/page.tsx`
- `app-frontend/src/app/(dashboard)/billing/page.tsx`

---

## 6. Phase D — 코드 품질 개선

### D-1. datetime.now() 타임존 통일

**현재 문제 (3곳):**
| 파일 | 줄 | 코드 |
|------|-----|------|
| `app/api/v1/ops/growth_club.py` | `:155` | `old_log.created_at = datetime.now()` |
| `app/api/v1/ops/growth_club.py` | `:259` | `old_log.created_at = datetime.now()` |
| `app/models/audit_log.py` | `:18` | `Field(default_factory=lambda: datetime.now())` |

**개선 방안:**
```python
# growth_club.py:155, 259 — 이미 상단에 utc_now 임포트가 있는지 확인 후:
from app.core.security import utc_now
old_log.created_at = utc_now()

# audit_log.py:18
from app.core.security import utc_now
created_at: datetime = Field(default_factory=utc_now)
```

**수정 대상 파일:**
- `app-backend/app/api/v1/ops/growth_club.py` — `:155`, `:259`
- `app-backend/app/models/audit_log.py` — `:18`

---

### D-2. alembic.ini 하드코딩 DB URL 정리

**현재 문제:**
```ini
# alembic.ini:4
sqlalchemy.url = postgresql+asyncpg://stepzero_admin:stepzero_password@localhost:5432/stepzero_db
```
- `alembic/env.py`에서 환경변수로 오버라이드하지만, INI 파일 자체에 자격증명 잔존

**개선 방안:**
```ini
# alembic.ini:4 — placeholder로 교체
sqlalchemy.url = driver://user:pass@localhost/dbname
```
- `alembic/env.py`가 `DATABASE_URL` 환경변수를 사용하므로 INI 값은 실제 사용되지 않음
- 자격증명 노출 방지를 위해 placeholder로 교체

**수정 대상 파일:**
- `app-backend/alembic.ini` — `:4`

---

### D-3. CORS 미사용 포트 제거

**현재 문제:**
```python
# config.py:17
"http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173"
```
- `localhost:5173` (Vite 포트) — 프로젝트가 Next.js를 사용하므로 불필요

**개선 방안:**
```python
BACKEND_CORS_ORIGINS_STR: str = "http://localhost:3000,http://127.0.0.1:3000"
```

**수정 대상 파일:**
- `app-backend/app/core/config.py` — `:17`

---

### D-4. 추천 칩 중복 제거

**현재 문제:**
- `roadmap-constants.ts:6` → `HERO_SUGGESTIONS = ["카페 프랜차이즈", "SaaS 스타트업", ...]`
- `ColdStartHero.tsx:8` → `SUGGESTED_TAGS = ["카페 프랜차이즈", "SaaS 스타트업", ...]`
- 동일한 데이터가 2곳에 중복 정의

**개선 방안:**
```typescript
// ColdStartHero.tsx:8 수정
import { HERO_SUGGESTIONS } from "@/features/roadmap/components/roadmap-constants";
// SUGGESTED_TAGS 상수 제거, HERO_SUGGESTIONS 직접 사용
```

**수정 대상 파일:**
- `app-frontend/src/features/dashboard/components/ColdStartHero.tsx` — import 변경

---

## 7. 구현 순서 및 예상 영향도

| Phase | 태스크 | 수정 파일 수 | 위험도 | 테스트 필요 |
|-------|--------|-------------|--------|------------|
| A-1 | 관리자 이메일 환경변수화 | 4 | 중 | 기존 인증 테스트 + 신규 |
| A-2 | Mock 인증 프로덕션 차단 | 2 | 낮 | config 검증 테스트 |
| B-1 | 통계 대시보드 정리 | 1 | 낮 | 프론트 수동 확인 |
| B-2 | Growth Club stub 구현 | 2~3 | 중 | 신규 서비스 테스트 |
| B-3 | 인사이트 숫자 제거 | 1 | 낮 | 없음 |
| C-1 | URL 유틸리티 통합 | 5 | 낮 | 기존 테스트 통과 확인 |
| C-2 | DiceBear 제거 | 1 | 낮 | 프론트 수동 확인 |
| C-3 | Placeholder 페이지 | 2 | 낮 | 없음 |
| D-1 | datetime 타임존 | 2 | 낮 | 기존 테스트 |
| D-2 | alembic.ini 정리 | 1 | 낮 | alembic 마이그레이션 동작 확인 |
| D-3 | CORS 정리 | 1 | 낮 | 없음 |
| D-4 | 추천칩 중복 제거 | 1 | 낮 | 없음 |

**총 수정 파일: ~23개** (중복 제외 약 18개)

---

## 8. 변경하지 않는 항목 (의도적 유지)

| 항목 | 이유 |
|------|------|
| `.env` 개발 기본값 (`stepzero_password` 등) | `config.py`에 프로덕션 검증 로직 존재 |
| `ENABLE_SOCIAL_MOCK` 플래그 자체 | 개발 환경에서 유용, Phase A-2에서 프로덕션 차단 추가 |
| `OpsAccessPlaceholder` 컴포넌트 | 의도된 접근 제어 UX |
| `HERO_SUGGESTIONS`, `INTAKE_FIELD_SUGGESTIONS` | UX 가이드용 예시 데이터 (정상) |
| `GENERATING_INSIGHTS` | 로딩 중 표시되는 팁 (근거 없는 통계만 아니면 OK) |
| `READINESS_LEVELS` | 비즈니스 로직 상수 (정상) |
| `.env.local` 실제 키 | `.gitignore` 보호됨, 로컬 개발 전용 |

---

## 9. 심층 분석에서 추가 발견된 사항

### 9-1. 프론트엔드 API 타입 불일치 (api.ts ↔ 백엔드)

**파일:** `app-frontend/src/features/ops/actionkit/api.ts:3-6`
```typescript
export interface ActionKitOpsSummary {
    total_items: number;
    pending_reviews: number;  // ← 백엔드에 없는 필드
}
```

**백엔드 실제 반환:**
```python
# total_items, items_with_files, inactive_items, total_related_laws, total_highlights
```

- `pending_reviews`는 백엔드에 존재하지 않음
- `items_with_files`, `inactive_items` 등이 누락됨
- `view.tsx`에서는 올바른 타입을 직접 정의하여 사용 중 (`:42-48`)
- **조치:** `api.ts`의 인터페이스를 백엔드 응답과 일치시키거나, `pnpm types:sync`로 자동 생성 타입 활용

### 9-2. ActionKit 스타터 팩 하드코딩

**파일:** `app-frontend/src/features/actionkit/components/ActionKitLibraryView.tsx:39-64`
```typescript
const STARTER_PACKS = [
    { id: "hire", title: "직원 채용 필수 팩", keywords: ["근로계약서", "취업규칙", "비밀유지"] },
    { id: "office", title: "사무실 계약 팩", keywords: ["임대차", "화재안전", "건축물"] },
    { id: "invest", title: "투자 유치 준비 팩", keywords: ["주주", "정관", "이사회"] },
];
```
- UI 구성 상수로 현재는 문제 없으나, 팩 추가 시 코드 수정 필요
- **향후 고려:** 백엔드 카테고리 API와 연동하여 동적 생성

### 9-3. is_superuser 체크 포인트 전수 목록

`is_superuser`가 직접 체크되는 모든 위치 (환경변수 전환 시 영향 범위):

| 파일 | 방식 | 용도 |
|------|------|------|
| `app/api/v1/ops/router.py:17` | `Depends(require_platform_admin)` | ops 전체 라우터 |
| `app/api/v1/actionkit/files.py:39` | `Depends(require_platform_admin)` | ActionKit 파일 업로드 |
| `app/api/v1/growth_club/comments.py:137` | `current_user.is_superuser` | 댓글 삭제 권한 |
| `app/api/deps.py:211-219` | `require_platform_admin()` 정의 | 의존성 함수 |

- **결론:** `is_superuser` 필드 자체는 변경할 필요 없음. `create_google_user()`의 할당 로직만 수정하면 됨.

### 9-4. Growth Club 큐 API 호출부

**파일:** `app-backend/app/api/v1/ops/growth_club.py:30-37`
```python
@router.get("/queue-summary")
async def get_growth_club_queue_summary() -> dict[str, int]:
    return get_queue_summary()
```
- 현재 `session` 미전달, `sync` 함수 호출
- B-2 태스크에서 `async` 전환 시 이 엔드포인트도 `session` 의존성 추가 필요
