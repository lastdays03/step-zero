# StepZero Linear + GitHub 운영 규칙

## 1. 목적
- 개발 진행 상태를 PR 이벤트 기반으로 자동 반영한다.
- 이슈, 브랜치, PR, 머지 이력을 한 흐름으로 관리한다.
- `feature/* -> develop -> main` Git-Flow를 일관되게 유지한다.

## 2. 적용 범위
- 저장소: `step-zero`
- 태스크 관리: Linear
- 코드 리뷰/머지: GitHub
- 기본 브랜치 전략: `feature/* -> develop -> main`

## 3. 핵심 원칙
1. 모든 개발 작업은 Linear 이슈에서 시작한다.
2. 이슈 하나는 작업 단위 하나로 유지한다.
3. PR 본문에 `Fixes <ISSUE-ID>`를 반드시 포함한다.
4. 머지 후 이슈 상태는 `Done`이어야 한다.

## 4. 이슈/브랜치/PR 규칙

### 4.1 이슈 키
- 팀 키 기반 이슈 ID를 사용한다. 예: `LAS-123`
- 이슈 ID는 PR 본문에 반드시 명시한다.

### 4.2 브랜치 네이밍
- 패턴: `feature/<issue-number>-<short-slug>`
- 예: `feature/123-profile-edit-api`
- 운영 기준은 숫자형 브랜치 네이밍을 기본으로 한다.

### 4.3 커밋 메시지
- Conventional Commits를 사용한다.
- 예: `feat: add profile edit API`

### 4.4 PR 작성
- PR 제목/본문은 한국어로 작성한다.
- PR 본문 최소 항목:
- 요약
- 변경 사항
- 검증 결과
- `Fixes <ISSUE-ID>`

## 5. 상태(Workflow) 운영
- 기본 상태: `Backlog -> Todo -> In Progress -> In Review -> Done`
- 자동화 원칙:
- PR Open/Ready 시 `In Progress` 또는 `In Review`
- PR Merge 시 `Done`
- 머지 후 `Done` 미전환 시 팀 Workflow 자동화 규칙을 점검한다.

## 6. 마일스톤 운영 규칙
1. 기본 구조
- 프로젝트마다 주간 단위 마일스톤 2개를 생성한다.
- `Wn 구현 완료`
- `Wn 운영/문서`

2. 배정 기준
- 코드 구현/버그 수정/성능 개선: `Wn 구현 완료`
- 문서/CI/운영 규칙/협업 설정: `Wn 운영/문서`

3. 주간 루틴
- 월요일: 대상 이슈를 마일스톤에 배정
- 주중: 상태 및 PR 자동연동으로 진행
- 금요일: 마일스톤 완료율 확인, 미완료 이슈 이월

## 7. 사이클 운영 규칙
1. 권장 설정
- `Enable cycles`: ON
- `Each cycle lasts`: `1 week`
- `Starting day of the week`: `Monday`
- `Cooldowns after each cycle`: `0`
- `Upcoming cycles`: `4~6`
- `Auto-add active issues to current cycle`: ON

2. 병행 원칙
- 사이클은 기간 관리, 마일스톤은 성격 관리로 사용한다.
- 동일 이슈에 사이클 + 마일스톤을 함께 지정할 수 있다.

3. 운영 기준
- 사이클 시작 시 `Todo` 중심으로 배정한다.
- 긴급 이슈 중간 투입 시 코멘트로 사유를 남긴다.
- 미완료 이슈는 다음 사이클로 이월한다.

## 8. 품질/검증 기준
- Backend 변경 완료 전: `cd app-backend && uv run pytest -q`
- Frontend 변경 완료 전: `cd app-frontend && pnpm lint`


## 9. 운영 점검 체크리스트
1. 개발 시작 전 Linear 이슈 존재
2. 브랜치 네이밍 규칙 준수
3. PR 본문에 `Fixes <ISSUE-ID>` 포함
4. PR 생성 후 이슈 attachment/상태 자동 전환 확인
5. PR 머지 후 `Done` 전환 확인

## 10. 문서 정합성 기준
- 본 문서는 "운영 정책" 문서다.
- 실제 실행 순서와 예시는 `docs/operations/linear-github-workflow.md`를 기준으로 한다.
- 규칙 변경 시 두 문서를 함께 갱신한다.
