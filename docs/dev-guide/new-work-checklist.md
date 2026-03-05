# New Work Checklist

새 기능/수정 작업 시작 전 확인 항목.

## 시작 전

- [ ] `docs/context/` 4개 파일 읽기 (dev-status → decisions → handoff → ops-rules)
- [ ] `dev-status.md`의 `Next 3 Actions`에서 작업 선택
- [ ] 관련 계획 문서 확인 (`docs/planning/` 또는 `dev/active/`)
- [ ] 작업 브랜치 확인/생성 (`feature/<issue-number>-<slug>`)
- [ ] `git fetch origin && git pull --rebase` 동기화

## 작업 중

- [ ] 변경 범위에 맞는 테스트 작성/실행
- [ ] 구조적 결정 발생 시 `decisions.md`에 기록
- [ ] 표준 예외 발생 시 `docs/dev-guide/exception-record-template.md` 양식으로 기록

## 완료 시

- [ ] Quality Gates 통과 (`uv run pytest -q` / `pnpm lint`)
- [ ] `dev-status.md` 갱신 (상태, Next 3 Actions)
- [ ] PR 작성 (한국어 제목/본문, Conventional Commits)
