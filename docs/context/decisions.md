# Decisions

## 기록 규칙
- 확정된 사항만 기록한다.
- 항목 형식은 `날짜 | 결정 | 근거`를 유지한다.

## Entries
- 2026-02-15 | Backend API HTTP 계층은 `app/api/v2/<feature>/<function>.py`로 운영 | API 모듈 경로 일관성 확보
- 2026-02-15 | Backend 비즈니스 계층은 `app/features/<feature>/{domain,application}`에 배치 | 기능별 경계 명확화
- 2026-02-15 | 운영콘솔 네이밍은 `ops`로 통일(`ops-console`, `ops_console` 금지) | 경로/용어 혼선 방지
- 2026-02-15 | Frontend 피처는 public entry(`index.ts`) 유지, 서버 컴포넌트에서 hook export 직접 import 금지 | 레이어 의존성 규칙 유지
- 2026-02-15 | 루트(`/`)는 랜딩 대신 `/dashboard`로 리다이렉트 | 기본 진입 동선 단순화
- 2026-02-15 | 관리자 기본 URL은 `/ops` 유지 | 운영 진입점 단일화
- 2026-02-15 | `핸드오프/마무리/종료` 요청 시 `handoff.md` 갱신 후 커밋/푸시까지 수행 | 세션 종료 누락 방지
- 2026-02-15 | Context memory 문서는 `README` 단일 진입점 + 고정 템플릿 섹션으로 운영 | PC 전환 시 복구 시간 단축
- 2026-02-15 | NotebookLM은 `공통 표준(L2)` + `프로젝트별 보조기억(L2)`의 이중 레이어로 운영하고, 실행 진실 원천은 레포 문서(L1)로 유지 | 표준 공통화와 프로젝트 상세기억을 동시에 확보하면서 충돌 리스크를 제어
