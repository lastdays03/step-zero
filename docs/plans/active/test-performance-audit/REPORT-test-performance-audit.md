# REPORT: 테스트 성능 감사 보고서

> 작성일: 2026-03-06 | 브랜치: feature/0-r2-storage-migration

---

## 1. 요약 (Executive Summary)

| 항목 | 백엔드 | 프론트엔드 |
|------|--------|------------|
| **총 실행 시간** | 287초 (4분 47초) | 2.8초 |
| **테스트 수** | 420개 | 22개 |
| **Pass** | 341 | 22 |
| **Fail** | 77 | 0 |
| **Error** | 1 | 0 |
| **Skip** | 1 | 0 |
| **핵심 병목** | `tests/eval/` RAG 품질 검사 (291초, 90%) | act() 경고 (기능 영향 없음) |

**결론**: 백엔드 테스트의 90%를 차지하는 `tests/eval/` (RAG 품질 평가)가 일반 `make test`에 포함되어 있어 개발 루프가 비정상적으로 느리다. 프론트엔드는 시간 문제 없으나 테스트 커버리지와 품질 경고 개선이 필요하다.

---

## 2. 백엔드 상세 분석

### 2.1 시간 분포

```
전체: 287초 (420 tests)
├── tests/eval/         291초 (16 tests) ← 90% 병목
│   ├── tier2_metrics    ~93초
│   └── tier3_full      ~198초
├── tests/api/          ~20초 (다수)
├── tests/services/     ~6초
└── tests/repositories/ ~3초
```

eval을 제외하면 **29초** (404 tests) — 정상 범위.

### 2.2 eval 테스트 병목 원인

| 순위 | 테스트 | 시간 | 원인 |
|------|--------|------|------|
| 1 | `test_legal_accuracy_full` (call) | 107초 | GPT-4o로 전체 법률 케이스 LLM-as-Judge |
| 2 | `test_legal_accuracy_full` (setup) | 77초 | 전체 법률 케이스 RAG 응답 생성 (DB + OpenAI) |
| 3 | `test_hit_rate` (setup) | 69초 | tier2 `evaluated_cases` fixture (RAG 응답 생성) |
| 4 | `test_answer_correctness_batch` | 17초 | GPT-4o-mini LLM-as-Judge |
| 5 | `test_faithfulness_batch` | 7초 | GPT-4o-mini LLM-as-Judge |
| 6 | `test_refusal_on_out_of_scope` | 5초 | 실제 RAG 호출 |
| 7 | `test_answer_relevancy_batch` | 5초 | GPT-4o-mini LLM-as-Judge |

**핵심 문제**: eval 테스트 파일에 `pytest.mark.eval`, `pytest.mark.slow` 마커가 있지만, `pyproject.toml`에 기본 제외 설정(`addopts`)이 없어 `pytest -q` 시 자동 수집된다.

### 2.3 실패 테스트 분석 (77 fail + 1 error)

#### 그룹 A: R2 스토리지 마이그레이션 관련 (58건)

현재 브랜치(`feature/0-r2-storage-migration`)의 진행 중 작업으로 인한 예상된 실패:

- `tests/api/` 대부분 — storage backend 변경으로 503 응답
- `tests/repositories/test_roadmap_chat_repository.py` — DB 스키마 변경 영향
- `tests/services/test_template_resolver.py` (9건) — 모듈 import 변경

#### 그룹 B: `requires_openai` 마커 문제 (10건)

```
tests/services/test_safety_qa.py::TestLLMSafetyValidation (10건 전부 FAIL)
```

**원인**: `conftest.py`에서 `OPENAI_API_KEY`를 더미값(`sk-test-dummy-key-for-ci`)으로 설정 → fixture 내부의 `pytest.skip()` 조건문(`if not os.environ.get("OPENAI_API_KEY")`)을 통과 → 실제 API 호출 시도 → 인증 실패.

`@pytest.mark.requires_openai` 마커는 등록만 되어 있고, **자동 skip 로직이 없다**.

#### 그룹 C: eval 에러 (1건)

```
tests/eval/test_tier2_metrics.py::TestEndToEndQuality::test_chat_routing_e2e → ERROR
```

`chat_service` fixture 의존성에서 `ChatService` import 실패.

### 2.4 미등록 마커 경고

```
PytestUnknownMarkWarning: Unknown pytest.mark.eval
PytestUnknownMarkWarning: Unknown pytest.mark.slow
PytestUnknownMarkWarning: Unknown pytest.mark.full_eval
```

`pyproject.toml`의 `markers`에 `eval`, `slow`, `full_eval`이 등록되지 않았다.

---

## 3. 프론트엔드 상세 분석

### 3.1 테스트 현황

| Suite | 파일 | Tests | 시간 | 상태 |
|-------|------|-------|------|------|
| roadmap-utils | `roadmap/__tests__/roadmap-utils.test.ts` | 14 | ~10ms | PASS |
| LoginForm | `auth/__tests__/LoginForm.test.tsx` | 2 | ~170ms | PASS |
| Dashboard | `dashboard/__tests__/Dashboard.test.tsx` | 6 | ~355ms | PASS |
| **합계** | **3 suites** | **22** | **2.8초** | **ALL PASS** |

### 3.2 시간 문제: 없음

프론트엔드 테스트는 2.8초로 정상 범위. Jest 초기화 오버헤드(~1.5초)를 감안하면 실질 테스트 시간은 ~1초.

### 3.3 품질 경고: `act()` Warning (10회 반복)

```
Warning: An update to DashboardView inside a test was not wrapped in act(...)
  at setRoadmapDetail (DashboardView.tsx:57)
  at setDocumentsLoading (DashboardView.tsx:67)
```

**원인**: `DashboardView` 컴포넌트가 마운트 시 `apiClient.get()`을 비동기 호출하고, 응답 도착 후 `setRoadmapDetail` / `setDocumentsLoading` state 업데이트가 테스트의 `act()` 범위 밖에서 발생.

**영향**: 기능 동작에는 영향 없으나, 테스트 출력이 경고 메시지로 오염되어 가독성 저하. 5개 테스트에서 각 2회씩 총 10회 출력.

**해결 방안**: 비동기 state 업데이트가 있는 테스트에서 `waitFor` 또는 `findBy*`로 비동기 완료를 대기하거나, mock이 동기적으로 resolve되도록 조정.

### 3.4 테스트 커버리지 관찰

| Feature | 테스트 유무 | 비고 |
|---------|------------|------|
| auth | O | LoginForm만 (2건) |
| dashboard | O | DashboardView (6건) |
| roadmap | O | 유틸 함수만 (14건), 컴포넌트 미테스트 |
| actionkit | **X** | |
| growth-club | **X** | |
| rag/chat | **X** | |
| ops | **X** | |
| profile | **X** | |
| shared | **X** | |

22개 feature 중 3개만 테스트 존재. 핵심 사용자 플로우(로드맵 생성, 챗봇, 액션킷)의 프론트엔드 테스트가 부재.

---

## 4. 종합 문제 목록 및 우선순위

### P0 — 즉시 수정 (개발 루프 직접 영향)

| # | 문제 | 영향 | 해결 방안 |
|---|------|------|-----------|
| 1 | eval 테스트가 `make test`에 포함 | 테스트 287초 → 29초로 단축 가능 | `pyproject.toml`에 `addopts = "--ignore=tests/eval"` 추가 |
| 2 | `requires_openai` 마커가 skip 미작동 | 10개 테스트 항상 FAIL | `conftest.py`에 `pytest_collection_modifyitems` 자동 skip 추가 |

### P1 — 단기 개선 (테스트 품질)

| # | 문제 | 영향 | 해결 방안 |
|---|------|------|-----------|
| 3 | 미등록 pytest 마커 3개 | 경고 56개 | `pyproject.toml` markers에 `eval`, `slow`, `full_eval` 등록 |
| 4 | Dashboard 테스트 act() 경고 | 로그 오염 (10회) | mock의 비동기 resolve를 `waitFor` 패턴으로 변경 |

### P2 — 중기 개선 (인프라)

| # | 문제 | 영향 | 해결 방안 |
|---|------|------|-----------|
| 5 | eval 실행 명령이 문서화 안 됨 | 개발자 혼란 | CLAUDE.md, Makefile에 `make test-eval` 추가 |
| 6 | 프론트엔드 테스트 커버리지 부족 | 22개 feature 중 3개만 | 핵심 플로우(로드맵, 챗봇) 테스트 추가 |

---

## 5. 권장 구성 변경

### 5.1 `app-backend/pyproject.toml`

```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
addopts = "--ignore=tests/eval"
markers = [
    "requires_openai: tests that require OPENAI_API_KEY to be set",
    "eval: RAG evaluation tests (expensive, requires real OpenAI API + PostgreSQL)",
    "slow: slow-running tests",
    "full_eval: full evaluation suite (tier 3)",
]
```

### 5.2 `app-backend/tests/conftest.py` 추가

```python
def pytest_collection_modifyitems(config, items):
    """requires_openai 마커가 있는 테스트를 더미 키 환경에서 자동 skip."""
    import os
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if api_key.startswith("sk-test") or not api_key:
        skip_marker = pytest.mark.skip(reason="requires real OPENAI_API_KEY (current key is dummy)")
        for item in items:
            if "requires_openai" in item.keywords:
                item.add_marker(skip_marker)
```

### 5.3 `app-backend/Makefile` 추가 타겟

```makefile
test-eval:    ## RAG 평가 테스트 (OpenAI API + PostgreSQL 필요)
	uv run pytest tests/eval -v -s

test-eval-t2: ## Tier 2 평가만 (~5분, ~$2-5)
	uv run pytest tests/eval/test_tier2_metrics.py -v -s

test-eval-t3: ## Tier 3 전체 평가 (~15분, ~$15-25)
	uv run pytest tests/eval/test_tier3_full.py -v -s
```

---

## 6. 적용 후 예상 효과

| 지표 | 현재 | 적용 후 |
|------|------|---------|
| `make test` 실행 시간 | 287초 | **29초** (-90%) |
| 테스트 실패 수 | 77 fail | **~58 fail** (R2 작업 완료 시 0) |
| 경고 수 | 56 | **~0** |
| eval 실행 방법 | `make test`에 혼입 | `make test-eval`로 명시적 실행 |
