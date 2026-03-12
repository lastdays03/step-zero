# Pre-Push 최적화 컨텍스트

> Last Updated: 2026-03-12

## 핵심 파일

| 파일 | 역할 | 변경 여부 |
|------|------|-----------|
| `.husky/pre-push` | pre-push 훅 (수정 대상) | **수정** |
| `app-backend/pyproject.toml` | pytest 설정 (addopts, markers) | 참조 |
| `.github/workflows/ci.yml` | CI 워크플로우 (전체 회귀 유지) | 참조 |
| `app-backend/tests/conftest.py` | 테스트 DB/fixture 설정 | Phase 3에서 검토 |
| `app-backend/tests/services/test_law_api_client.py` | sleep 패치 대상 | **수정** |
| `app-backend/app/services/law_api_client.py` | `_REQUEST_INTERVAL` 정의 | 참조 (변경 없음) |
| `CLAUDE.md` | Quality Gates 섹션 | **수정** |
| `README.md` | 훅/CI 역할 설명 | **수정** |
| `docs/operations/project-operation-rules.md` | 협업 규칙 문서 | **수정** |

## 분석 보고서

- `docs/plans/reports/REPORT-pre-push-performance.md` — 실측 데이터 및 원인 분석 전문

## 확정된 결정

1. **pre-push는 smoke subset만 실행한다** — `tests/services`, `tests/repositories`, `tests/integration` 디렉토리만 포함. `tests/api`는 CI 전담.
2. **CI는 전체 회귀를 유지한다** — `ci.yml`의 pytest 명령은 변경하지 않음.
3. **마커 기반(`smoke`)이 아닌 디렉토리 기반으로 범위를 나눈다** — 초기 도입 비용이 낮음.
4. **`_REQUEST_INTERVAL`은 테스트에서만 0으로 패치한다** — 프로덕션 코드 변경 없음.
5. **`-x` fail-fast를 pre-push에 포함한다** — 성공 경로 최적화가 아니라 실패 대기 시간 단축용 보조 옵션.

## 의존성

- Husky 훅 시스템 (루트 `package.json`의 `prepare` 스크립트)
- CI 워크플로우는 별도 변경 없이 기존 전체 회귀 유지

## 실측 데이터 (2026-03-12)

```
전체 pytest (451개):     24.37s
smoke subset (338개):     3.30s
pre-push 전체:            5.61s
프론트 lint:              5.47s
law_api_client 파일:      26 passed in 0.40s
```
