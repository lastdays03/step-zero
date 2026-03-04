# docs/dev/ — 구현 계획 (How)

`/dev-docs` 커맨드로 생성되는 구현 상세 문서를 관리한다.

## 구조

```
dev/
├── active/          # 진행 중인 작업
│   └── {task-name}/
│       ├── {task-name}-plan.md
│       ├── {task-name}-context.md
│       └── {task-name}-tasks.md
└── done/            # 완료된 작업 아카이브
```

## 기획과의 구분

- `docs/planning/` — 기획 (What/Why): 범위, 목표, 완료 기준
- `docs/dev/` — 구현 (How): 상세 설계, 태스크 추적

→ 기획: `docs/planning/PLAN-*.md` 참조
