# Context: 테스트 성능 감사

> Last Updated: 2026-03-06

## Related Planning Doc

- `docs/dev/active/test-performance-audit/REPORT-test-performance-audit.md` — 감사 보고서 (분석 원본)

## Key Files

### 백엔드 — 이미 변경됨
| 파일 | 변경 내용 |
|------|-----------|
| `app-backend/pyproject.toml` | `addopts = "--ignore=tests/eval"` + 마커 3개 등록 |
| `app-backend/tests/conftest.py` | `pytest_collection_modifyitems` — requires_openai 자동 skip |
| `app-backend/tests/eval/README.md` | eval 수동 실행 가이드 신규 생성 |

### 백엔드 — 변경 예정
| 파일 | 변경 내용 |
|------|-----------|
| `app-backend/Makefile` | `test-eval`, `test-eval-t2`, `test-eval-t3` 타겟 추가 |
| `CLAUDE.md` | Quick Commands에 eval 테스트 명령 추가 |

### 프론트엔드 — 변경 예정
| 파일 | 변경 내용 |
|------|-----------|
| `app-frontend/src/features/dashboard/__tests__/Dashboard.test.tsx` | act() 경고 수정 |

## Key Decisions

| 결정 | 근거 |
|------|------|
| eval은 `--ignore`로 기본 제외 | 마커 기반 `-m "not eval"`보다 확실하고, 경로 직접 지정으로 우회 가능 |
| `pytest_collection_modifyitems`로 skip | conftest fixture 내부 skip은 더미 키에 의해 우회됨 |
| Makefile 타겟으로 eval 진입점 제공 | 개발자가 커맨드를 외울 필요 없이 `make test-eval`로 실행 |
| act() 경고는 `waitFor` 패턴으로 해결 | 테스트 로직 변경 없이 비동기 대기만 추가 |

## Dependencies

- Phase 1 (P0)은 독립적으로 완료 가능 — 외부 의존 없음
- Phase 2 (act() 수정)은 `@testing-library/react`의 `waitFor` 활용 — 이미 설치됨
- 현재 브랜치 `feature/0-r2-storage-migration`의 58건 FAIL은 R2 작업 완료 시 해소 (본 계획 범위 외)
