# Roadmap Quality Improvement - Tasks

> Last Updated: 2026-02-25

## Phase 1: 기존 업종 품질 안정화

### P1-1. 비법률 단계 fallback 로직 개선 [M] ✅ (2026-02-26)
- [x] 단계 성격 분류 매핑 정의 (법률필수 vs 비법률)
- [x] `_fallback_detail()` 수정: 7개 phase별 전문 템플릿 (세무, 인사, 정책자금, 법률준비, 준비, 인허가, 운영준비)
- [x] `llm_personalizer._fallback_from_facts()` 수정: 업종명 반영
- [x] 메타데이터 자동 기록: has_fallback, mapping_source, source_count
- [x] 테스트: 63 passed
- **결과**: fallback 시 phase별 5개+ 체크리스트, 실제 법령 근거, 업종별 위험요소 포함

### P1-2. ActionKit Matcher 검색 쿼리 개선 [S] ✅ (2026-02-26)
- [x] BUSINESS_QUERY_TEMPLATES: 10개 업종별 특화 키워드 매핑
- [x] _build_queries(): 다중 쿼리 생성 (base + 업종특화 3개 = 4쿼리)
- [x] _multi_query_search(): asyncio.gather 병렬 벡터 검색 + 결과 병합
- [x] 로깅 강화 (쿼리 수, 개별 결과 수, 병합 결과)
- [x] 테스트: 82 passed, 4 skipped
- **결과**: 업종별 다중 쿼리 전략 + 병렬 검색

### P1-3. generation_mode별 품질 태깅 [S] ✅ (2026-02-26)
- [x] Alembic migration `ea3b65f32267` 생성 (source_count, has_fallback, mapping_source)
- [x] `_personalized_to_steps_payload()`에서 메타데이터 자동 기록
- [x] `_fallback_detail()`에서 `has_fallback=True, mapping_source='fallback'` 설정
- [x] 정상 매칭: `has_fallback=False, mapping_source='actionkit_direct'/'rag'`
- **결과**: P0-2(스키마) + P1-1(기록로직)에서 통합 구현됨. DB 적용은 `alembic upgrade head` 필요

### P1-4. 기존 로드맵 품질 평가 스크립트 [S] ✅ (2026-02-26)
- [x] `scripts/eval_roadmap_quality.py` 작성
- [x] 5개 지표: fallback_rate, source_url_coverage, generation_mode_distribution, avg_actions_per_step, retrieval_precision_at_3
- [x] CLI: --json, --output, --help
- [x] RoadmapSnapshot 클래스로 N+1 없이 효율적 로딩
- **결과**: `python -m scripts.eval_roadmap_quality --json` → JSON 리포트

---

## Phase 2: 비음식 업종 법률 문서 확장

### P2-1. 우선 확장 업종 선정 및 법률 매핑 [M]
- [ ] 6개 우선 업종 확정
  - 통신판매업 (온라인쇼핑몰): 전자상거래법, 통신판매업 신고
  - 미용업: 공중위생관리법
  - 일반소매업: 유통산업발전법
  - 학원업: 학원법
  - 숙박업: 공중위생관리법, 관광진흥법
  - 식품제조가공업: 식품위생법 확장
- [ ] 업종별 필요 법률 문서 목록 작성 (최소 3개/업종)
- [ ] 업종별 핵심 인허가 절차 정리
- **AC**: 업종별 필요 법률 문서 목록 확정 문서 작성
- **의존**: 없음

### P2-2. 법률 문서 수집 및 ActionKit 적재 [XL]
- [ ] 국가법령정보센터에서 법률/시행령/시행규칙 수집
  - 전자상거래법 관련 (3건+)
  - 공중위생관리법 관련 (3건+)
  - 유통산업발전법 관련 (3건+)
  - 학원법 관련 (3건+)
  - 관광진흥법 관련 (3건+)
  - 식품제조가공업 관련 (3건+)
- [ ] ActionKit 도메인 확장: `laws/chapter-7`~ (업종별)
- [ ] 벡터DB 청킹 + 임베딩 적재 (`file_pipeline` 활용)
- [ ] 적재 결과 검증 (벡터 검색 테스트)
- **AC**: 업종당 최소 3개 법률 문서 + 벡터 적재 완료
- **의존**: P2-1

### P2-3. 업종별 카테고리→페이즈 매핑 확장 [M]
- [ ] `CATEGORY_TO_PHASE` 매핑에 새 업종 카테고리 추가
- [ ] 업종별 기본 페이즈 템플릿 정의
  - 통신판매: 사업자등록→통신판매신고→쇼핑몰구축→결제시스템→세무
  - 미용업: 입지→위생교육→영업신고→시설기준→세무→인사
  - 소매업: 입지→사업자등록→매장설비→상품관리→세무→인사
  - 학원업: 입지→학원등록→강사자격→시설기준→세무
  - 숙박업: 입지→사업자등록→영업신고→시설기준→소방→세무
  - 식품제조: 시설확보→제조허가→식품위생→세무→인사
- [ ] 업종별 페이즈 순서 검증
- **AC**: 6개 업종 페이즈 템플릿 정의 완료
- **의존**: P2-1

### P2-4. Validate 프롬프트 업종 목록 업데이트 [S]
- [ ] `validate_generation_input()` 프롬프트에 지원 업종 목록 추가
- [ ] `_fallback_validation()` 매핑 확장 (카페→휴게음식점 외 추가)
  - 온라인쇼핑몰/인터넷쇼핑몰 → 통신판매업
  - 헤어샵/미장원 → 미용업
  - 편의점/마트 → 일반소매업
  - 학원/교습소 → 학원업
  - 모텔/펜션/게스트하우스 → 숙박업
- [ ] 새 업종 입력 테스트
- **AC**: 새 업종 입력 시 `valid=true` + 정규화 성공
- **의존**: P2-2

### P2-5. ActionKit Matcher 업종별 쿼리 전략 [M]
- [ ] 업종에 따라 다른 검색 키워드 전략 매핑
  - 통신판매업 → "전자상거래 통신판매 신고"
  - 미용업 → "공중위생 미용업 신고"
  - 소매업 → "유통산업 소매 사업자등록"
  - 학원업 → "학원 등록 설립"
  - 숙박업 → "숙박업 영업신고 공중위생"
- [ ] `match()` 메서드에 업종별 쿼리 분기 로직 추가
- [ ] 새 업종별 ActionKit 매칭 결과 검증 (3건 이상)
- **AC**: 새 업종에서 ActionKit 매칭 3건 이상
- **의존**: P2-2, P2-3

---

## Phase 3: UX 개선 + 모니터링

### P3-1. 프론트엔드 업종 선택 가이드 [M]
- [ ] RoadmapChatIntake에서 지원 업종 목록 표시 (카드/칩 형태)
- [ ] 미지원 업종 입력 시 안내 메시지 표시
- [ ] 업종 선택 시 자동 입력 기능
- [ ] 반응형 디자인 적용
- **AC**: 지원 업종 목록 UI + 미지원 업종 안내
- **의존**: P2-1 (업종 목록 확정)

### P3-2. "근거 보강 필요" 대신 단계별 맞춤 안내 [S] ✅ (2026-02-26)
- [x] BE: RoadmapStepDetailResponse에 source_count, has_fallback, mapping_source 노출
- [x] FE: MappingSourceBadge 컴포넌트 (3종 배지)
  - actionkit_direct → 🟢 "법령 기반" (BookOpen)
  - rag → 🔵 "AI 분석" (Database)
  - fallback → 🟡 "일반 안내" (AlertCircle)
- [x] has_fallback=true ACTIVE step: amber 배경/테두리
- [x] source_url 없는 LEGAL_BASIS: "상세 법령 정보 준비 중" 안내
- [x] TypeScript 빌드 통과
- **결과**: mapping_source별 시각적 구분 완료

### P3-3. 로드맵 품질 대시보드 [L]
- [ ] `/ops/roadmap-quality` 페이지 생성
- [ ] 업종별 fallback 비율 차트
- [ ] 생성 성공률 차트
- [ ] 평균 액션 수/단계 차트
- [ ] 시계열 품질 추이
- [ ] API 엔드포인트: `/api/v1/ops/roadmap-quality`
- **AC**: /ops/roadmap-quality 페이지 + 차트
- **의존**: P1-3 (품질 메타 컬럼), P1-4 (평가 스크립트)

### P3-4. 골든 데이터셋 확장 [M]
- [ ] 새 업종별 평가 데이터셋 추가 (업종당 2건+)
  - 통신판매업 골든 데이터 2건
  - 미용업 골든 데이터 2건
  - 소매업 골든 데이터 2건
  - 학원업 골든 데이터 2건
  - 숙박업 골든 데이터 2건
  - 식품제조업 골든 데이터 2건
- [ ] tier4 E2E 테스트에 업종 다양성 반영
- [ ] 평가 실행 및 결과 검증
- **AC**: 업종당 2건 이상의 골든 데이터 + 평가 통과
- **의존**: P2-2 (법률 문서 적재)

---

## Progress Summary

| Phase | 총 태스크 | 완료 | 진행률 |
|---|---|---|---|
| Phase 1 (품질 안정화) | 4 | **4** | **100%** |
| Phase 2 (업종 확장) | 5 | 0 | 0% |
| Phase 3 (UX + 모니터링) | 4 | **2** | **50%** (P3-2 완료, P3-1/P3-3/P3-4 미착수) |
| **전체** | **13** | **6** | **46%** |

### ACTIONKIT_RAG 관련 추가 완료 사항 (P1-5, 계획서에 별도 미기재)
- _MIN_ACTIONKIT_MATCHES: 3→1 하향 (1개 매치만으로 ACTIONKIT_RAG 활성화)
- _MIN_RELEVANCE_SCORE = 0.2 필터링 추가
- 테스트: 39 passed, 기존 전부 통과
