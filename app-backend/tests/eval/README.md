# RAG 평가 테스트 (tests/eval)

실제 OpenAI API + PostgreSQL을 사용하는 RAG 품질 평가 테스트.
일반 `make test`에서는 **자동 제외**되며, 수동으로만 실행한다.

## 사전 요구사항

- `OPENAI_API_KEY` (실제 키, 더미 불가)
- PostgreSQL DATABASE_URL (pgvector 활성화, `law_vectors` 컬렉션 시드 완료)
- `pip install ragas datasets` (Tier 2 RAGAS 메트릭 사용 시)

## 실행 방법

```bash
cd app-backend

# 전체 eval (Tier 2 + Tier 3)
uv run pytest tests/eval -v -s

# Tier 2만 — 기본 RAG 품질 메트릭 (~5분, ~$2-5)
uv run pytest tests/eval/test_tier2_metrics.py -v -s

# Tier 3만 — 법률 도메인 전문 평가 (~15분, ~$15-25)
uv run pytest tests/eval/test_tier3_full.py -v -s
```

> `tests/eval` 경로를 직접 지정하면 `pyproject.toml`의 `--ignore=tests/eval` 설정을 우회한다.

## 티어 구조

| 티어 | 파일 | 내용 | 비용 | 시간 |
|------|------|------|------|------|
| Tier 2 | `test_tier2_metrics.py` | Hit Rate, Faithfulness, Answer Relevancy, Keyword Match, RAGAS | ~$2-5 | ~5분 |
| Tier 3 | `test_tier3_full.py` | 법률 정확성(GPT-4o), 법령 인용, OOS 거부, 응답 지연 | ~$15-25 | ~15분 |

## 실행 시점

- RAG 파이프라인 변경 후 (프롬프트, 검색 파라미터, 임베딩 모델 등)
- 릴리즈 전 회귀 검증
- 골든 데이터셋 갱신 후

## 결과 확인

평가 결과는 `tests/eval/results/`에 JSON으로 저장된다:
- `faithfulness.json` — Faithfulness 점수
- `correctness.json` — Answer Correctness 점수
- `legal_accuracy_full.json` — 법률 정확성 + 환각 사례
- `ragas_results.csv` — RAGAS 종합 메트릭
- `summary_report.json` — 전체 종합 리포트
