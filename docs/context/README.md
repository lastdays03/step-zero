# Context Memory (Lightweight)

목표: PC를 옮겨도 최소 비용으로 작업 맥락을 복구한다.

## 파일 구성
- `dev-status.md`: 개발 진행 상태(완료/진행/다음 액션)
- `ops-rules.md`: 운영/협업 규칙(핸드오프, 동기화, 브랜치/PR)
- `decisions.md`: 확정된 기술/구조 결정만 누적
- `handoff.md`: 세션 종료 시점 요약

## 운영 규칙
- 로그 전체를 저장하지 않는다.
- 최신성과 간결성을 우선한다.
- 세션 시작:
1. `dev-status.md`
2. `decisions.md`
3. `handoff.md`
4. `ops-rules.md`
순서로 읽고 바로 작업 시작
- 세션 진행 중 다른 PC로 이어서 작업(종료 없이):
1. 현재 PC 변경사항 커밋/푸시
2. 새 PC에서 `git fetch origin && git pull --rebase`
3. `dev-status.md`와 `handoff.md` 재확인
4. 차이가 있을 때만 `dev-status.md`에 1~2줄 Sync Note 기록
- 세션 종료:
1. `handoff.md` 갱신
2. 필요 시 `dev-status.md` 정리
3. 코드 변경과 함께 커밋/푸시
- 트리거 규칙:
1. 사용자가 `핸드오프`, `마무리`, `종료`를 요청하면
2. `handoff.md` 갱신 후 즉시 커밋/푸시까지 수행
3. 실패 시 원인을 보고하고 중단 상태를 명시

## 작성 기준
- `dev-status.md`: 15~25줄
- `ops-rules.md`: 20줄 내외
- `decisions.md`: 항목당 1~2줄
- `handoff.md`: 6~12줄
