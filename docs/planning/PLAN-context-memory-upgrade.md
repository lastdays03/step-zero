# PLAN: Context Memory Upgrade

## 진행 상태 (2026-02-15)
- [x] Phase 1 문서 구조 고정(README 단일 진입점 + 컨텍스트 4종 템플릿 정리)
- [ ] Phase 1 운영 검증(1주)
- [ ] Phase 2 Validation 착수
- [ ] Phase 3 Optional 검토

## 목표
- PC 변경 시 작업 맥락 복구 시간을 최소화한다.
- 과도한 기록 없이 경량 메모리 중심으로 운영한다.
- 필요 시 NotebookLM을 보조기억 장치로 확장한다.

## Phase 1 (Now): Lightweight Memory Only
- 범위:
1. `docs/context/dev-status.md`
2. `docs/context/ops-rules.md`
3. `docs/context/decisions.md`
4. `docs/context/handoff.md`
5. `docs/context/README.md`
- 운영:
1. 작업 중 `dev-status.md` 갱신
2. 운영 규칙 변경 시 `ops-rules.md` 갱신
3. 확정 사항은 `decisions.md` 반영
4. 세션 종료 시 `handoff.md` 갱신
- 성공 기준:
1. 다른 PC에서 10분 내 맥락 복구 가능
2. 1주간 운영 중 누락 없이 핸드오프 유지

### Phase 1 적용 메모 (2026-02-15)
- `docs/context/README.md`에 시작/종료 30초 체크리스트 추가
- `dev-status.md` 고정 섹션 템플릿 도입(상태/리스크/테스트/Sync Notes)
- `decisions.md`를 `날짜 | 결정 | 근거` 포맷으로 통일
- `handoff.md`/`ops-rules.md`를 트리거 기반 운영 형태로 정리

## Phase 2 (Validation)
- 기간: 1~2주
- 점검 항목:
1. 자주 빠지는 정보 유형(결정 근거/남은 리스크/테스트 상태)
2. 문서 유지 비용(작성 시간)
3. 실제 이어서 작업 성공률
- 산출:
1. 템플릿 경량화 또는 필드 보강
2. 작성 트리거 규칙 보정

## Phase 3 (Optional): NotebookLM Augmentation
- 목적: 회의록/기획서/아키텍처 원문 검색 성능 보강
- 원칙:
1. 실행 규칙의 진실 원천은 레포 문서(`AGENTS.md`, `docs/context/*`)
2. NotebookLM은 탐색/질의 보조 역할
- 도입 범위:
1. 소스 업로드: 운영규칙, 아키텍처, 기획서, 회의 메모
2. 질의 패턴: “결정 근거”, “관련 문서 찾기”, “과거 합의 재확인”
- 종료 기준:
1. 세션 재시작 시 추가 검색 시간이 실질적으로 단축
2. 문서 중복 관리 비용이 증가하지 않음

## 리스크
- 경량 문서가 오래되면 무용화
- 규칙 미준수 시 핸드오프 누락
- 외부 보조기억 도입 시 출처 단일화 실패 가능성

## 대응
- `마무리/종료` 트리거로 `handoff.md` 강제 갱신
- 주 1회 `dev-status.md`/`decisions.md` 정리
- 외부 도구 도입 시 “레포 문서 우선” 원칙 유지
