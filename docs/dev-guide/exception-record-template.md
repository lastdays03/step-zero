# Exception Record Template

프로젝트 표준에서 벗어나는 예외를 기록하는 양식. `decisions.md`에 1줄 요약 후, 상세가 필요하면 이 양식으로 별도 기록한다.

## 양식

```markdown
### [날짜] 예외 제목

- **표준**: 원래 적용되어야 할 규칙/패턴
- **예외 내용**: 실제로 다르게 구현한 부분
- **사유**: 예외를 적용한 이유
- **영향 범위**: 영향받는 파일/모듈
- **복귀 조건**: 표준으로 돌아갈 수 있는 조건 (없으면 "영구 예외")
```

## 기록 위치

- 1줄 요약: `docs/context/decisions.md` (날짜 | 결정 | 근거)
- 상세 기록: 해당 기능의 계획 문서 또는 `docs/dev-guide/` 내 별도 파일

## 기존 예외 사례

| 날짜 | 예외 | 사유 |
|------|------|------|
| 2026-03-02 | FK CASCADE를 Alembic에서만 정의 | SQLModel sa_column_kwargs 미지원 |
| 2026-03-02 | TemplateResolver를 try-except로 감싸 호출 | 기존 테스트 mock session 호환성 |
