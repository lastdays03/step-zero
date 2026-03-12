# Pre-Push 훅 성능 분석 및 개선 방안

> 작성일: 2026-03-12
> 상태: 핵심 개선 완료, 추가 최적화 검토
> 분석: Claude Code + Codex 교차 검증 후 구현 결과 반영

## 1. 요약

| 항목 | 변경 전 | 변경 후 |
|------|---------|---------|
| pre-push wall time | 27.16s | **5.61s** |
| backend smoke subset wall time | 6.29s | **3.30s** |
| backend 전체 회귀 wall time | 27.16s | **24.37s** |
| frontend lint wall time | 5.23s | 5.47s |

핵심은 pre-push의 병목이 프론트가 아니라 백엔드 전체 회귀 범위였다는 점이다. 훅을 smoke subset으로 축소하고 `LawApiClient` 테스트 sleep을 제거한 뒤, 체감 시간은 **27.16초 -> 5.61초**로 줄었다.

## 2. 구현 내용

### 2.1 pre-push 훅 범위 축소

`.husky/pre-push`를 아래 기준으로 변경했다.

```sh
cd app-backend && uv run pytest -q -x tests/services tests/repositories tests/integration -m "not slow and not requires_openai"
cd app-frontend && pnpm lint
```

- `tests/api`는 pre-push에서 제외
- backend smoke subset + frontend lint를 병렬 실행
- `-x`를 추가해 실패 시 첫 실패에서 중단

### 2.2 `law_api_client` 테스트 sleep 제거

`app-backend/tests/services/test_law_api_client.py`에 autouse fixture를 추가해 `_REQUEST_INTERVAL=0`을 패치했다.

```python
@pytest.fixture(autouse=True)
def no_rate_limit(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr("app.services.law_api_client._REQUEST_INTERVAL", 0)
```

프로덕션 코드(`app-backend/app/services/law_api_client.py`)는 변경하지 않았다.

### 2.3 문서 정비

아래 문서에 로컬 smoke 훅과 CI 전체 회귀의 역할 분리를 반영했다.

- `CLAUDE.md`
- `README.md`
- `docs/operations/project-operation-rules.md`

## 3. 실측 결과

### 3.1 현재 pre-push 경로

```text
./.husky/pre-push
-> 338 passed, 10 deselected
-> wall time: 5.61s
```

현재 pre-push 체감 시간은 **약 5.6초**이며, 이 시점에는 frontend lint가 사실상 상한선을 결정한다.

### 3.2 backend smoke subset 단독

```text
cd app-backend && uv run pytest -q -x tests/services tests/repositories tests/integration \
  -m "not slow and not requires_openai"

-> 338 passed, 10 deselected
-> wall time: 3.30s
```

초기 분석 단계의 6.29초 대비, `LawApiClient` 테스트 sleep 제거 후 smoke subset 자체도 더 빨라졌다.

### 3.3 backend 전체 회귀 유지

```text
cd app-backend && uv run pytest -q -m "not slow and not requires_openai"

-> 451 passed, 10 deselected
-> wall time: 24.37s
```

CI가 실행하는 전체 회귀 범위는 유지된다. `LawApiClient` 테스트 최적화로 전체 회귀 시간도 일부 감소했다.

### 3.4 `law_api_client` 테스트 확인

```text
cd app-backend && uv run pytest -q tests/services/test_law_api_client.py --durations=0

-> 26 passed in 0.40s
-> slowest item: 0.37s setup
-> 나머지 77 durations < 0.005s
```

즉, 느린 부분은 테스트 setup이고 개별 테스트 call 경로에는 더 이상 0.5초 sleep이 남아 있지 않다.

## 4. 원인 정리

### 4.1 근본 원인: 로컬 훅에 전체 회귀 스위트를 실은 설계

변경 전 pre-push는 backend `451개` 테스트를 그대로 실행했고, 동일한 명령이 CI에서도 다시 실행됐다.

- `.husky/pre-push:24`
- `app-backend/pyproject.toml:78`
- `.github/workflows/ci.yml:155`

이 구조 때문에 로컬 훅과 CI가 같은 회귀 범위를 중복 실행하고 있었다.

### 4.2 확정 병목: `LawApiClient` rate-limit sleep

```python
_REQUEST_INTERVAL = 0.5
await asyncio.sleep(_REQUEST_INTERVAL)
```

mock 테스트에도 sleep이 적용돼 약 2.5초를 낭비하고 있었다. 테스트에서만 패치해 제거했다.

### 4.3 후순위 후보: API 테스트 비용, fixture scope, SQLite 전략

`tests/api`가 현재 지연의 핵심 구간인 것은 맞지만, `client fixture scope`나 SQLite file DB를 1차 원인으로 단정할 근거는 부족하다.

- `client` scope 변경: A/B 계측 필요
- SQLite in-memory: 병렬화 도입 시 검토 가치 있음
- 현재 문제의 핵심 해법은 이미 범위 축소로 해결됨

## 5. 남은 후보 작업

| 우선순위 | 작업 | 상태 |
|----------|------|------|
| 1 | pre-push smoke subset 유지 | 완료 |
| 2 | `LawApiClient` 테스트 sleep 제거 | 완료 |
| 3 | `-x` fail-fast 적용 | 완료 |
| 4 | client fixture scope A/B 계측 | 미실행 |
| 5 | SQLite in-memory / xdist 검토 | 미실행 |

## 6. 결론

pre-push가 느린 이유는 테스트 인프라 자체보다 **로컬 훅의 검증 범위가 과도했던 설계**였다. 범위를 smoke subset으로 줄이고 확정 병목 하나를 제거하자, pre-push 체감 시간은 **27.16초 -> 5.61초**로 줄었다.

현재 구조는 다음과 같이 정리된다.

- 로컬 pre-push: backend smoke subset + frontend lint
- CI: backend 전체 회귀 + frontend lint/test/build

추가 최적화 여지는 남아 있지만, 이번 변경으로 개발 루프를 막던 핵심 문제는 해소됐다.
