# docs/plans/ — 기획 + 구현 문서 통합 관리

## 구조

```
plans/
├── active/          # 진행 중인 작업
│   └── {topic}/
│       ├── PLAN-{topic}.md          # 기획 (What/Why) — 범위, 목표, 완료 기준
│       ├── {topic}-tasks.md         # 구현 (How) — 태스크 체크리스트
│       └── {topic}-context.md       # 구현 (How) — 설계 결정, 컨텍스트
├── reports/         # 독립 리서치 보고서 (PLAN과 무관)
│   └── REPORT-*.md
└── done/            # 완료 아카이브 (폴더째 이동)
```

## 분류 기준

- `진행중`: 구현/검증/운영 반영이 남아 있는 문서
- `완료`: 목표 기능이 반영되고 기본 검증(테스트/빌드/린트 등)을 통과한 문서
- `보류`: 우선순위에서 제외된 문서(파일 상단에 `Status: On Hold` 표기)

## 운영 규칙

1. `/dev-docs` 커맨드로 `active/{topic}/` 하위에 3파일 세트(plan + tasks + context) 생성
2. 독립 리서치 보고서는 `reports/`에 `REPORT-<topic>.md`로 작성
3. 작업 완료 시 `active/{topic}/` 폴더를 통째로 `done/`으로 이동
4. 완료된 REPORT도 `done/`으로 이동 (단일 아카이브 규칙)
5. 완료 이동 시 커밋 메시지에 `docs: archive completed plan` 문구 포함
6. 보류 문서는 이동하지 않고 상태만 명시
7. 재활성화 시 `done/`에서 `active/`로 이동하고 `Status: Reopened` 명시

## 파일 네이밍

- 계획: `PLAN-<topic>.md`
- 보고서: `REPORT-<topic>.md`
- 영문 + 케밥케이스, 파일명 버전 접미사(`_v2`) 지양

## 파일 역할 분리

- **PLAN 파일**: 기획 개요 — 범위, 목표, 완료 기준, 기술 조사
- **tasks/context 파일**: 구현 상세 — 설계, 태스크 추적, 컨텍스트
- PLAN 파일에 구현 상세를 작성하지 않는다 (별도 tasks/context 파일 사용)
