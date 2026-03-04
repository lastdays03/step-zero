# Planning Docs Management Rules

## 목적
- `docs/planning/`은 진행 중이거나 검토 중인 플랜 문서만 유지한다.
- 완료된 플랜은 `docs/planning/completed/`로 이동해 이력을 보관한다.

## 분류 기준
- `진행중`: 구현/검증/운영 반영이 남아 있는 플랜
- `완료`: 목표 기능이 반영되고 기본 검증(테스트/빌드/린트 등)을 통과한 플랜
- `보류`: 우선순위에서 제외된 플랜(파일 상단에 `Status: On Hold` 표기)

## 운영 규칙
1. 새 플랜은 `docs/planning/`에 작성한다.
2. 플랜이 완료되면 즉시 `docs/planning/completed/`로 이동한다.
3. 완료 이동 시 커밋 메시지에 `docs: archive completed plan` 문구를 포함한다.
4. 보류 플랜은 이동하지 않고 상태만 명시한다.
5. 완료 플랜을 재활성화할 경우 `docs/planning/`으로 다시 이동하고 `Status: Reopened`를 명시한다.

## 파일 네이밍 권장
- 계획: `PLAN-<topic>.md`
- 보고서: `REPORT-<topic>.md`
- 동일 주제 버전업 시 git 이력 활용 권장 (파일명 `_v2` 접미사 지양)

## docs/planning/ vs docs/dev/ 역할 구분

이 폴더는 **기획 문서(What/Why)**만 관리한다. 구현 상세는 `/dev-docs` 커맨드가 생성하는 `docs/dev/` 디렉토리에서 관리한다.

| | `docs/planning/` (이 폴더) | `docs/dev/` (`/dev-docs` 커맨드) |
|--|----------------------------|-----------------------------------|
| **내용** | 기획 개요 — 범위, 목표, 완료 기준 | 구현 상세 — 설계, 태스크 추적, 컨텍스트 |
| **작성 시점** | 프로젝트 착수 전 | `/dev-docs` 커맨드 실행 시 |
| **형식** | 단일 PLAN-*.md | 3파일 세트 (plan + tasks + context) |

**규칙**:
- PLAN 문서에 구현 상세(파일 맵, 태스크 체크리스트 등)를 작성하지 않는다
- PLAN 문서 상단에 `→ 구현 추적: docs/dev/active/{name}/` 참조 링크를 포함한다
- `docs/dev/active/*/plan.md` 상단에 `→ 기획: docs/planning/PLAN-*.md` 참조 링크를 포함한다
