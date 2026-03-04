# StepZero Linear + GitHub 실전 워크플로우 가이드

## 1. 목적
- 개발 작업 상태를 사람 수동 업데이트가 아니라 PR 이벤트 기준으로 자동 반영한다.
- 이슈, 브랜치, PR, 머지 이력을 한 흐름으로 관리한다.
- `feature/* -> develop -> main` Git-Flow를 지키면서 운영한다.

## 2. 기본 원칙
- 모든 개발 작업은 Linear 이슈에서 시작한다.
- 이슈 하나는 작업 단위 하나로 유지한다.
- PR 본문에 반드시 `Fixes <ISSUE-ID>`를 포함한다.
- 배포 반영은 항상 `develop` 경유 후 `main`으로 진행한다.

## 3. 선행 설정
1. Linear에서 GitHub 통합 활성화
- `Settings > Features > Integrations > GitHub`

2. 팀 워크플로우 자동화 설정
- `Team settings > Workflow`에서 PR 이벤트별 상태 전환 규칙 설정
- 권장:
- PR Open/Ready: `In Progress` 또는 `In Review`
- PR Merged: `Done`

3. 개인 옵션(선택)
- `Settings > My account > Preferences > Behavior`
- `On git branch copy ...` 옵션은 없어도 연동 동작에 필수는 아니다.

## 4. 1건 처리 표준 절차
1. 이슈 생성/확정
- 상태: `Backlog` 또는 `Todo`
- 제목은 "결과물" 기준으로 작성

2. 브랜치 생성
- 패턴: `feature/<issue-number>-<short-slug>`
- 예: `feature/123-profile-edit-api`

3. 개발/커밋
- Conventional Commits 사용
- 예: `feat: add profile edit API`

4. PR 생성 (`feature/* -> develop`)
- PR 제목/본문은 한국어
- PR 본문에 필수 포함:
- 요약
- 변경 사항
- 검증 결과
- `Fixes LAS-123` 같은 이슈 연결 문구

5. 리뷰/수정
- 리뷰 반영 커밋을 같은 PR에 추가
- 필요하면 이슈 본문/체크리스트 업데이트

6. 머지
- 머지 후 Linear 이슈가 `Done`으로 자동 전환되는지 확인
- 미전환 시 팀 Workflow 자동화 규칙 점검

7. 정리
- 머지된 feature 브랜치 삭제
- 테스트성 PR/브랜치는 즉시 정리

## 5. 팀 데일리 운영 규칙
1. 작업 시작 전에 할 일
- 오늘 처리할 이슈만 `In Progress`로 이동
- `In Progress`인데 PR 없는 이슈가 오래 유지되지 않게 관리

2. PR 생성 후 확인
- 이슈에 PR attachment 생성 여부
- 이슈 상태 자동 전환 여부

3. 머지 후 확인
- 이슈 `Done` 전환
- 완료 시간(`completedAt`) 기록 여부

## 6. 실패 패턴과 대응
1. PR은 있는데 이슈가 안 연결됨
- PR 본문의 `Fixes <ISSUE-ID>` 형식 확인
- 이슈 ID 오타 확인

2. PR Open인데 상태가 안 바뀜
- 팀 Workflow의 PR 자동화 규칙 확인
- GitHub 통합 연결 상태 확인

3. Merge 후 Done 미전환
- `On merge -> Done` 규칙 존재 여부 확인
- PR이 실제로 `develop`에 머지되었는지 확인

## 7. 최소 운영 체크리스트
1. 개발 시작 전 Linear 이슈 존재
2. 브랜치명 규칙 준수 (`feature/<issue-number>-...`)
3. PR 본문 한국어 + `Fixes <ISSUE-ID>` 포함
4. PR 생성 후 Linear attachment 확인
5. PR 머지 후 이슈 `Done` 확인

## 8. 테스트로 확인된 현재 동작 (2026-02-14)
- PR 생성 시 Linear 이슈에 PR attachment 자동 생성됨
- PR Open 시 이슈 상태 자동 전환됨
- PR Merge 시 이슈가 `Done`으로 자동 전환됨
- 개인 `branch copy` 토글 없이도 위 동작은 정상 수행됨

## 9. 마일스톤 운영 규칙
1. 사용 목적
- 사이클을 아직 고정 운영하지 않거나 팀 규모가 작은 경우, 마일스톤으로 주간 단위를 먼저 관리한다.
- 이슈를 "이번 주 완료 범위"와 "운영/문서 작업"으로 분리해 회고를 단순화한다.

2. 마일스톤 생성 기준
- 프로젝트마다 주간 단위 마일스톤 2개를 기본 생성:
- `Wn 구현 완료`
- `Wn 운영/문서`
- 예: `W1 구현 완료`, `W1 운영/문서`

3. 이슈 연결 기준
- 코드 구현/버그 수정/성능 개선: `Wn 구현 완료`
- 문서/CI/협업 규칙/운영 점검: `Wn 운영/문서`
- 이슈 생성 시점 또는 스프린트 플래닝 시점에 반드시 마일스톤 지정

4. 주간 운영 루틴
1. 월요일
- 이번 주 대상 이슈를 정하고 마일스톤에 배정
- 이번 주 범위 밖 이슈는 `Backlog` 유지
2. 주중
- 이슈 상태와 PR 자동연동 중심으로 진행
- 상태는 `Todo -> In Progress -> In Review -> Done` 유지
3. 금요일
- 마일스톤별 완료율 확인
- 미완료 이슈는 다음 주 마일스톤으로 이동 후 사유 1줄 기록

5. 보드/리포트 확인 방법
- 프로젝트 이슈 뷰에서 `Group by Milestone`으로 주간 진행상황 확인
- 완료 점검 시 `Filter: Status = Done` + `Group by Milestone` 조합 사용
- 회고 시 "마일스톤별 완료/이월 개수"를 기본 지표로 사용

## 10. 사이클 운영 규칙
1. 사용 목적
- 팀의 주간 실행력을 일정하게 유지하고, 이월량을 추적한다.
- "이번 주 약속한 일"을 사이클 범위로 명확히 고정한다.

2. 권장 설정값
- `Enable cycles`: ON
- `Each cycle lasts`: `1 week`
- `Starting day of the week`: `Monday`
- `Cooldowns after each cycle`: `0`
- `Upcoming cycles`: `4~6`
- `Auto-add active issues to current cycle`: ON

3. 사이클과 마일스톤 병행 원칙
- 사이클은 "기간(언제)" 관리
- 마일스톤은 "성격(무엇)" 관리
- 같은 이슈에 사이클 + 마일스톤을 함께 지정해도 된다.

4. 이슈 배정 기준
- 사이클 시작 시 `Todo` 이슈만 사이클에 넣는다.
- 긴급 버그는 예외로 사이클 중간 추가 가능하되, 이유를 코멘트로 남긴다.
- 완료 불확실 이슈는 사이클에 넣지 않고 `Backlog` 유지

5. 주간 운영 루틴
1. 월요일
- 이번 사이클 목표 확정
- 사이클 대상 이슈 배정(과도하게 담지 않기)
2. 화~목
- PR 자동연동으로 상태 관리
- 병목 이슈(`In Progress` 장기 정체) 우선 해소
3. 금요일
- 사이클 완료율/이월 이슈 확인
- 이월 이슈는 다음 사이클로 이동 + 원인 기록

6. 운영 지표
- 사이클 완료율(`Done / committed`)
- 이월 개수
- 평균 리드타임(이슈 시작~완료)
- 리뷰 대기 시간(`In Review` 체류시간)
