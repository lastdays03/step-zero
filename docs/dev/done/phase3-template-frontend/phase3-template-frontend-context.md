# Phase 3: 로드맵 템플릿 프론트엔드 — 컨텍스트 문서

> Last Updated: 2026-03-02

---

## 1. 핵심 파일 맵

### 수정 대상 파일 (기존)

| 파일 | 수정 범위 | 변경 사유 |
|------|----------|----------|
| `features/ops/roadmap-templates/view.tsx` | business_type 필터, 역생성 버튼 추가 | 목록 뷰 기능 완성 |
| `features/ops/roadmap-templates/template-detail-view.tsx` | startup_method 편집, Dialog 적용 | 상세 뷰 UX 개선 |
| `features/ops/roadmap-templates/components/template-list-table.tsx` | startup_method 컬럼 추가 | 목록 정보 완성 |
| `features/ops/roadmap-templates/components/template-step-editor.tsx` | 빈 카테고리 액션 추가 지원 | 편집 기능 완성 |
| `features/ops/roadmap-templates/components/template-action-editor.tsx` | 추가/수정 UI 구현 | 액션 CRUD 완성 |

### 신규 생성 파일

| 파일 | 역할 |
|------|------|
| `features/ops/roadmap-templates/components/create-from-roadmap-dialog.tsx` | 로드맵 UUID → 템플릿 생성 다이얼로그 |
| `features/ops/roadmap-templates/components/status-change-dialog.tsx` | 상태 변경 확인 다이얼로그 |
| `features/ops/roadmap-templates/__tests__/view.test.tsx` | 목록 뷰 렌더링 테스트 |
| `features/ops/roadmap-templates/__tests__/template-status-badge.test.tsx` | 상태 배지 테스트 |

### 변경 없는 파일 (참조용)

| 파일 | 역할 |
|------|------|
| `features/ops/roadmap-templates/types.ts` | 타입 정의 (완성됨) |
| `features/ops/roadmap-templates/api.ts` | API 호출 함수 (완성됨) |
| `features/ops/roadmap-templates/index.ts` | Public export (완성됨) |
| `features/ops/roadmap-templates/components/template-status-badge.tsx` | 상태 배지 (완성됨) |
| `features/ops/home/view.tsx` | Ops 홈 (카드 이미 추가됨) |
| `features/ops/index.ts` | Ops export (이미 등록됨) |
| `app/(dashboard)/ops/roadmap-templates/page.tsx` | 라우트 (완성됨) |
| `app/(dashboard)/ops/roadmap-templates/[templateId]/page.tsx` | 라우트 (완성됨) |

---

## 2. Backend API 참조

### Base URL: `/api/v1/ops/roadmap-templates`
### 인증: `require_platform_admin` (superuser only)

| # | Method | Path | FE 함수 | FE 사용처 | UI 구현 상태 |
|---|:------:|------|---------|----------|:----------:|
| 1 | GET | `/summary` | `fetchTemplateSummary()` | view.tsx 통계카드 | ✅ |
| 2 | GET | `/` | `fetchTemplates(params?)` | view.tsx 목록 | ✅ |
| 3 | GET | `/{id}` | `fetchTemplateDetail(id)` | detail-view 상세 | ✅ |
| 4 | POST | `/from-roadmap` | `createTemplateFromRoadmap(uuid)` | **미구현** → 신규 Dialog | ❌ |
| 5 | PATCH | `/{id}` | `updateTemplate(id, payload)` | detail-view 메타편집 | ⚠️ (startup_method 빠짐) |
| 6 | PATCH | `/{id}/status` | `updateTemplateStatus(id, payload)` | detail-view 상태변경 | ⚠️ (prompt→Dialog) |
| 7 | DELETE | `/{id}` | `deleteTemplate(id)` | view.tsx 삭제 | ⚠️ (confirm→Dialog) |
| 8 | POST | `/{id}/steps/{sid}/actions` | `createTemplateAction(tid,sid,p)` | **미구현** → 액션에디터 | ❌ |
| 9 | PATCH | `/{id}/steps/{sid}/actions/{aid}` | `updateTemplateAction(tid,sid,aid,p)` | **미구현** → 액션에디터 | ❌ |
| 10 | DELETE | `/{id}/steps/{sid}/actions/{aid}` | `deleteTemplateAction(tid,sid,aid)` | 액션에디터 삭제 | ✅ |

---

## 3. 타입 참조 (types.ts — 완성됨)

```typescript
type TemplateStatus = "DRAFT" | "REVIEW" | "APPROVED" | "ARCHIVED";

interface RoadmapTemplateAction {
  id: number;
  template_step_id: number;
  action_type: "CHECKLIST" | "LEGAL_BASIS" | "DOCUMENT";
  title: string;
  description: string;
  source_url: string | null;
  actionkit_item_id: number | null;
  actionkit_file_id: number | null;
  sort_order: number;
  metadata_json: Record<string, unknown>;
  created_at: string;
}

interface RoadmapTemplateStep {
  id: number;
  template_id: number;
  step_order: number;
  phase: string;
  title: string;
  objective: string;
  estimated_days: number;
  risk_notes: string[];
  created_at: string;
  actions: RoadmapTemplateAction[];
}

interface RoadmapTemplate {
  id: number;
  business_type: string;
  startup_method: string | null;
  title: string;
  status: TemplateStatus;
  version: number;
  source_roadmap_id: string | null;
  created_by: number;
  approved_by: number | null;
  approved_at: string | null;
  created_at: string;
  updated_at: string;
}

interface RoadmapTemplateDetail extends RoadmapTemplate {
  steps: RoadmapTemplateStep[];
}

interface TemplateSummary {
  total: number;
  draft: number;
  review: number;
  approved: number;
  archived: number;
}
```

---

## 4. UI 패턴 참조 (ActionKit에서 재활용)

### 4.1 인라인 추가 패턴
```tsx
// ActionKitEditModal에서 관련법령 추가 패턴:
<div className="flex gap-2">
  <Input
    value={newLawName}
    onChange={e => setNewLawName(e.target.value)}
    placeholder="법령명 입력"
  />
  <Button size="sm" onClick={handleAddLaw}>추가</Button>
</div>
```

### 4.2 Dialog 패턴
```tsx
// shadcn/ui Dialog 구조:
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";

<Dialog open={isOpen} onOpenChange={onClose}>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>제목</DialogTitle>
    </DialogHeader>
    {/* 본문 */}
    <DialogFooter>
      <Button variant="outline" onClick={onClose}>취소</Button>
      <Button onClick={handleConfirm}>확인</Button>
    </DialogFooter>
  </DialogContent>
</Dialog>
```

### 4.3 필터 드롭다운 패턴
```tsx
// 간단한 select 사용 (shadcn Select 또는 native):
<select
  value={businessTypeFilter}
  onChange={e => setBusinessTypeFilter(e.target.value)}
  className="h-9 rounded-md border border-slate-200 px-3 text-sm"
>
  <option value="">전체 업종</option>
  {businessTypes.map(bt => (
    <option key={bt} value={bt}>{bt}</option>
  ))}
</select>
```

---

## 5. 상태 전이 규칙 (FE에서 검증)

```
DRAFT ──→ REVIEW     (검토 요청)
REVIEW ──→ APPROVED  (승인)
REVIEW ──→ DRAFT     (반려)
APPROVED ──→ ARCHIVED (보관 처리)
```

### 편집 가능 상태: DRAFT, REVIEW
### 삭제 가능 상태: DRAFT, REVIEW
### 상태 변경 시 reason(사유) 입력: 선택사항

---

## 6. 의존성

### 하드 의존성 (필수)
- Phase 2 Section A (DB 스키마 + 마이그레이션) 완료
- Phase 2 Section B (백엔드 CRUD 서비스 + API) 완료
- 백엔드 서버 실행 가능 (`make run`)

### 소프트 의존성 (권장)
- Phase 2 Section B Group 3 (파이프라인 통합) — 역생성 테스트에 필요
- `npm run types:sync` — BE OpenAPI 스키마에서 자동 타입 생성 (수동 타입이 정확하면 스킵 가능)

### 사용하는 UI 라이브러리
- `@/components/ui/button` — Button
- `@/components/ui/card` — Card, CardContent
- `@/components/ui/dialog` — Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter
- `@/components/ui/input` — Input (있으면 사용)
- `@/components/ui/textarea` — Textarea (있으면 사용)
- `lucide-react` — 아이콘 (FileStack, RefreshCw, Plus, Pencil, Trash2, ArrowLeft, etc.)

---

## 7. 확정된 결정사항 (Phase 2에서 이월)

| 결정 | 근거 |
|------|------|
| Phase 1 매칭 키: `business_type`만 | 8개 업종 충분, startup_method는 선택적 |
| 상태 전이: DRAFT→REVIEW→APPROVED→ARCHIVED | 문서 B Section 10.1 |
| APPROVED 수정 불가, 새 버전만 가능 | 운영 중 템플릿 보호 |
| 자동 DRAFT: 업종 최초 생성 시만 | 중복 방지 |
| 감사로그: 상태 변경만 기록 | 기존 패턴 준수 |
