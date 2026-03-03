# Roadmap Quality Improvement & Business Type Expansion Plan v2

> Last Updated: 2026-02-25
> 고도화: 에이전트 팀 분석 결과 통합 (plan-leader, plan-reviewer, backend-architect, frontend-ux-analyst)

## Executive Summary

현재 로드맵 생성 시스템은 **휴게음식점** 업종에서만 어느 정도 품질이 나오고, 그 외 업종에서는
"근거 보강 필요" fallback이 빈번하게 발생한다. 벡터DB에 **식품위생법 중심 47개 문서**만
적재되어 있어, 비음식 업종은 지원이 불가능한 상태이다.

### v1 대비 주요 변경 사항

| 항목 | v1 | v2 |
|---|---|---|
| Phase 구조 | 3 Phase | **5 Phase** (Phase 0 + Wave 분리) |
| 업종 확장 | 6개 동시 | **2개씩 3 Wave** + 품질 게이트 |
| 리스크 | 5개 | **11개** (환각, 법률 유효성 등 추가) |
| 성공 지표 | 5개 | **8개** (환각률, 검색정밀도, 응답시간 추가) |
| 신규 태스크 | - | P0-1, P1-5, Quick Win 3건 추가 |
| 롤백 전략 | 없음 | **Phase별 롤백 방안 정의** |
| 보안 | 미고려 | **Prompt Injection 대응 포함** |

---

## Current State Analysis

### DB 분석 결과 (2026-02-25)

| 항목 | 수치 |
|---|---|
| 총 로드맵 | 5개 (휴게음식점 4, 일반음식점 1) |
| 벡터DB 고유 문서 | 47개 (laws 22 + kits 25) |
| "근거 보강 필요" 발생 | **16건** (전체 LEGAL_BASIS 75건 중 21%) |
| 휴게음식점 fallback | 14건 (68건 중 20%) |
| 일반음식점 fallback | 2건 (7건 중 29%) |
| LEGAL_BASIS source_url 보유율 | 휴게음식점 79%, 일반음식점 71% |
| generation_mode | **전체 RAG (37건), ACTIONKIT_RAG 0건** |
| correctness (평가) | **0.30** (10건 중 7건 0점) |
| faithfulness (평가) | 0.62 |
| hit_rate@3 (평가) | 0.86 |

### 핵심 문제점 (v2 보완)

1. **"근거 보강 필요" 발생 패턴** - 비법률 단계(마케팅/인테리어/메뉴개발)에서 집중 발생
2. **업종 범위 제한** - 식품위생법 중심, 비음식 업종 지원 불가
3. **ACTIONKIT_RAG 미활성** - generation_mode가 전부 RAG, ActionKit 매칭이 임계값(3건) 미달
4. **LLM 환각** - `_validate_references()`가 debug 로깅만 수행, 환각된 법령명이 사용자에게 노출
5. **Prompt Injection 취약** - `validate_generation_input()`에서 사용자 입력이 RAG 프롬프트에 직접 삽입
6. **validate의 RAG 의존** - validation마다 LLM 호출 → 비용 발생 + 비결정적

---

## Implementation Plan (v2 - 5 Phase)

### Phase 0: Baseline 측정 (1일) - 신규

> "측정 없이 개선 없다" - 모든 개선 전에 정량적 baseline 확보

#### P0-1. 품질 평가 스크립트 + Baseline 측정 [S]
- (기존 P1-4를 Phase 0으로 앞당김)
- `scripts/eval_roadmap_quality.py` 작성
  - 업종별 fallback 비율 (법률 단계 / 비법률 단계 분리)
  - source_url 커버리지 (업종별)
  - 단계별 평균 액션 수
  - generation_mode 분포
  - retrieval precision@3 baseline
- JSON 리포트 출력 + baseline 수치 기록
- **AC**: 스크립트 실행 → JSON 리포트 생성, 최소 포함 항목: fallback_rate, source_url_coverage, generation_mode_distribution, avg_actions_per_step
- **의존**: 없음

#### P0-2. 품질 메타데이터 태깅 + DB Migration [S]
- (기존 P1-3를 Phase 0으로 앞당김)
- `roadmap_step_details` 테이블에 품질 메타 컬럼 추가 (Alembic migration)
  - `source_count: Integer, nullable=True` - 사용된 ActionKit 항목 수
  - `has_fallback: Boolean, nullable=True` - fallback 사용 여부
  - `mapping_source: String, nullable=True` - actionkit_direct / rag / fallback
- 모든 nullable → 무중단 마이그레이션 가능
- Alembic downgrade 스크립트 반드시 동반 작성
- **AC**: migration 적용 + 새 로드맵 생성 시 자동 기록 + downgrade 테스트 통과
- **의존**: 없음

---

### Phase 1: Quick Win - 품질 안정화 (2-3일)

> 기존 음식점 업종의 fallback 제거 + ACTIONKIT_RAG 활성화

#### P1-1. 비법률 단계 fallback 로직 개선 [M]
- `_fallback_detail()` / `_generate_phase_detail_with_retry()` / `llm_personalizer._fallback_from_facts()` 3곳 수정
- 단계 성격 분류 매핑 추가:
  - 법률필수: 인허가, 소방, 영업신고, 세무신고
  - 비법률: 마케팅, 인테리어, 메뉴개발, 오픈준비, 홍보, 매장설비, 상품관리, 쇼핑몰구축, 결제시스템
- 비법률 단계 → LEGAL_BASIS에 "법적 근거 불필요 - 실무 단계" + 실용 체크리스트 생성
- **주의**: "인테리어"에도 건축법/소방법 관련 요건이 있을 수 있으므로 분류 기준 검증 필요
- **AC**: 비법률 단계에서 "근거 보강 필요" 0건 + 법률 단계 분류 정확도 테스트 통과
- **AC 보완**: "법률 단계 한정 fallback ≤ 5%" 별도 추적 (지표 조작 방지)
- **의존**: 없음

#### P1-2. ActionKit Matcher 검색 쿼리 개선 [M] (S→M 상향)
- 현재: `"{business_type} {location} 창업 인허가"` 고정 쿼리 (actionkit_matcher.py:82)
- 개선: 업종별 추가 키워드 매핑 + 다중 쿼리 전략
  - BUSINESS_TYPE_KEYWORDS 딕셔너리 (업종→키워드 리스트)
  - 최대 3개 쿼리 → `asyncio.gather` 병렬 실행 → 중복 제거
- **성능 트레이드오프**: 벡터 검색 1회→3회, 병렬화로 ~1.5배 증가 예상
- **AC**: retrieval precision baseline 대비 향상 (P0-1 baseline 기준), ACTIONKIT_RAG mode 발생 확인
- **의존**: P0-1 (baseline 수치)

#### P1-5. ACTIONKIT_RAG 미활성 원인 분석 + 해소 [M] - 신규
- 현재 ACTIONKIT_RAG 0건: ActionKit 매칭이 `_MIN_ACTIONKIT_MATCHES=3` 미달
- 원인 분석: match() 쿼리 품질? 벡터 검색 임계값? item_titles 추출 로직?
- 해소 방안: 임계값 조정 / 쿼리 개선(P1-2 연계) / 매칭 로직 개선
- **AC**: 기존 음식점 업종에서 ACTIONKIT_RAG mode로 생성 성공 1건 이상
- **의존**: P1-2 (쿼리 개선 후)

#### P1-QW. Quick Win FE 수정 3건 [XS] - 신규
- **QW-1**: `TimelinePhaseCard.tsx:89` - COMPLETED expanded 초기값 `false`로 변경 (1줄)
- **QW-2**: EmptyHero/ChatIntake SUGGESTIONS 통합 → 공유 상수 `roadmap-constants.ts` 추출
- **QW-3**: validate 에러 reason 활용 → ChatIntake와 GenerationPanel 간 중복 에러 처리 통합
- **AC**: 각 수정사항 적용 + 빌드 통과
- **의존**: 없음 (즉시 실행 가능, Phase 0과 병렬)

#### P3-2. Fallback UX 개선 [S] (Phase 3에서 앞당김)
- P1-1과 동시 진행 가능 (FE 작업)
- LEGAL_BASIS 렌더링 분기: 정상 vs fallback
  - 비법률 단계: "이 단계는 법적 절차가 아닌 실무 단계입니다" (파란 안내 카드)
  - 법률 단계 fallback: "추가 법률 근거 확인이 필요합니다" (노란 경고 카드)
- source_url 부재 시 국가법령정보센터 검색 링크 생성
- **AC**: "근거 보강 필요" 텍스트가 사용자에게 0건 노출 (정량)
- **의존**: P1-1 (비법률 분류 기준), P0-2 (has_fallback 메타데이터)

---

### Phase 2A: 업종 확장 Wave 1 (5일) - 파일럿

> 기존 법률 활용 가능한 2개 업종으로 파이프라인 전체 검증

#### 대상 업종 (Wave 1)
| 업종 | 핵심 법률 | 선정 근거 |
|---|---|---|
| 식품제조가공업 | 식품위생법 확장 (기존 chapter-2) | 난이도 低, 기존 벡터 활용 |
| 통신판매업 | 전자상거래법, 통신판매업 신고 | 수요 높음 |

#### P2A-1. Wave 1 업종 법률 매핑 [S]
- 2개 업종의 필요 법률 문서 목록 확정 (최소 3개/업종)
- 법령 유효성 확인 (폐지 법률 아닌지)
- **AC**: 업종별 법률 문서 목록 + 법령 유효성 확인 완료
- **의존**: 없음 (Phase 1과 병렬 시작 가능!)

#### P2A-2. Wave 1 법률 문서 수집 + 벡터 적재 [L]
- 국가법령정보센터에서 법률/시행령/시행규칙 수집
- 벡터 메타데이터에 `target_business_types` 필드 추가 (업종 필터링용)
- 벡터 메타데이터에 `effective_date`, `last_verified_date` 추가
- `file_pipeline` 활용, 업종별 태그로 적재 (롤백 시 해당 업종만 삭제 가능)
- **AC**: 업종당 3개+ 법률 문서 적재 + similarity search top-3에 해당 업종 문서 1건 이상 포함
- **의존**: P2A-1

#### P2A-3. Wave 1 매핑/Validate/쿼리 확장 [M]
- CATEGORY_TO_PHASE 매핑 2개 업종 추가
- validate 프롬프트 + _fallback_validation() 확장
- 업종별 검색 키워드 전략 추가
- **AC**: 2개 업종 입력 시 valid=true + ActionKit 매칭 3건 이상 + 로드맵 생성 성공
- **의존**: P2A-2

#### 품질 게이트 (Wave 1 → Wave 2 진입 조건)
- [ ] Wave 1 업종 fallback 비율 < 10%
- [ ] Wave 1 업종 ActionKit 매칭 ≥ 3건
- [ ] Wave 1 업종 로드맵 생성 성공
- [ ] 기존 업종(음식점) hit_rate@3 ≥ 0.85 유지 (regression 방지)
- [ ] 교차 업종 오염 테스트 통과 (미용업 검색 시 식품위생법 미포함)

---

### Phase 2B: 업종 확장 Wave 2 (5일)

> Wave 1 검증 완료 후 추가 2개 업종

#### 대상 업종 (Wave 2)
| 업종 | 핵심 법률 | 비고 |
|---|---|---|
| 미용업 | 공중위생관리법 | 1인 창업 수요 높음 |
| 일반소매업 | 유통산업발전법 | 편의점/소매점 |

#### P2B-1~3. (P2A와 동일 구조로 반복)
- **게이트 조건**: Wave 1과 동일

---

### Phase 2C: 업종 확장 Wave 3 (5일)

> 규제 복잡도 높은 업종

#### 대상 업종 (Wave 3)
| 업종 | 핵심 법률 | 비고 |
|---|---|---|
| 학원업 | 학원법 | 규제 복잡 |
| 숙박업 | 공중위생관리법 + 관광진흥법 | 2개 법률 교차 |

#### P2C-1~3. (P2A와 동일 구조로 반복)
- **게이트 조건**: Wave 1과 동일

---

### Phase 3: Ops + 모니터링 (3-5일, Phase 2A 완료 후 시작 가능)

#### P3-1. 프론트엔드 업종 선택 가이드 [M]
- RoadmapChatIntake의 SUGGESTIONS를 2-tier로 분리:
  - Tier 1 "지원 업종" (초록색 뱃지): 검증 완료 업종
  - Tier 2 "곧 지원 예정" (회색 칩): 다음 Wave 업종
- 업종 목록을 API 엔드포인트에서 동적 로드 (`/api/v1/roadmaps/supported-business-types`)
- 미지원 업종 입력 시 구체적 안내: "'{입력값}'은 현재 미지원입니다. 지원 업종: [칩 목록]"
- EmptyHero 추천 검색어 클릭 → ChatIntake로 전환 + 자동 입력
- **AC**: 지원 업종 동적 표시 + 미지원 업종 안내 + 모바일 반응형
- **의존**: P2A-1 (업종 목록 확정)

#### P3-3. 로드맵 품질 대시보드 [L]
- `/ops/roadmap-quality` 페이지 (기존 ops 패턴 준수)
- 상단 KPI 카드 4개: 총 로드맵 수, 평균 Fallback 비율, source_url 커버리지, 지원 업종 수
- 차트 4개:
  1. 업종별 Fallback 비율 (수평 바, 목표선 5%)
  2. 생성 성공률 시계열 (generation_mode 별)
  3. 단계별 평균 액션 수 (비법률 vs 법률 구분)
  4. 로드맵 품질 상세 테이블 (정렬/필터)
- 백엔드 API 4개: summary, by-business-type, timeline, details
- **AC**: /ops/roadmap-quality 접속 + KPI 카드 + 차트 4개 렌더링 + 업종 필터
- **의존**: P0-2 (품질 메타 컬럼), P0-1 (평가 스크립트)

#### P3-4. 골든 데이터셋 확장 [M]
- 완료된 Wave의 업종부터 점진적 추가 (업종당 3건+)
- tier4 E2E 테스트에 업종 다양성 반영
- 교차 업종 오염 테스트 포함
- **AC**: 업종당 3건+ 골든 데이터 + 평가 통과 (legal_basis_accuracy ≥ 0.6)
- **의존**: P2A-2 (법률 문서 적재)

---

## Risk Assessment (v2 - 11개)

### 기존 리스크 (보완)

| # | 리스크 | 영향 | 확률 | 완화 방안 |
|---|---|---|---|---|
| R1 | 법률 문서 저작권 이슈 | 높음 | 낮음 | 국가법령정보센터는 공공데이터, CC BY 확인 |
| R2 | 새 업종 품질 불안정 | 높음 | 중간 | **Wave별 품질 게이트** + 점진적 오픈 |
| R3 | 벡터DB 용량/정밀도 저하 | 중간 | 중간 | 업종별 메타데이터 필터링, pgvector 인덱스 검토 |
| R4 | LLM 비용 증가 | 중간 | 낮음 | ActionKit 직접 매핑 우선, validate 화이트리스트 1차 |
| R5 | validate 오탐 | 중간 | 중간 | 화이트리스트 기반 → DB/config 외부화 |

### 신규 리스크

| # | 리스크 | 영향 | 확률 | 완화 방안 |
|---|---|---|---|---|
| R6 | **LLM 환각 (Hallucination)** | **높음** | **높음** | `_validate_references()` strict mode 도입, 환각 감지 시 항목 제거/경고 |
| R7 | **업종 간 법률 충돌/혼합** | 중간 | 중간 | 벡터 메타데이터 `target_business_types` + 검색 후 업종 필터링 |
| R8 | **법률 문서 시간적 유효성** | 높음 | 중간 | `effective_date`, `last_verified_date` 메타데이터 + 주기적 검증 |
| R9 | **Prompt Injection** | 높음 | 낮음 | 입력값 sanitization 레이어 추가, structured output 모드 |
| R10 | **동시 생성 Rate Limit** | 중간 | 중간 | retry with exponential backoff, API 호출 모니터링 |
| R11 | **FE-BE API 계약 미정의** | 중간 | 높음 | P1-1/P0-2 변경 시 API 응답 스키마 문서화 선행 |

---

## Success Metrics (v2 - 8개)

| 지표 | 현재 | Phase 1 목표 | Phase 2 목표 | 비고 |
|---|---|---|---|---|
| 법률 단계 fallback 비율 | ~5% (추정) | ≤ 5% | ≤ 5% | **법률 단계 한정** (지표 조작 방지) |
| 전체 fallback 비율 | 21% | ≤ 10% | ≤ 10% | 비법률 "법적 근거 불필요" 포함 |
| LEGAL_BASIS source_url 보유율 | 79% | ≥ 90% | ≥ 85% (기존), ≥ 70% (신규) | 업종별 분리 추적 |
| 지원 업종 수 | 2 | 2 | 8+ | 업종당 최소 품질 기준 충족 필요 |
| 로드맵 생성 성공률 | 100% | 100% | ≥ 95% | 실패 시 재시도 UX 포함 |
| **환각률** (신규) | 미측정 | baseline 측정 | ≤ 5% | 환각된 법령 인용 비율 |
| **검색 정밀도** (신규) | hit_rate 0.86 | ≥ 0.85 유지 | ≥ 0.85 유지 | 문서 확장 후 regression 방지 |
| **응답 시간** (신규) | 미측정 | baseline 측정 | P95 ≤ 30초 | 로드맵 생성 시간 |

---

## Dependency Map (v2 최적화)

```
[즉시 시작 가능 - 최대 병렬화]
├── P0-1: 품질 평가 스크립트 + Baseline ← 독립
├── P0-2: 품질 메타 Migration ← 독립
├── P1-QW: Quick Win FE 3건 ← 독립
└── P2A-1: Wave 1 업종 법률 매핑 ← 독립 (리서치, Phase 1과 동시!)

[P0 완료 후]
├── P1-1: 비법률 fallback 개선 ← P0-2
├── P1-2: ActionKit 쿼리 개선 ← P0-1 (baseline)
└── P3-2: Fallback UX 개선 ← P0-2 + P1-1과 동시 (FE)

[P1-1, P1-2 완료 후]
├── Phase 1 효과 측정 (P0-1 스크립트 재실행)
└── P1-5: ACTIONKIT_RAG 미활성 해소 ← P1-2

[P2A-1 + Phase 1 완료 후]
├── P2A-2: Wave 1 법률 문서 적재
├── P2A-3: Wave 1 매핑/Validate/쿼리
└── P3-1: 업종 선택 가이드 (FE) ← P2A-1

[Wave 1 게이트 통과 후]
├── P2B: Wave 2 (미용업 + 소매업)
├── P3-3: 품질 대시보드 ← P0-2
└── P3-4: 골든 데이터셋 확장 (Wave 1 업종부터)

[Wave 2 게이트 통과 후]
└── P2C: Wave 3 (학원업 + 숙박업)
```

**핵심 최적화**: P2A-1(업종 선정)은 순수 리서치이므로 Phase 1과 **동시 시작** → 전체 일정 3-5일 단축

---

## Rollback Strategy (신규)

| Phase | 시나리오 | 롤백 방법 |
|---|---|---|
| P0-2 | DB migration 실패 | Alembic downgrade 스크립트 (컬럼 추가만이므로 리스크 낮음) |
| P1-1 | 비법률 분류 오류 → 법적 근거 누락 | NON_LEGAL_PHASES 상수에서 해당 키워드 제거 (즉시 복구) |
| P1-2 | 다중 쿼리로 성능 저하 | BUSINESS_TYPE_KEYWORDS를 빈 dict로 설정 → 기존 단일 쿼리 복구 |
| P2A-2 | 새 문서가 검색 정밀도 악화 | 업종별 태그로 적재 → 문제 업종 벡터만 삭제 |
| P2A-3 | validate 오탐 | 화이트리스트를 DB/config 외부화 → 즉시 업종 제거 |
| P3-1 | UX 문제 | Feature flag로 기존 UI 복원 |
| P3-3 | 대시보드 에러 | ops 라우팅에서 메뉴 비활성화 |

---

## Technical Debt Resolution (신규)

| 부채 | 심각도 | 해소 Phase | 방법 |
|---|---|---|---|
| `_fallback_detail()` 하드코딩 | 중간 | P1-1 | NON_LEGAL_PHASES를 Enum/Config으로 외부화 |
| `validate` RAG 의존 (매번 LLM 호출) | 높음 | P2A-3 | 화이트리스트 1차 → LLM 2차 fallback |
| `run_in_threadpool` 사용 | 낮음 | Phase 1 | `ainvoke()` async native로 전환 |
| `CATEGORY_TO_PHASE` 하드코딩 | 중간 | P2A-3 | 업종→카테고리→페이즈 3단계 매핑 또는 config 분리 |
| `_fallback_validation()` 정규화 한계 | 중간 | P2A-3 | 매핑 테이블 DB/config 외부화 |
| 평가 체계 단편화 | 중간 | P3-4 | 로드맵 전용 평가 tier 정비, CI 통합 |

---

## Timeline (v2)

| Phase | 예상 기간 | 우선순위 | 비고 |
|---|---|---|---|
| Phase 0: Baseline | 1일 | **즉시** | P2A-1과 병렬 시작 |
| Phase 1: Quick Win | 2-3일 | Phase 0 완료 후 | P1-QW는 Phase 0과 병렬 |
| Phase 2A: Wave 1 | 5일 | Phase 1 완료 후 | 파일럿 (식품제조 + 통신판매) |
| Phase 2B: Wave 2 | 5일 | Gate 통과 후 | 미용업 + 소매업 |
| Phase 2C: Wave 3 | 5일 | Gate 통과 후 | 학원업 + 숙박업 |
| Phase 3: Ops | 3-5일 | Phase 2A 완료 후 | 2A와 일부 병렬 가능 |

**총 예상**: Phase 0~1 (4일) + Phase 2A (5일) + Phase 2B (5일) + Phase 2C (5일) + Phase 3 (5일, 병렬)
실질적으로 **~20-25일** (v1의 ~14-20일 대비 증가하나, 품질 게이트로 리스크 대폭 감소)

---

## Code-Level Implementation Notes

### 수정 대상 파일 요약

| 파일 | 수정 사항 | Phase |
|---|---|---|
| `roadmap_generation_service.py:387-403` | `_fallback_detail()` 비법률 분기 | P1-1 |
| `roadmap_generation_service.py:351` | `_generate_phase_detail_with_retry()` 비법률 힌트 | P1-1 |
| `llm_personalizer.py:383` | `_fallback_from_facts()` 비법률 처리 | P1-1 |
| `actionkit_matcher.py:82` | 다중 쿼리 전략 | P1-2 |
| `actionkit_matcher.py:126` | `run_in_threadpool` → async | P1-2 |
| `actionkit_matcher.py:28-41` | CATEGORY_TO_PHASE 확장 | P2A-3 |
| `roadmap_generation_service.py:121` | Prompt injection sanitization | P1-1 |
| `roadmap_generation_service.py:422` | `_fallback_validation()` 확장 | P2A-3 |
| `models/roadmap.py:56-68` | RoadmapStepDetail 품질 메타 필드 | P0-2 |
| `roadmap_repository.py` | `create_steps_with_details()` 메타 주입 | P0-2 |
| `TimelinePhaseCard.tsx:89` | COMPLETED expanded 초기값 | P1-QW |
| `RoadmapChatIntake.tsx:76-82` | SUGGESTIONS 통합 | P1-QW |
| `TimelineStepItem.tsx:136-211` | LEGAL_BASIS fallback 분기 | P3-2 |
| `RoadmapGenerationPanel.tsx:128-132` | validate 에러 구체화 | P1-QW |
| `RoadmapEmptyHero.tsx:13` | SUGGESTIONS 통합 | P1-QW |
