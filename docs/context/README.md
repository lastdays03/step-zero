# Context Memory (Lightweight)

목표: PC를 옮겨도 최소 비용으로 작업 맥락을 복구한다.

## 파일 구성
- `NOW.md`: 현재 상태, 이번 작업 목표, 다음 3개 액션
- `DECISIONS.md`: 확정된 규칙/결정만 누적
- `HANDOFF.md`: 세션 종료 시점 요약

## 운영 규칙
- 로그 전체를 저장하지 않는다.
- 최신성과 간결성을 우선한다.
- 세션 시작:
1. `NOW.md`
2. `DECISIONS.md`
3. `HANDOFF.md`
순서로 읽고 바로 작업 시작
- 세션 진행 중 다른 PC로 이어서 작업(종료 없이):
1. 현재 PC 변경사항 커밋/푸시
2. 새 PC에서 `git fetch origin && git pull --rebase`
3. `NOW.md`와 `HANDOFF.md` 재확인
4. 차이가 있을 때만 `NOW.md`에 1~2줄 Sync Note 기록
- 세션 종료:
1. `HANDOFF.md` 갱신
2. 필요 시 `NOW.md` 정리
3. 코드 변경과 함께 커밋/푸시
- 트리거 규칙:
1. 사용자가 `핸드오프`, `마무리`, `종료`를 요청하면
2. `HANDOFF.md` 갱신 후 즉시 커밋/푸시까지 수행
3. 실패 시 원인을 보고하고 중단 상태를 명시

## 작성 기준
- `NOW.md`: 15줄 내외
- `DECISIONS.md`: 항목당 1~2줄
- `HANDOFF.md`: 6~12줄
