# docs/ 디렉토리 가이드

## 폴더 역할

| 폴더 | 역할 | 갱신 빈도 |
|------|------|-----------|
| `context/` | 세션 운영 (상태/결정/핸드오프/규칙) | 매 세션 |
| `plans/active/` | 진행 중 기획 + 구현 문서 (`/dev-docs`로 생성) | 구현 시작/완료 시 |
| `plans/reports/` | 독립 리서치 보고서 (REPORT-*.md) | 조사 시 |
| `plans/done/` | 완료 아카이브 (폴더째 이동) | 작업 완료 시 |
| `architecture/` | 시스템 아키텍처 설계 | 분기별 검증 |
| `operations/` | 팀 협업 프로세스 규칙 (Git, PR 등) | 규칙 변경 시 |
| `dev-guide/` | 개발자 가이드, 체크리스트, 기능 가이드 | 필요 시 |
| `archive/` | 역할 완료 문서 보관 (brainstorm, feedback 등) | 정리 시 |

## docs/plans/ 구조

```
plans/
├── active/          # 진행 중인 작업
│   └── {topic}/
│       ├── PLAN-{topic}.md          # 기획 (What/Why)
│       ├── {topic}-tasks.md         # 구현 (How) — 태스크 체크리스트
│       └── {topic}-context.md       # 구현 (How) — 설계 결정
├── reports/         # 독립 리서치 보고서
│   └── REPORT-*.md
└── done/            # 완료 아카이브
```

- PLAN 파일에 구현 상세를 작성하지 않는다 (별도 tasks/context 파일 사용)
- 완료 시 `active/{topic}/` 폴더를 통째로 `done/`으로 이동

## 네이밍 규칙

- 계획: `PLAN-<topic>.md`
- 보고서: `REPORT-<topic>.md`
- 가이드: `<topic>-guide.md` 또는 자유 형식
- 영문 + 케밥케이스 권장
- 파일명 버전 접미사(`_v2`) 지양 — git 이력 활용

## 참조

- 세션 시작 복구: `context/README.md`
- 계획 문서 관리: `plans/README.md`
- 구현 계획 생성: `/dev-docs` 커맨드
- 컨텍스트 보존: `/dev-docs-update` 커맨드
