# Phase 0 구현 계획: 링크 오류 수정 + startup_method 어휘 정리

> 작성일: 2026-03-01
> 목적: implementation-order-report.md Phase 0의 10개 작업을 코드베이스 검증 후 구체적 구현 계획으로 상세화
> 방법: BE(llm_personalizer/generation_service/repository) + FE(TimelineStepItem/ChatIntake) + 인프라(Alembic) 3개 영역 병렬 코드 분석
> 근거 문서: chatbot-enhancement-analysis.md, roadmap-template-management-analysis.md, implementation-order-report.md

---

## 1. Context

로드맵 생성 파이프라인에서 **3가지 근본 문제**가 확인되었다:

1. **링크 오류** — LLM이 `actionkit_item_id`를 변조/누락하고, `_validate_references()`가 경고만 남기고 수정하지 않음. 또한 `break`문으로 첫 파일만 매핑되어 다중 파일 손실.
2. **프론트엔드 폴백 부재** — `source_url` 없는 DOCUMENT 액션은 아무것도 표시 안 함. `metadata_json.actionkit_item_id` 대안 링크 미활용.
3. **어휘 불일치** — `startup_type`(개인/법인)만 존재, `startup_method`(신규/양수양도/프랜차이즈) 차원 누락. 향후 템플릿 매칭의 선행 조건.

이 문제들은 Phase 2(템플릿)와 Phase 4(AI 코치)의 기반이므로 **반드시 선행 수정**해야 한다.

---

## 2. 구현 순서 및 의존성 그래프

```
0-A-4 (break 제거) ──────┐
                         ├──→ 0-B-1 (source_url 통일) ──→ 0-B-2 (DB 마이그레이션)
0-A-3 (참조 복구) ───────┤                                       │
                         ├──→ 0-B-3 (퍼지 매칭)                  │
0-A-1 (FE 폴백) ─→ 0-A-2 (FE 대안 링크)                        │
                                                                 │
0-C-3 (BE 모델) ─→ 0-C-2 (BE 전파) ─→ 0-C-1 (FE 폼) ◀─────────┘
                                              ↑
                                   마이그레이션과 동일 009 파일
```

**권장 순서**: 0-A-4 → 0-A-3 → 0-A-1+0-A-2 → 0-B-1 → 0-C-3+0-B-2(단일 마이그레이션) → 0-C-2 → 0-C-1 → 0-B-3

---

## 3. 작업별 상세 구현 계획

### 3.1 0-A-4: 다중 파일 매핑 수정 (BE, 0.5일)

**파일**: `app-backend/app/features/roadmaps/application/roadmap_generation_service.py`

**문제**: Line 312-322, `break`문으로 ActionKit 아이템당 첫 파일만 매핑

```python
# 현재 코드 (문제)
item_file_urls: dict[int, str] = {}
if matched_items:
    for m in matched_items:
        if m.item.id is not None and m.files:
            for f in m.files:
                item_file_urls[m.item.id] = (
                    f"/api/v1/actionkits/files/{f.object_key}"
                )
                break  # ← 첫 파일만 매핑 후 종료
```

**변경**:
1. `item_file_urls` 타입을 `dict[int, str]` → `dict[int, list[str]]`로 변경
2. `break` 제거, 리스트 컴프리헨션으로 모든 파일 수집:
   ```python
   item_file_urls: dict[int, list[str]] = {}
   if matched_items:
       for m in matched_items:
           if m.item.id is not None and m.files:
               item_file_urls[m.item.id] = [
                   f"/api/v1/actionkits/files/{f.object_key}"
                   for f in m.files
               ]
   ```
3. 소비처 3곳에서 `[0]` 인덱스로 첫 파일 접근 (기존 동작 유지):
   - legal_basis enrichment (Line 331-334): `source_url = item_file_urls[item_id][0]`
   - documents fallback (Line 351-355): `file_url = item_file_urls[item_id][0]`
   - document_items append (Line 357-365): `source_url`/`file_url`은 첫 파일 유지
4. document_items에 `all_file_urls` 키 추가 → `metadata_json`에 저장되어 향후 활용 가능:
   ```python
   "all_file_urls": item_file_urls.get(doc.get("actionkit_item_id"), []),
   ```

**하위 호환**: 기존 `source_url`/`file_url` 동작 동일 (첫 파일), `all_file_urls`는 additive

---

### 3.2 0-A-3: LLM 참조 자동 복구 로직 (BE, 2일)

**파일**: `app-backend/app/features/roadmaps/application/llm_personalizer.py`

**문제**: Line 302-328, `_validate_references()`가 `logger.debug()`만 남기고 데이터 수정 안 함

```python
# 현재 코드 (문제) - 경고만 남기고 데이터 수정 없음
@staticmethod
def _validate_references(
    details: list[PersonalizedStepDetail],
    original_law_names: set[str],
    original_file_keys: set[str],
) -> list[PersonalizedStepDetail]:
    for detail in details:
        for lb in detail.legal_basis:
            title = lb.get("title", "")
            if title and original_law_names and title not in original_law_names:
                logger.debug("LLM modified law name: '%s' not in originals", title)
        for doc in detail.documents:
            file_url = doc.get("file_url", "")
            if file_url and original_file_keys and file_url not in original_file_keys:
                logger.debug("LLM modified file path: '%s' not in originals", file_url)
    return details  # ← 아무 수정 없이 반환
```

**변경**:

#### 3.2.1 `_build_repair_indexes()` 신규 추가
- `matched_items: list[MatchedActionKit]`에서 복구용 인덱스 구축
- 반환 dict:
  - `valid_item_ids: set[int]` — 유효한 아이템 ID 집합
  - `item_id_to_laws: dict[int, list[dict]]` — 아이템별 법령 정보
  - `item_id_to_files: dict[int, list[dict]]` — 아이템별 파일 정보
  - `law_name_to_item_id: dict[str, int]` — 법령명 → 아이템 ID 역매핑
  - `file_key_to_item_id: dict[str, int]` — 파일키 → 아이템 ID 역매핑
  - `law_name_set: set[str]`, `file_key_set: set[str]`

#### 3.2.2 `_validate_references()` → `_validate_and_repair_references()` 교체
- **시그니처 변경**: `(details, matched_items)` — `original_law_names`/`original_file_keys` 대신 `matched_items` 직접 받음
- **복구 전략 (우선순위)**:
  1. `actionkit_item_id` 유효 → 해당 아이템의 원본 `law_name`/`file_url`로 복구
  2. `title`/`file_url`이 원본 집합에 존재 → `actionkit_item_id` 역매핑으로 복구
  3. 모두 무효 → 할루시네이션으로 판단, 항목 제거 (`logger.warning`)
- `detail.actionkit_items` 리스트의 무효 ID도 필터링
- 빈 리스트 방어: `repaired_legal`이 비면 원본 유지 (데이터 전부 삭제 방지)

#### 3.2.3 `personalize()` 호출부 수정 (Line 175-177)
```python
# Before:
original_law_names, original_file_keys = self._collect_originals(matched_items)
details = self._validate_references(details, original_law_names, original_file_keys)

# After:
details = self._validate_and_repair_references(details, matched_items)
```
- `_collect_originals()` 메서드 삭제 (Line 288-300)

**하위 호환**: `personalize()` 입출력 동일, 유효한 참조는 수정 없이 통과

---

### 3.3 0-A-1: DOCUMENT/LEGAL_BASIS 일관된 폴백 표시 (FE, 0.5일)

**파일**: `app-frontend/src/features/roadmap/components/TimelineStepItem.tsx`

**문제**: Line 253-257, DOCUMENT는 `source_url` 없으면 아무것도 표시 안 함

**현재 코드**:
```tsx
{item.source_url ? (
    <a href={item.source_url} target="_blank" rel="noreferrer"
       className="inline-flex items-center gap-1 mt-1 text-xs text-[#36a4f2] hover:underline">
        근거/원문 보기 <ExternalLink className="w-3 h-3" />
    </a>
) : item.action_type === "LEGAL_BASIS" ? (
    <span className="inline-flex items-center gap-1 mt-1 text-xs text-slate-400">
        상세 법령 정보 준비 중
    </span>
) : null}  // ← DOCUMENT는 아무것도 표시 안 함
```

**변경**: Line 257의 `: null}` 앞에 DOCUMENT 분기 추가
```tsx
) : item.action_type === "DOCUMENT" ? (
    <span className="inline-flex items-center gap-1 mt-1 text-xs text-slate-400">
        서류 정보 준비 중
    </span>
) : null}
```

---

### 3.4 0-A-2: actionkit_item_id 기반 대안 링크 (FE, 1일)

**파일**: `app-frontend/src/features/roadmap/components/TimelineStepItem.tsx`

**문제**: `source_url` null이지만 `metadata_json.actionkit_item_id`가 있어도 링크 미표시

**변경**: Line 243-257 전체를 IIFE 패턴으로 교체 (중첩 삼항 → 명확한 분기)

```tsx
{(() => {
    const actionkitItemId = item.metadata_json?.actionkit_item_id as number | undefined;

    if (item.source_url) {
        return (
            <a href={item.source_url} target="_blank" rel="noreferrer"
               className="inline-flex items-center gap-1 mt-1 text-xs text-[#36a4f2] hover:underline">
                근거/원문 보기 <ExternalLink className="w-3 h-3" />
            </a>
        );
    }
    if (actionkitItemId) {
        return (
            <a href={`/api/v1/actionkits/items/${actionkitItemId}/download`}
               target="_blank" rel="noreferrer"
               className="inline-flex items-center gap-1 mt-1 text-xs text-[#36a4f2]/70 hover:text-[#36a4f2] hover:underline">
                원문 보기 <ExternalLink className="w-3 h-3" />
            </a>
        );
    }
    if (item.action_type === "LEGAL_BASIS") {
        return (<span className="inline-flex items-center gap-1 mt-1 text-xs text-slate-400">
            상세 법령 정보 준비 중</span>);
    }
    if (item.action_type === "DOCUMENT") {
        return (<span className="inline-flex items-center gap-1 mt-1 text-xs text-slate-400">
            서류 정보 준비 중</span>);
    }
    return null;
})()}
```

- 우선순위: `source_url` → `actionkit_item_id` 링크 → 타입별 "준비 중" 메시지
- `actionkit_item_id` 링크는 `text-[#36a4f2]/70` (약간 연한 색)으로 구분
- 링크 텍스트: "원문 보기" (source_url의 "근거/원문 보기"와 구분)

**전제**: `/api/v1/actionkits/items/{id}/download` 엔드포인트 존재 확인됨 (`app-backend/app/api/v1/actionkit/files.py`)

---

### 3.5 0-B-1: source_url item_id 기반 통일 (BE, 1일)

**파일**: `app-backend/app/features/roadmaps/application/roadmap_generation_service.py`, `app-backend/app/repositories/roadmap_repository.py`

**변경**:

#### roadmap_generation_service.py
1. `_actionkit_item_url(item_id: int) -> str` 헬퍼 추가:
   ```python
   def _actionkit_item_url(item_id: int) -> str:
       return f"/api/v1/actionkits/items/{item_id}"
   ```
2. legal_basis source_url enrichment (Line 329-342): `item_id` 유효하면 `_actionkit_item_url(item_id)` 사용
   ```python
   source_url = _actionkit_item_url(item_id) if item_id else None
   ```
3. document source_url (Line 344-365): `item_id` 유효하면 `_actionkit_item_url(item_id)`, `file_url`은 다운로드용으로 별도 유지
   ```python
   source_url = _actionkit_item_url(item_id) if item_id else file_url
   ```

#### roadmap_repository.py
4. `_resolve_document_source_url()` (Line 16-21): `actionkit_item_id` 우선 체크 추가
   ```python
   @staticmethod
   def _resolve_document_source_url(item: dict) -> str | None:
       item_id = item.get("actionkit_item_id")
       if item_id:
           return f"/api/v1/actionkits/items/{item_id}"
       for key in ("source_url", "download_url", "template_url", "file_url"):
           value = item.get(key)
           if isinstance(value, str) and value.strip():
               return value
       return None
   ```

---

### 3.6 0-C-3 + 0-B-2: DB 마이그레이션 (단일 파일, 0.5일+0.5일)

**파일**: `app-backend/alembic/versions/009_startup_method_and_source_urls.py` (신규)

**변경**:
1. `roadmap` 테이블에 `startup_method` 컬럼 추가 (nullable, AutoString)
2. `roadmap_step_actions`의 기존 source_url을 `metadata_json->>'actionkit_item_id'` 기반으로 일괄 업데이트:
   ```sql
   UPDATE roadmap_step_actions
   SET source_url = '/api/v1/actionkits/items/' || (metadata_json->>'actionkit_item_id')
   WHERE metadata_json->>'actionkit_item_id' IS NOT NULL
     AND metadata_json->>'actionkit_item_id' != ''
     AND action_type IN ('LEGAL_BASIS', 'DOCUMENT')
   ```

**모델 파일**: `app-backend/app/models/roadmap.py` Line 16 뒤에 추가:
```python
startup_method: str | None = None  # 신규/양수양도/프랜차이즈
```

**주의**: PostgreSQL 전용 `->>`문법. 테스트 DB(SQLite)에서는 마이그레이션이 아닌 `create_all()`로 스키마 생성하므로 영향 없음. downgrade에서 source_url 원복은 불가 (원래 값이 비정상이므로 허용).

---

### 3.7 0-C-2: GenerationPayload + 파이프라인 전파 (BE, 0.5일)

**수정 파일 목록**:

| # | 파일 | 위치 | 변경 |
|---|------|------|------|
| 1 | `roadmap_generation_service.py` | Line 69-78 `GenerationPayload` | `startup_method: str \| None = None` 추가 |
| 2 | `roadmap_generation_service.py` | Line 284-296 `_payload_to_dict()` | `"startup_method": payload.startup_method` 추가 |
| 3 | `roadmap_generation_service.py` | Line 256-267 `process_job()` | `create_roadmap()` 호출에 `startup_method=payload.startup_method` 전달 |
| 4 | `roadmap_repository.py` | Line 85-114 `create_roadmap()` | 파라미터에 `startup_method: str \| None = None` 추가, Roadmap 생성에 전달 |
| 5 | `api/v1/schemas.py` | Line 145-154 `RoadmapJobCreateRequest` | `startup_method: str \| None = None` 추가 |
| 6 | `llm_personalizer.py` | Line 95-110 `_USER_PROMPT_TEMPLATE` | `- 창업 방식: {startup_method}` 줄 추가 (Line 99 `창업 형태` 다음) |
| 7 | `llm_personalizer.py` | Line 138-148 `personalize()` | format() 호출에 `startup_method=payload.get("startup_method") or "미입력"` 추가 |

**하위 호환**: 모든 필드 `None` 기본값. 기존 `input_payload` JSON에 `startup_method` 없어도 `GenerationPayload(**payload)` 정상 동작 (Line 187).

---

### 3.8 0-C-1: 인테이크 폼 startup_method 추가 (FE, 1일)

**전제**: 0-C-2 백엔드 배포 완료 필수 (`GenerationPayload`가 `startup_method`를 인식해야 함)

**수정 파일 목록**:

| # | 파일 | 변경 |
|---|------|------|
| 1 | `roadmap-constants.ts` | `INTAKE_FIELD_SUGGESTIONS`에 `startup_method: ["신규 창업", "양수양도", "프랜차이즈"]` 추가 |
| 2 | `RoadmapChatIntake.tsx` | `FieldKey` 타입에 `"startup_method"` 추가 |
| 3 | `RoadmapChatIntake.tsx` | `RoadmapRawInput` 인터페이스에 `startup_method: string` 추가 |
| 4 | `RoadmapChatIntake.tsx` | `RoadmapIntakePayload`에 `startup_method: string` 추가 |
| 5 | `RoadmapChatIntake.tsx` | `QUESTIONS` 배열에 startup_type 다음 삽입: `{ key: "startup_method", prompt: "창업 방식은 무엇인가요? (신규 창업/양수양도/프랜차이즈)", required: true }` |
| 6 | `RoadmapChatIntake.tsx` | `PANEL_ROWS`에 `{ key: "startup_method", label: "방식", icon: <Repeat2 /> }` 추가. `Repeat2` lucide-react import 추가 |
| 7 | `RoadmapChatIntake.tsx` | `answers` 초기값에 `startup_method: ""` 추가 |
| 8 | `RoadmapChatIntake.tsx` | `handleValidate` rawInput 구성에 `startup_method` 포함 |
| 9 | `RoadmapChatIntake.tsx` | 검증 로직에 `!rawInput.startup_method` 추가 |
| 10 | `RoadmapGenerationPanel.tsx` | payload 구성에 `startup_method: input.startup_method.trim()` 추가, summary 문자열에 `방식 '${input.startup_method}'` 추가 |
| 11 | `useRoadmapJob.ts` | `RoadmapIntakePayload` 타입에 `startup_method: string` 추가 |

---

### 3.9 0-B-3: 퍼지 매칭 모드 (BE, 2일)

**파일**: `app-backend/app/features/roadmaps/application/llm_personalizer.py`

**변경**: 0-A-3의 복구 전략 2와 3 사이에 **전략 2.5** 삽입

#### `_fuzzy_match_law_name(title, law_name_set, threshold=0.6)` 추가
- Jaccard 유사도(문자 집합 교집합/합집합) 기반
- 부분 문자열 포함 시 0.8 보너스
- 외부 의존성 없음 (difflib/fuzzywuzzy 미사용)
- threshold=0.6: 보수적 매칭으로 false positive 방지

#### `_fuzzy_match_file_key(file_url, file_key_set)` 추가
- basename 일치 (경로 끝 파일명) 또는 부분 문자열 포함으로 매칭

#### `_validate_and_repair_references()` 내 통합
- legal_basis: 전략 2 실패 → `_fuzzy_match_law_name()` 시도 → 매칭 성공 시 복구, 실패 시 전략 3(제거)
- documents: 전략 2 실패 → `_fuzzy_match_file_key()` 시도 → 매칭 성공 시 복구, 실패 시 전략 3(제거)

---

## 4. 검증 방법

### 4.1 백엔드
```bash
cd app-backend && .venv/bin/pytest -q                    # 전체 테스트 통과
cd app-backend && make migrate-verify                    # 모델 ↔ DB 스키마 일치
cd app-backend && black . && isort . --profile black     # 코드 포맷
```

### 4.2 프론트엔드
```bash
cd app-frontend && npm run lint                          # ESLint 통과
cd app-frontend && npm run build                         # 빌드 성공
npm run types:sync                                       # API 타입 동기화
```

### 4.3 수동 검증
1. 기존 로드맵의 LEGAL_BASIS/DOCUMENT 링크 클릭 → 404 없음 확인
2. 새 로드맵 생성 → 모든 source_url이 `/api/v1/actionkits/items/{id}` 패턴
3. source_url 없는 액션에서 "준비 중" 메시지 또는 actionkit 대안 링크 표시
4. 인테이크 폼에서 "창업 방식" 질문 정상 동작, 제안 칩 표시

### 4.4 신규 테스트 추가 (0-A-3, 0-B-3)
- `TestValidateAndRepairReferences`: 유효 참조 통과, item_id 기반 복구, law_name 기반 역매핑, 할루시네이션 제거
- `TestFuzzyMatching`: 정확 매칭, 부분 매칭, 매칭 실패 케이스

---

## 5. 전체 수정 파일 요약

| 파일 | 작업 | 난이도 |
|------|------|:------:|
| `llm_personalizer.py` | 0-A-3, 0-B-3: repair 로직, 퍼지 매칭, 프롬프트 수정 | ★★★ |
| `roadmap_generation_service.py` | 0-A-4, 0-B-1, 0-C-2: 다중파일, source_url 통일, payload | ★★☆ |
| `roadmap_repository.py` | 0-B-1, 0-C-2: source_url 해결, startup_method 전파 | ★☆☆ |
| `models/roadmap.py` | 0-C-3: startup_method 컬럼 | ★☆☆ |
| `api/v1/schemas.py` | 0-C-2: 요청 스키마 필드 추가 | ★☆☆ |
| `009_startup_method_and_source_urls.py` | 0-C-3+0-B-2: 마이그레이션 (신규) | ★★☆ |
| `TimelineStepItem.tsx` | 0-A-1, 0-A-2: 폴백 표시, 대안 링크 | ★★☆ |
| `RoadmapChatIntake.tsx` | 0-C-1: startup_method 질문 추가 | ★★☆ |
| `roadmap-constants.ts` | 0-C-1: 제안 칩 추가 | ★☆☆ |
| `RoadmapGenerationPanel.tsx` | 0-C-1: payload/summary 수정 | ★☆☆ |
| `useRoadmapJob.ts` | 0-C-1: 타입 확장 | ★☆☆ |
| `tests/` (확장) | 0-A-3, 0-B-3: 복구/퍼지 매칭 테스트 | ★★☆ |

---

## 6. 공수 총괄

| 작업 | 영역 | 공수 |
|------|:----:|:----:|
| 0-A-4 다중 파일 매핑 | BE | 0.5일 |
| 0-A-3 참조 자동 복구 | BE | 2일 |
| 0-A-1 FE 폴백 표시 | FE | 0.5일 |
| 0-A-2 FE 대안 링크 | FE | 1일 |
| 0-B-1 source_url 통일 | BE | 1일 |
| 0-B-2 DB 기존 데이터 복구 | DB | 0.5일 |
| 0-B-3 퍼지 매칭 | BE | 2일 |
| 0-C-1 FE 인테이크 폼 | FE | 1일 |
| 0-C-2 BE 파이프라인 전파 | BE | 0.5일 |
| 0-C-3 DB 모델 + 마이그레이션 | DB | 0.5일 |
| **합계** | | **9.5일 (약 2주)** |

### 병렬화 시

```
BE 개발자:  0-A-4(0.5d) → 0-A-3(2d) → 0-B-1(1d) → 0-C-3+0-B-2(0.5d) → 0-C-2(0.5d) → 0-B-3(2d) = 6.5일
FE 개발자:  0-A-1(0.5d) → 0-A-2(1d) → ── 대기 ── → 0-C-1(1d)                                    = 2.5일

총 elapsed: 약 7-8일 (1.5주)
```

---

## 7. 리스크 및 완화 전략

| 리스크 | 영향도 | 완화 전략 |
|--------|:------:|----------|
| 퍼지 매칭 false positive | ★★★ | 보수적 threshold=0.6, 포괄적 로깅, 테스트 커버리지 |
| 마이그레이션 source_url 덮어쓰기 (복구 불가) | ★★☆ | 기존 값이 이미 비정상; 새 패턴이 결정적이므로 허용 |
| FE 0-C-1 → BE 0-C-2 배포 순서 역전 | ★★★★ | BE 먼저 배포 필수. `GenerationPayload`가 `startup_method` 모르면 crash |
| SQLite 테스트에서 마이그레이션 SQL 미실행 | ★☆☆ | 테스트 DB는 `create_all()` 사용, 마이그레이션 불필요 |
| `all_file_urls`로 metadata_json 크기 증가 | ★☆☆ | 대부분 아이템당 1-3개 파일, JSON 증가 미미 |
