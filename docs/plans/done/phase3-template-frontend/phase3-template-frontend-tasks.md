# Phase 3: 로드맵 템플릿 프론트엔드 — Task Checklist

> Last Updated: 2026-03-02
> Branch: `feature/2-template-system`
> 의존성: Phase 2 백엔드 (Section A + B) 완료 필수

---

## Section 1: 신규 Dialog 컴포넌트 (1h)

### 1-A. 상태 변경 확인 다이얼로그

- [x] **1-A-1** `components/status-change-dialog.tsx` 생성
  - [x] Props: `isOpen`, `onClose`, `onConfirm(reason?)`, `currentStatus`, `targetStatus`, `templateTitle`
  - [x] shadcn/ui Dialog 사용
  - [x] 현재→대상 상태 배지 표시
  - [x] 사유 입력 Textarea (선택사항)
  - [x] 확인/취소 버튼

### 1-B. 로드맵 역생성 다이얼로그

- [x] **1-B-1** `components/create-from-roadmap-dialog.tsx` 생성
  - [x] Props: `isOpen`, `onClose`, `onCreated()`
  - [x] Roadmap UUID 입력 필드
  - [x] `createTemplateFromRoadmap(uuid)` API 호출
  - [x] 로딩 상태 (버튼 disabled + 텍스트)
  - [x] 성공: onCreated 콜백 + Dialog 닫기
  - [x] 실패: 인라인 에러 메시지

---

## Section 2: 액션 에디터 완성 (3.5h)

### 2-A. 액션 추가 UI

- [x] **2-A-1** `template-action-editor.tsx`에 `actionType` prop 추가
  - 현재: label만 받음 → `actionType: "CHECKLIST" | "LEGAL_BASIS" | "DOCUMENT"` 추가
- [x] **2-A-2** 인라인 추가 폼 구현
  - [x] "＋ 추가" 버튼 (editable일 때만 표시)
  - [x] 클릭 → 인라인 입력 폼 토글 (title, description, source_url)
  - [x] action_type은 prop에서 자동 설정
  - [x] "저장" → `createTemplateAction(templateId, stepId, payload)` 호출
  - [x] "취소" → 폼 닫기
  - [x] 성공 → `onActionChange()` 콜백
- [x] **2-A-3** 입력 유효성 검사
  - [x] title 필수 (빈 문자열 방지)
  - [x] 저장 중 버튼 disabled

### 2-B. 액션 수정 UI

- [x] **2-B-1** 각 액션 행에 수정 버튼 추가 (Pencil 아이콘)
  - editable일 때만 표시
  - Trash2 버튼 왼쪽에 배치
- [x] **2-B-2** 인라인 편집 모드 구현
  - [x] 수정 버튼 클릭 → 해당 행 편집 모드 전환
  - [x] editingActionId 상태로 관리
  - [x] title, description, source_url 입력 필드
  - [x] "저장" → `updateTemplateAction(templateId, stepId, actionId, payload)` 호출
  - [x] "취소" → 편집 모드 해제
  - [x] 성공 → `onActionChange()` 콜백

### 2-C. 스텝 에디터 개선

- [x] **2-C-1** `template-step-editor.tsx` 수정
  - `TemplateActionEditor`에 `actionType` prop 전달
  - 빈 카테고리도 렌더링 (editable일 때)
  ```
  AS-IS: {checklists.length > 0 && <TemplateActionEditor .../>}
  TO-BE: {(checklists.length > 0 || editable) && <TemplateActionEditor actionType="CHECKLIST" .../>}
  ```
  - 동일하게 legalBasis, documents 섹션도 수정
- [x] **2-C-2** 빈 카테고리 안내 문구 조건 업데이트
  - editable일 때는 "등록된 액션이 없습니다" 대신 각 카테고리 에디터 표시

---

## Section 3: 뷰 개선 (2.5h)

### 3-A. 목록 뷰 (`view.tsx`)

- [x] **3-A-1** business_type 필터 드롭다운 추가
  - [x] `businessTypeFilter` 상태 추가
  - [x] 업종 목록 자동 추출 (`useMemo` + `Set`)
  - [x] 필터 select를 헤더 영역에 배치
  - [x] `filtered` useMemo에 businessTypeFilter 조건 추가
- [x] **3-A-2** "로드맵에서 생성" 버튼 추가
  - [x] 헤더 우측 (새로고침 버튼 옆)
  - [x] `showCreateDialog` 상태
  - [x] `CreateFromRoadmapDialog` 렌더링
  - [x] 성공 시 `load()` 호출
- [ ] **3-A-3** 삭제 확인 `confirm()` → Dialog 변경 (선택적)
  - 우선순위 낮음, confirm()도 동작하므로 보류

### 3-B. 상세 뷰 (`template-detail-view.tsx`)

- [x] **3-B-1** startup_method 편집 필드 추가
  - [x] `editStartupMethod` 상태 추가
  - [x] 메타 편집 카드에 3번째 필드 추가
  - [x] `handleSaveMeta()`에 startup_method 포함
- [x] **3-B-2** 상태 변경 → StatusChangeDialog 적용
  - [x] `statusDialogState` 상태 (isOpen, targetStatus)
  - [x] nextAction/rejectAction 버튼 → Dialog 오픈으로 변경
  - [x] Dialog onConfirm → `handleStatusChange(status, reason)` 호출
  - [x] `prompt()` 제거

### 3-C. 목록 테이블 (`template-list-table.tsx`)

- [x] **3-C-1** startup_method 컬럼 추가
  - 업종 컬럼 옆에 "창업방식" 컬럼
  - null이면 "-" 표시

---

## Section 4: Quality Gates (1.5h)

### 4-A. 린트 + 빌드

- [x] **4-A-1** `cd app-frontend && npm run lint` — 0 errors ✅
- [x] **4-A-2** `cd app-frontend && npm run build` — 성공 (19 static pages, 12.8s) ✅

### 4-B. 테스트 (선택적)

- [ ] **4-B-1** `__tests__/template-status-badge.test.tsx`
  - 4개 상태별 올바른 레이블 렌더링
  - 올바른 CSS 클래스 적용
- [ ] **4-B-2** `__tests__/view.test.tsx`
  - 기본 렌더링 (타이틀, 탭 5개 표시)
  - API mock으로 데이터 로드 확인

### 4-C. 통합 확인

- [ ] **4-C-1** BE 서버 실행 후 실제 동작 테스트 (Phase 2 BE 완료 후)
  - [ ] 목록 페이지 접근 (`/ops/roadmap-templates`)
  - [ ] 통계 카드 표시
  - [ ] 상태 탭 필터링
  - [ ] 상세 페이지 진입
  - [ ] 메타 편집 + 저장
  - [ ] 상태 변경 워크플로우
  - [ ] 액션 추가/수정/삭제
  - [ ] 역생성 (로드맵 UUID 입력 → 템플릿 생성)

---

## Progress Summary

| Section | 전체 | 완료 | 진행률 |
|:-------:|:----:|:----:|:------:|
| 1 (Dialog 컴포넌트) | 2 | 2 | 100% |
| 2 (액션 에디터) | 5 | 5 | 100% |
| 3 (뷰 개선) | 6 | 5 | 83% |
| 4 (Quality Gates) | 5 | 2 | 40% |
| **합계** | **18** | **14** | **78%** |

---

## 의존성 그래프

```
Section 1 (Dialog 컴포넌트)
├── 1-A (StatusChangeDialog) ──→ 3-B-2 (상세뷰 적용)
└── 1-B (CreateFromRoadmapDialog) ──→ 3-A-2 (목록뷰 적용)

Section 2 (액션 에디터)
├── 2-A (액션 추가) ──┐
├── 2-B (액션 수정) ──┤──→ 2-C (스텝에디터 개선)
└── (독립적으로 진행 가능)

Section 3 (뷰 개선)
├── 3-A (목록뷰) ← 1-B에 의존
├── 3-B (상세뷰) ← 1-A에 의존
└── 3-C (테이블) ← 독립

Section 4 (Quality Gates)
└── 전체 → 4-A (lint/build) → 4-B (테스트) → 4-C (통합)
```

### 병렬화 가능 구간

```
Track A: Section 1 전체 + Section 3 (Dialog → 뷰 적용)
Track B: Section 2 전체 (액션 에디터, 독립적)
  ↓
Track C: Section 4 (Quality Gates, 모두 완료 후)
```
