# Phase 0 로드맵 파이프라인 수정 - 구현 계획

> Last Updated: 2026-03-01 (Session 2)
> Status: **구현 완료 / 커밋 & PR 대기**
> Branch: `feature/0-roadmap-improvement`

---

## 1. Executive Summary

로드맵 생성 파이프라인의 **3가지 근본 문제**를 해결하는 Phase 0 작업이다.

| 문제 | 증상 | 영향 범위 |
|------|------|-----------|
| **링크 오류** | LLM이 `actionkit_item_id` 변조/누락, `break`문으로 첫 파일만 매핑 | 사용자 로드맵의 법령/서류 링크 404 |
| **FE 폴백 부재** | `source_url` 없는 DOCUMENT 액션에 아무것도 표시 안 함 | 사용자에게 빈 화면 노출 |
| **어휘 불일치** | `startup_method`(신규/양수양도/프랜차이즈) 차원 누락 | Phase 2 템플릿 매칭 불가 |

이 3가지는 Phase 2(템플릿)와 Phase 4(AI 코치)의 선행 조건이므로 **반드시 먼저 수정**해야 한다.

---

## 2. Current State Analysis (구현 전)

### 2.1 BE - 링크 생성 파이프라인
- `roadmap_generation_service.py`: `break`문으로 아이템당 첫 파일만 매핑
- `llm_personalizer.py`: `_validate_references()`가 경고 로그만 남기고 데이터 수정 안 함
- `roadmap_repository.py`: `_resolve_document_source_url()`이 파일 경로 기반으로만 해석

### 2.2 FE - 링크 표시 로직
- `TimelineStepItem.tsx`: `source_url` 없는 DOCUMENT는 `null` 렌더링
- `metadata_json.actionkit_item_id`가 있어도 대안 링크 미활용

### 2.3 어휘 체계
- `startup_type`(개인/법인)만 존재
- `startup_method`(신규/양수양도/프랜차이즈) 차원 없음
- DB/모델/스키마/폼 어디에도 해당 필드 없음

---

## 3. Proposed Future State (구현 완료)

### 3.1 BE - 복구 + 통일
- `_validate_and_repair_references()`: 3단계 복구 전략 + 퍼지 매칭
- `_actionkit_item_url()`: 모든 source_url을 `/api/v1/actionkits/items/{id}` 패턴으로 통일
- `item_file_urls: dict[int, list[str]]`: 다중 파일 매핑

### 3.2 FE - 폴백 + 대안 링크
- IIFE 패턴: `source_url` → `actionkit_item_id` 링크 → 타입별 "준비 중" 메시지
- DOCUMENT/LEGAL_BASIS 모두 일관된 폴백

### 3.3 어휘 체계
- `startup_method` 필드: DB(모델+마이그레이션) → BE(payload+pipeline) → FE(form+panel)
- 기존 데이터 source_url 일괄 업데이트 (마이그레이션)

---

## 4. Implementation Phases

### Phase A: 링크 오류 수정 (핵심)

| ID | 작업 | 파일 | 크기 | 상태 |
|----|------|------|:----:|:----:|
| 0-A-4 | 다중 파일 매핑 (`break` 제거) | `roadmap_generation_service.py` | S | **완료** |
| 0-A-3 | LLM 참조 자동 복구 로직 | `llm_personalizer.py` | L | **완료** |
| 0-A-1 | DOCUMENT 폴백 표시 | `TimelineStepItem.tsx` | S | **완료** |
| 0-A-2 | `actionkit_item_id` 대안 링크 | `TimelineStepItem.tsx` | M | **완료** |

### Phase B: source_url 통일 + 퍼지 매칭

| ID | 작업 | 파일 | 크기 | 상태 |
|----|------|------|:----:|:----:|
| 0-B-1 | source_url item_id 기반 통일 | `roadmap_generation_service.py`, `roadmap_repository.py` | M | **완료** |
| 0-B-2 | 기존 데이터 source_url 마이그레이션 | `009_startup_method_and_source_urls.py` | M | **완료** |
| 0-B-3 | 퍼지 매칭 모드 | `llm_personalizer.py` | L | **완료** |

### Phase C: startup_method 어휘 추가

| ID | 작업 | 파일 | 크기 | 상태 |
|----|------|------|:----:|:----:|
| 0-C-3 | DB 모델 + 마이그레이션 | `models/roadmap.py`, `009_*.py` | S | **완료** |
| 0-C-2 | BE 파이프라인 전파 | 7개 파일 (service/repo/schema/personalizer) | M | **완료** |
| 0-C-1 | FE 인테이크 폼 | 4개 파일 (ChatIntake/constants/Panel/hook) | M | **완료** |

### Phase D: 파일 URL 접근성 개선 (Session 2 추가)

| ID | 작업 | 파일 | 크기 | 상태 |
|----|------|------|:----:|:----:|
| 0-D-1 | 이중 인코딩 StaticFiles 수정 | `main.py` (DecodingStaticFiles) | S | **완료** |
| 0-D-2 | FE 링크 BE 도메인 prefix | `TimelineStepItem.tsx` (API_URL) | S | **완료** |
| 0-D-3 | 아이템 뷰어 엔드포인트 | `files.py` (/view, /download, redirect) | M | **완료** |
| 0-D-4 | 테스트 수정 (tuple 언패킹) | `test_roadmap_generation_service.py` | S | **완료** |

---

## 5. 의존성 그래프

```
0-A-4 (break 제거) ──────┐
                         ├──→ 0-B-1 (source_url 통일) ──→ 0-B-2 (DB 마이그레이션)
0-A-3 (참조 복구) ───────┤                                       │
                         ├──→ 0-B-3 (퍼지 매칭)                  │
0-A-1 (FE 폴백) ─→ 0-A-2 (FE 대안 링크)                        │
                                                                 │
0-C-3 (BE 모델) ─→ 0-C-2 (BE 전파) ─→ 0-C-1 (FE 폼) ◀─────────┘

0-D-1 (이중 인코딩) ──→ 0-D-3 (뷰어 엔드포인트)
0-D-2 (FE API_URL) ────┘
0-D-4 (테스트 수정)
```

**구현 순서**: 0-A-4 → 0-A-3 → 0-A-1+0-A-2 → 0-B-1 → 0-C-3+0-B-2 → 0-C-2 → 0-C-1 → 0-B-3 → 0-D-1 → 0-D-2 → 0-D-3 → 0-D-4

---

## 6. Risk Assessment

| 리스크 | 영향도 | 완화 전략 | 상태 |
|--------|:------:|----------|:----:|
| 퍼지 매칭 false positive | ★★★ | threshold=0.6, Jaccard+substring, 20개 테스트 | 완화됨 |
| 마이그레이션 source_url 덮어쓰기 | ★★☆ | 기존 값이 이미 비정상, 새 패턴이 결정적 | 허용 |
| FE→BE 배포 순서 역전 | ★★★★ | BE 먼저 배포 필수 (startup_method 인식) | 문서화 |
| SQLite 테스트에서 마이그레이션 미실행 | ★☆☆ | 테스트 DB는 `create_all()` 사용 | 영향 없음 |
| `all_file_urls`로 metadata_json 크기 증가 | ★☆☆ | 아이템당 1-3개 파일, 증가 미미 | 허용 |
| 리버스 프록시 이중 인코딩 | ★★★ | `DecodingStaticFiles` 커스텀 클래스 | 해결됨 |
| FE/BE 도메인 분리 링크 404 | ★★★ | `NEXT_PUBLIC_API_URL` prefix 적용 | 해결됨 |
| 한국어 파일명 Content-Disposition 인코딩 | ★★☆ | RFC 5987 `filename*=UTF-8''` | 해결됨 |

---

## 7. Success Metrics

| 지표 | 기준 | 현재 |
|------|------|------|
| Backend pytest (Docker) | 177 passed, 0 failed | **177 passed, 1 skipped** |
| 신규 테스트 (복구/퍼지) | 20 passed | **통과** |
| Frontend lint (Docker) | 에러 0 | **통과** |
| Frontend build (Docker) | 빌드 성공 | **Next.js 16.1.6 빌드 성공** |
| source_url 패턴 통일 | 모든 새 로드맵 `/api/v1/actionkits/items/{id}` | 코드 확인 + DB 검증 완료 |
| FE 폴백 커버리지 | LEGAL_BASIS + DOCUMENT 모두 폴백 | 코드 확인 완료 |
| 마이그레이션 009 적용 | 기존 source_url 변환 | **396건 file→item 변환 완료** (로컬 DB) |
| 파일 뷰어 엔드포인트 | .md HTML 렌더링, .pdf 인라인 | **200 OK** |
| 이중 인코딩 URL 지원 | 한국어 파일 URL 200 OK | **DecodingStaticFiles 적용** |

---

## 8. 배포 체크리스트

1. [x] `npm run lint` (Docker) — 통과
2. [x] `npm run build` (Docker) — Next.js 16.1.6 성공
3. [ ] `npm run types:sync` 실행하여 BE OpenAPI → FE 타입 동기화
4. [ ] `black .` + `isort . --profile black` 코드 포맷
5. [ ] Git 커밋 (13 modified + 4 untracked, test 파일은 `git add -f`)
6. [ ] PR 생성: `feature/0-roadmap-improvement` → `develop`
7. [ ] **BE 먼저 배포** → 마이그레이션 실행 (`alembic upgrade head`)
8. [ ] FE 배포
9. [ ] 수동 검증: 기존 로드맵 링크 클릭 → 404 없음
10. [ ] 수동 검증: 새 로드맵 생성 → startup_method 질문 + source_url 패턴 확인
