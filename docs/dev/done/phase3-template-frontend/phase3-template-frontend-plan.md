# Phase 3: 로드맵 템플릿 관리 — 프론트엔드 구현 계획

> Last Updated: 2026-03-02
> Branch: `feature/2-template-system` (Phase 2와 동일 브랜치에서 진행)
> 의존성: Phase 2 백엔드 완료 필수 (Section A + B)
> 참조: `docs/research/roadmap-improvement/REPORT-implementation-order.md` Phase 3

---

## 1. Executive Summary

운영자가 업종별 로드맵 템플릿을 **검수/승인/관리**할 수 있는 Ops 관리자 UI를 완성한다. 기존에 스캐폴딩된 9개 FE 파일을 기반으로, 누락된 기능을 채우고 UX를 운영 수준으로 끌어올린다.

### 핵심 목표
1. **템플릿 CRUD 완성**: 목록 조회 → 상세 편집 → 상태 워크플로우 전체 동작
2. **역생성 기능**: 기존 로드맵 → 템플릿 자동 생성 UI
3. **액션 편집 완성**: 추가/수정/삭제 + 정렬 UI
4. **운영 품질 UX**: Dialog 기반 확인, 토스트 피드백, 적절한 로딩/에러 처리

### 예상 공수: 3일 (기존 스캐폴딩 재활용)

---

## 2. 현재 상태 분석

### 2.1 이미 구현된 것 (스캐폴딩)

| 파일 | 상태 | 기능 | 완성도 |
|------|:----:|------|:------:|
| `types.ts` | ✅ 완료 | 5개 인터페이스 + 1개 타입 | 100% |
| `api.ts` | ✅ 완료 | 10개 API 함수 (BE 10개 엔드포인트 전부) | 100% |
| `index.ts` | ✅ 완료 | 2개 컴포넌트 export | 100% |
| `view.tsx` | ⚠️ 부분 | 통계카드 + 상태탭 + 테이블 (필터/검색/역생성 없음) | 70% |
| `template-detail-view.tsx` | ⚠️ 부분 | 메타편집 + 상태변경 + 스텝아코디언 (startup_method 편집/Dialog 없음) | 65% |
| `template-list-table.tsx` | ⚠️ 부분 | 테이블 기본구조 (사용횟수/startup_method 컬럼 없음) | 75% |
| `template-status-badge.tsx` | ✅ 완료 | 4개 상태 배지 | 100% |
| `template-step-editor.tsx` | ⚠️ 부분 | 아코디언 + 액션 표시 (빈 섹션에 액션 추가 UI 없음) | 70% |
| `template-action-editor.tsx` | ⚠️ 부분 | 삭제만 구현 (추가/수정 UI 없음) | 40% |
| **라우트 페이지 (2개)** | ✅ 완료 | page.tsx + [templateId]/page.tsx | 100% |
| **Ops 홈 카드** | ✅ 완료 | 7번째 카드 추가됨 | 100% |
| **ops/index.ts** | ✅ 완료 | roadmap-templates export 추가됨 | 100% |

### 2.2 구현 필요 사항 (GAP 분석)

| # | 갭 | 영향 범위 | 중요도 | 공수 |
|---|---|----------|:------:|:----:|
| G1 | 목록 뷰: business_type 필터 드롭다운 | view.tsx | ★★★ | 0.5h |
| G2 | 목록 뷰: "로드맵에서 생성" 버튼 + 다이얼로그 | view.tsx + 신규 컴포넌트 | ★★★★ | 2h |
| G3 | 목록 테이블: startup_method 컬럼 추가 | template-list-table.tsx | ★★ | 0.5h |
| G4 | 상세 뷰: startup_method 편집 필드 | template-detail-view.tsx | ★★ | 0.5h |
| G5 | 상세 뷰: 상태변경 Dialog (prompt→Dialog) | template-detail-view.tsx + 신규 컴포넌트 | ★★★ | 1.5h |
| G6 | 액션 에디터: 추가 UI (인라인 폼) | template-action-editor.tsx | ★★★★ | 2h |
| G7 | 액션 에디터: 수정 UI (인라인 편집) | template-action-editor.tsx | ★★★ | 1.5h |
| G8 | 스텝 에디터: 빈 카테고리에도 액션 추가 가능 | template-step-editor.tsx | ★★★ | 1h |
| G9 | 삭제 확인: confirm→Dialog | view.tsx, template-action-editor.tsx | ★★ | 1h |
| G10 | 로딩/에러 UX 개선 | 전체 | ★★ | 1h |
| G11 | `npm run lint` + `npm run build` 통과 | 전체 | ★★★★★ | 0.5h |
| G12 | 기본 프론트엔드 테스트 | __tests__/ 신규 | ★★ | 1.5h |

**총 예상 공수: ~13.5h (약 2일)**

---

## 3. 구현 설계

### 3.1 디렉토리 구조 (최종)

```
app-frontend/src/features/ops/roadmap-templates/
├── index.ts                           # Public export (변경 없음)
├── view.tsx                           # 목록 뷰 (개선)
├── template-detail-view.tsx           # 상세/편집 뷰 (개선)
├── api.ts                             # API 함수 (변경 없음)
├── types.ts                           # 타입 (변경 없음)
├── components/
│   ├── template-list-table.tsx        # 목록 테이블 (개선)
│   ├── template-status-badge.tsx      # 상태 배지 (변경 없음)
│   ├── template-step-editor.tsx       # 스텝 편집기 (개선)
│   ├── template-action-editor.tsx     # 액션 편집기 (대폭 개선)
│   ├── create-from-roadmap-dialog.tsx # [신규] 로드맵→템플릿 생성 다이얼로그
│   └── status-change-dialog.tsx       # [신규] 상태 변경 확인 다이얼로그
└── __tests__/
    ├── view.test.tsx                  # [신규] 목록 뷰 테스트
    └── template-status-badge.test.tsx # [신규] 상태 배지 테스트
```

### 3.2 주요 기능 설계

#### 3.2.1 목록 뷰 개선 (`view.tsx`)

**추가 기능:**
- `business_type` 필터 드롭다운 — 현재 탭(status 필터)과 별도
- "로드맵에서 템플릿 생성" 버튼 → CreateFromRoadmapDialog 오픈
- 헤더에 필터 UI 추가 (RefreshCw 버튼 옆)

**필터 로직:**
```typescript
const filtered = useMemo(() => {
  let result = templates;
  if (activeTab !== "all") result = result.filter(t => t.status === activeTab);
  if (businessTypeFilter) result = result.filter(t => t.business_type === businessTypeFilter);
  return result;
}, [templates, activeTab, businessTypeFilter]);

// 업종 목록 (중복 제거)
const businessTypes = useMemo(() =>
  [...new Set(templates.map(t => t.business_type))].sort(),
  [templates]
);
```

#### 3.2.2 로드맵 역생성 다이얼로그 (`create-from-roadmap-dialog.tsx`)

**UX 흐름:**
1. "로드맵에서 생성" 버튼 클릭
2. Dialog 오픈: Roadmap UUID 입력 필드
3. "생성" 버튼 → `createTemplateFromRoadmap(uuid)` 호출
4. 성공 → 목록 새로고침 + 토스트 알림
5. 실패 → 에러 메시지 표시

**참고 패턴:** ActionKit `CategoryEditModal` (Dialog + input + save)

#### 3.2.3 상태 변경 다이얼로그 (`status-change-dialog.tsx`)

**현재 문제:** `prompt()`/`confirm()` 사용 → 브라우저 기본 UI, UX 불량

**개선:**
```typescript
interface StatusChangeDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (reason?: string) => void;
  currentStatus: TemplateStatus;
  targetStatus: TemplateStatus;
  templateTitle: string;
}
```

**UI:**
- Dialog 컴포넌트 (shadcn/ui)
- 현재 상태 → 대상 상태 표시 (배지)
- 사유 입력 (Textarea, 선택사항)
- 확인/취소 버튼

#### 3.2.4 액션 편집기 개선 (`template-action-editor.tsx`)

**현재:** 삭제만 가능
**개선:** 추가 + 수정 + 삭제 완성

**추가 UI (인라인 폼):**
- 섹션 하단 "＋ 추가" 버튼 → 인라인 입력 폼 토글
- 필드: title (필수), description (선택), source_url (선택)
- action_type은 섹션(체크리스트/법적근거/서류)에 따라 자동 설정
- "저장" → `createTemplateAction()` 호출 → `onActionChange()` 콜백

**수정 UI (인라인 편집):**
- 각 액션 행에 "연필" 아이콘 버튼 (editable일 때만 표시)
- 클릭 → 해당 행이 편집 모드로 전환 (input 필드들)
- "저장" / "취소" 버튼
- `updateTemplateAction()` 호출

**참고 패턴:** ActionKit의 인라인 추가/제거 패턴

#### 3.2.5 스텝 에디터 개선 (`template-step-editor.tsx`)

**현재 문제:** 빈 카테고리(체크리스트/법적근거/서류가 0개)에서 액션 추가 불가

**개선:** 모든 카테고리를 항상 표시하되, 0개인 경우에도 `TemplateActionEditor`를 렌더링하여 "＋ 추가" 가능하게 함

```typescript
// 변경: 조건부 렌더링 → 항상 렌더링 (editable일 때)
{(checklists.length > 0 || editable) && (
  <TemplateActionEditor
    label="체크리스트"
    actionType="CHECKLIST"
    actions={checklists}
    ...
  />
)}
```

#### 3.2.6 목록 테이블 개선 (`template-list-table.tsx`)

**추가 컬럼:**
- `startup_method` (업종 컬럼 옆)
- 날짜 표시 개선

---

## 4. 기술 결정사항

| # | 결정 | 근거 |
|---|------|------|
| 1 | 신규 Dialog 컴포넌트 생성 (shadcn/ui `Dialog` 사용) | 브라우저 `prompt()`/`confirm()` 대체, 일관된 UX |
| 2 | ActionKit 패턴 재활용 (인라인 추가/수정) | 검증된 패턴, 코드 일관성 |
| 3 | 별도 커스텀 훅 불필요 (useState로 충분) | 상태 복잡도 낮음, 오버엔지니어링 방지 |
| 4 | `types:sync`는 BE 완성 후 한번만 실행 | API 타입 수동 정의가 이미 정확함 |
| 5 | 토스트 알림은 기존 패턴 따름 (있으면 사용, 없으면 console.log) | 프로젝트에 토스트 라이브러리 확인 필요 |
| 6 | 로드맵 UUID 입력은 텍스트 필드 (드롭다운 아님) | 로드맵 목록 API가 ops 라우터에 없음 |

---

## 5. 구현 순서

### Step 1: 핵심 컴포넌트 신규 생성 (1h)
- `create-from-roadmap-dialog.tsx`
- `status-change-dialog.tsx`

### Step 2: 액션 에디터 완성 (3.5h)
- `template-action-editor.tsx` — 추가/수정 UI
- `template-step-editor.tsx` — 빈 카테고리 액션 추가 지원

### Step 3: 뷰 개선 (2.5h)
- `view.tsx` — business_type 필터 + 역생성 버튼
- `template-detail-view.tsx` — startup_method 편집 + Dialog 적용
- `template-list-table.tsx` — startup_method 컬럼

### Step 4: Quality Gates (1.5h)
- `npm run lint` 통과
- `npm run build` 성공
- 기본 테스트 작성

---

## 6. 리스크 및 완화

| 리스크 | 영향 | 완화 |
|--------|:----:|------|
| Phase 2 BE가 미완성이면 FE 통합 테스트 불가 | ★★★★ | API mock으로 개발, BE 완성 후 통합 |
| Dialog 컴포넌트 import 경로 이슈 | ★★ | shadcn/ui Dialog 사용 확인 |
| `types:sync` 실행 시 수동 타입과 충돌 | ★★ | 수동 타입이 정확하므로 sync 후 diff 확인 |
| 브라우저 `confirm()`/`prompt()` 사용처 누락 | ★ | grep으로 전체 검색 |

---

## 7. 성공 기준

1. **기능 완성**: 10개 API 엔드포인트를 모두 호출하는 UI 존재
2. **워크플로우 동작**: DRAFT → REVIEW → APPROVED → ARCHIVED 전체 흐름 동작
3. **CRUD 완성**: 템플릿 생성(역생성), 조회, 수정, 삭제, 상태변경 + 액션 추가/수정/삭제
4. **Quality Gates**: `npm run lint` + `npm run build` 통과
5. **운영 UX**: Dialog 기반 확인, 상태 배지, 적절한 로딩/에러 표시
