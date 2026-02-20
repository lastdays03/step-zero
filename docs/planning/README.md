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
- `PLAN-<topic>.md` 형식 유지
- 동일 주제 버전업 시 `PLAN-<topic>-v2.md` 사용
