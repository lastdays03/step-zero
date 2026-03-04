# docs/ 디렉토리 가이드

## 폴더 역할

| 폴더 | 역할 | 갱신 빈도 |
|------|------|-----------|
| `context/` | 세션 운영 (상태/결정/핸드오프/규칙) | 매 세션 |
| `planning/` | 기획 문서 + 리서치 보고서 (PLAN-*.md, REPORT-*.md) | 프로젝트 착수/조사 시 |
| `planning/completed/` | 완료 문서 아카이브 | 기획/리서치 완료 시 이동 |
| `dev/` | 구현 계획 (How) — `/dev-docs`로 생성 | 구현 시작/완료 시 |
| `architecture/` | 시스템 아키텍처 설계 | 분기별 검증 |
| `operations/` | 팀 협업 프로세스 규칙 (Git, PR 등) | 규칙 변경 시 |
| `dev-guide/` | 개발자 가이드, 체크리스트, 기능 가이드 | 필요 시 |
| `archive/` | 역할 완료 문서 보관 (brainstorm, feedback 등) | 정리 시 |

## docs/planning/ vs docs/dev/ 역할 구분

프로젝트 문서는 목적에 따라 두 곳에 분리 관리한다:

| | `docs/planning/` | `docs/dev/` (`/dev-docs` 커맨드) |
|--|-------------------|-----------------------------------|
| **내용** | 기획 (What/Why) — 범위, 목표, 완료 기준 | 구현 (How) — 상세 설계, 태스크 추적 |
| **작성 시점** | 프로젝트 착수 전 | `/dev-docs` 커맨드 실행 시 |
| **형식** | 단일 `PLAN-*.md` | 3파일 세트 (plan + tasks + context) |
| **진행 추적** | 없음 | 체크리스트 (`/dev-docs-update`로 갱신) |
| **완료 시** | `planning/completed/`로 이동 | `dev/done/`으로 이동 |

**중복 금지**: 같은 프로젝트에 대해 양쪽에 동일 내용을 작성하지 않는다.
- `docs/planning/PLAN-*.md` → 기획 개요만 유지 (구현 상세 X)
- `docs/dev/active/*/plan.md` → 구현 상세만 유지 (기획 배경은 PLAN 참조 링크)

## 네이밍 규칙

- 계획: `PLAN-<topic>.md`
- 보고서: `REPORT-<topic>.md`
- 가이드: `<topic>-guide.md` 또는 자유 형식
- 영문 + 케밥케이스 권장
- 파일명 버전 접미사(`_v2`) 지양 — git 이력 활용

## 참조

- 세션 시작 복구: `context/README.md`
- 계획 문서 관리: `planning/README.md`
- 구현 계획 생성: `/dev-docs` 커맨드
- 컨텍스트 보존: `/dev-docs-update` 커맨드
