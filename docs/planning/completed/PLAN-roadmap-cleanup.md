# 로드맵 기능 정리 계획

> 작성일: 2026-02-28
> 기반 문서: roadmap-improvement 리서치 (planning/completed/roadmap-improvement/)
> **완료일: 2026-02-28**

---

## 정리 대상 요약

| # | 대상 | 유형 | 위치 | 위험도 | 상태 |
|---|------|------|------|--------|------|
| 1 | `generate.py` | 레거시 백엔드 엔드포인트 | BE | 낮음 | 완료 |
| 2 | `POST /roadmaps` 즉시 생성 | 미사용 API | BE | 낮음 | 유지 (API 계약) |
| 3 | `useGenerateRoadmap.ts` | 데드 코드 (훅) | FE | 없음 | 완료 |
| 4 | `GenerationForm.tsx` | 데드 코드 (컴포넌트) | FE | 없음 | 완료 |
| 5 | `RoadmapNode.tsx` / `RoadmapRenderer.tsx` | 데드 코드 (컴포넌트) | FE | 없음 | 완료 |
| 6 | `RoadmapRenderer.test.tsx` | 데드 코드 테스트 | FE | 없음 | 완료 |
| 7 | 타입 중복 정의 | 코드 품질 | FE | 낮음 | 불필요 (api-types.ts 미사용 확인) |
| 8 | `roadmap.md` 문서 부정확 | 문서 | docs | 없음 | 완료 |

---

## 1. 레거시 백엔드 `generate.py` 제거

**현황:**
- `app-backend/app/api/v1/roadmaps/generate.py` — `POST /api/v1/generate`
- `api.py`에서 별도 prefix(`/generate`)로 등록되어 있음
- `router.py`에서는 include하지 않음
- 프론트엔드에서 호출하는 곳 없음

**조치:**
- `generate.py` 파일 삭제
- `app-backend/app/api/v1/api.py`에서 import 및 include_router 제거

**관련 파일:**
- `app-backend/app/api/v1/roadmaps/generate.py` → 삭제
- `app-backend/app/api/v1/api.py` → import/include 제거

---

## 2. `POST /roadmaps` 즉시 생성 엔드포인트 검토

**현황:**
- `app-backend/app/api/v1/roadmaps/create.py`에 정의
- 기본 3단계만 생성 (AI 없이)
- 프론트엔드에서 호출하는 활성 코드 없음 (유일한 호출자는 데드 코드인 `useGenerateRoadmap`)
- 비동기 생성(`POST /roadmaps/jobs`)이 완전 대체

**조치:**
- 당장 삭제하지 않고 유지 (API 계약)
- 추후 공식 deprecated 처리 권장

---

## 3. 데드 프론트엔드 훅 `useGenerateRoadmap.ts` 삭제

**현황:**
- `app-frontend/src/features/roadmap/hooks/useGenerateRoadmap.ts`
- `POST /roadmaps` 호출 (레거시 즉시 생성)
- 유일한 사용처: `GenerationForm.tsx` (역시 데드 코드)

**조치:**
- 파일 삭제
- `hooks/index.ts`에서 export 제거

**관련 파일:**
- `app-frontend/src/features/roadmap/hooks/useGenerateRoadmap.ts` → 삭제
- `app-frontend/src/features/roadmap/hooks/index.ts` → export 제거

---

## 4. 데드 프론트엔드 컴포넌트 `GenerationForm.tsx` 삭제

**현황:**
- `app-frontend/src/features/roadmap/components/GenerationForm.tsx`
- 이전 세대 생성 폼 (Mock 모드 표시)
- 프론트엔드 어디서도 import/사용하지 않음
- 현재는 `RoadmapGenerationPanel` + `RoadmapChatIntake`가 대체

**조치:**
- 파일 삭제
- `components/index.ts`에서 export 제거

**관련 파일:**
- `app-frontend/src/features/roadmap/components/GenerationForm.tsx` → 삭제
- `app-frontend/src/features/roadmap/components/index.ts` → export 제거

---

## 5. 데드 트리 컴포넌트 `RoadmapNode.tsx` / `RoadmapRenderer.tsx` 삭제

**현황:**
- 초기 프로토타입의 트리 뷰 렌더러
- 현재 UI는 타임라인 기반 (`TimelinePhaseCard` + `TimelineStepItem`)
- 유일한 사용처: 테스트 파일 (역시 삭제 대상)

**조치:**
- 두 파일 모두 삭제
- `components/index.ts`에서 export 제거
- `types/roadmap.ts`의 `RoadmapNodeData` 타입도 사용처 확인 후 제거

**관련 파일:**
- `app-frontend/src/features/roadmap/components/RoadmapNode.tsx` → 삭제
- `app-frontend/src/features/roadmap/components/RoadmapRenderer.tsx` → 삭제
- `app-frontend/src/features/roadmap/components/index.ts` → export 제거
- `app-frontend/src/features/roadmap/types/roadmap.ts` → `RoadmapNodeData` 제거 검토

---

## 6. 데드 테스트 `RoadmapRenderer.test.tsx` 삭제

**현황:**
- `app-frontend/src/features/roadmap/__tests__/RoadmapRenderer.test.tsx`
- 삭제 대상인 `RoadmapRenderer`만 테스트
- 로드맵 feature의 유일한 테스트인데, 실제 사용 컴포넌트는 하나도 테스트하지 않음

**조치:**
- 파일 삭제
- `__tests__/` 디렉터리도 비면 삭제

---

## 7. 프론트엔드 타입 중복 정리

**현황:**
- `roadmap-utils.ts` — 수동 작성된 상세 타입 (RoadmapDetailAction, RoadmapDetailStep 등)
- `api-types.ts` (423~535행) — 자동 생성된 API 타입 (동일 엔티티의 다른 정의)
- 두 곳에 같은 엔티티의 타입이 각각 존재하며, `roadmap-utils.ts`가 더 완전함 (completed_at, metadata_json, MappingSource 등 포함)

**조치:**
- `roadmap-utils.ts`의 타입을 정본으로 유지
- `api-types.ts`의 로드맵 관련 타입과 일치 여부 확인
- 가능하면 한쪽에서 다른 쪽을 import하여 중복 제거
- 또는 OpenAPI 스키마를 업데이트하여 `api-types.ts` 재생성 후 `roadmap-utils.ts`에서 import

---

## 8. `roadmap.md` 문서 정정

**부정확한 내용:**

| 섹션 | 현재 기술 | 실제 |
|------|-----------|------|
| 3.1 계층 구조 | `generate.py`를 roadmaps 디렉터리 내로 표시 | 실제로는 `api.py`에서 `/generate` 별도 prefix로 등록 |
| 4.4 레거시 | `POST /api/v1/roadmaps/generate` | 실제 경로: `POST /api/v1/generate` |
| 7.1 디렉터리 | `GenerationForm.tsx` (레거시)로만 표시 | 데드 코드임을 명시 필요 |
| 7.1 디렉터리 | `RoadmapNode.tsx`, `RoadmapRenderer.tsx` 나열 | 데드 코드임을 명시 필요 |
| 7.3 커스텀 훅 | `useGenerateRoadmap` (레거시)로 표시 | 데드 코드임을 명시 필요 |

**조치:**
- 정리 작업 완료 후 `roadmap.md`에서 삭제된 파일/엔드포인트 관련 내용 제거
- 레거시/데드코드 관련 섹션 정리

---

## 실행 결과

```
Phase 1: 데드 코드 제거 ✓
├─ #6 RoadmapRenderer.test.tsx 삭제 + __tests__/ 디렉터리 삭제
├─ #5 RoadmapNode.tsx, RoadmapRenderer.tsx 삭제
├─ #4 GenerationForm.tsx 삭제
├─ #3 useGenerateRoadmap.ts 삭제
├─ components/index.ts export 정리 (3건 제거)
├─ hooks/index.ts export 정리 (1건 제거)
└─ types/roadmap.ts에서 RoadmapNodeData 인터페이스 제거

Phase 2: 레거시 백엔드 제거 ✓
├─ #1 generate.py 삭제
└─ api.py에서 import/include_router 제거

Phase 3: 코드 품질 개선 — 불필요
└─ #7 api-types.ts 로드맵 타입은 아무 데서도 import하지 않음 (roadmap-utils.ts가 정본)

Phase 4: 문서 업데이트 ✓
├─ #8 roadmap.md 계층 구조에서 generate.py 제거
├─ 4.4 레거시 섹션 삭제
├─ 7.1 디렉터리에서 데드 코드 파일 3건 제거
├─ 7.3 커스텀 훅에서 useGenerateRoadmap 제거
└─ 10. 파일 맵에서 삭제된 파일 제거 + roadmap-utils.ts 추가
```

### 검증 결과
- 프론트엔드: 삭제된 파일 참조 0건 (grep 확인)
- 백엔드: 삭제된 파일 참조 0건 (grep 확인)
