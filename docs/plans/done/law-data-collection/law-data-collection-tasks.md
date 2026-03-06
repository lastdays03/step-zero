# 법률 자료 수집 전략 - 태스크 체크리스트

> Last Updated: 2026-02-26 (ActionKitItem 보강 태스크 추가)

## 상태 범례

- [ ] 미시작
- [x] 완료
- [>>] 진행 중
- [!!] 블로커
- [--] 건너뜀

## 진행 요약

| Phase | 총 태스크 | 완료 | 진행률 |
|---|---|---|---|
| Phase 0: API 등록 | 4 | 4 | 100% |
| Phase 1: 수집 스크립트 | 8 | **6** | **75%** |
| Phase 2: Wave 1 수집 | **7** | **7** | **100%** |
| Phase 3: Wave 2 수집 | 4 | 0 | 0% |
| Phase 4: Wave 3 수집 | 4 | 0 | 0% |
| Phase 5: ActionKit 큐레이션 | 6 | 0 | 0% |
| **전체** | **33** | **17** | **52%** |

---

## Phase 0: API 등록 및 환경 설정 (0.5일)

### P0-1. open.law.go.kr 회원가입 + OC 발급 [XS] ✅ (2026-02-26)
- [x] open.law.go.kr 접속하여 회원가입
- [x] OC (Open API Code) 발급 확인 (이메일 ID = OC)
  - OC = `lastdays03` (lastdays03@gmail.com)

### P0-2. 환경변수 및 설정 추가 [XS] ✅ (2026-02-26)
- [x] `app-backend/.env.local`에 `LAW_API_OC=lastdays03` 추가 (실제 키)
- [x] `app-backend/.env`에 `LAW_API_OC=` 추가 (기본 템플릿)
- [x] `app-backend/.env.example`에 `LAW_API_OC=` 추가
- [x] `app-backend/app/core/config.py`에 `LAW_API_OC: str | None = None` + `_normalize_optional_secret` 적용
  - 검증: `get_settings().LAW_API_OC` → `"lastdays03"`

### P0-3. API 연결 테스트 [XS] ✅ (2026-02-26)
- [x] curl로 식품위생법 검색 → HTTP 200 + JSON 3건 반환
  ```
  curl "http://www.law.go.kr/DRF/lawSearch.do?OC=lastdays03&target=law&type=JSON&query=식품위생법&display=3"
  ```
- [x] 응답 구조 확인: 법령일련번호(277149), 법령명한글(식품위생법), 시행일자(20251001)
  - 참고: 법령구분명(법률/대통령령/총리령), 소관부처명, 공포번호 등 포함

### P0-4. httpx 의존성 확인 [XS] ✅ (2026-02-26)
- [x] `pyproject.toml` dev deps에 `httpx>=0.26.0` 이미 존재
- [x] venv에 httpx v0.28.1 설치됨 확인

---

## Phase 1: 수집 스크립트 개발 (2~3일)

### P1-1. 국가법령정보센터 API 클라이언트 래퍼 [M] ✅ (2026-02-26)
- [x] Pydantic 모델 4종: LawSearchResult, LawFullText, LawArticle, AdminRuleResult (한글 alias)
- [x] LawApiClient 클래스: httpx.AsyncClient, async context manager
- [x] 4개 메서드: search_laws, get_law_full_text, get_law_articles, search_admin_rules
- [x] Rate limiting: asyncio.Semaphore(2) + 0.5초 간격
- [x] 에러 핸들링: LawApiError (타임아웃, HTTP, 파싱)
- [x] **실제 API 호출 시 발견된 버그 2건 수정**:
  - law_mst alias `법령MST` → `법령일련번호` 수정
  - target=jo 404 → target=law 내 조문단위 직접 파싱으로 변경
- [x] 테스트: 26 passed (test_law_api_client.py)

### P1-2. API 클라이언트 유닛 테스트 [S] ✅ (2026-02-26)
- [x] 26개 테스트 작성 (test_law_api_client.py)
- [x] 유틸 함수(4), 응답 모델(4), 초기화(2), API 메서드(6), 에러(3), Context Manager(2), 파싱(3), 쿼리빌더(2)

### P1-3. 업종별 법률 수집 설정 정의 [S] ✅ (2026-02-26)
- [x] `scripts/fetch_laws_config.py` 신규 생성
- [x] WAVE_CONFIG: 3 Wave, 6 업종, 9개 검색 쿼리
- [x] 헬퍼: get_wave_targets(), get_all_targets(), list_all_queries()

### P1-4. 법률 수집 CLI 스크립트 [L] ✅ (2026-02-26)
- [x] `scripts/fetch_laws.py` 신규 생성
- [x] CLI: --wave, --law, --list, --status, --dry-run, --force
- [x] 수집 플로우: API 검색→MST→본문+조문→.md 저장+_meta.json
- [x] hierarchy 필터링: 법률→법률, 시행령→대통령령, 시행규칙→총리령/부령
- [x] 검증: --list (9건), --status, --wave 1 --dry-run, --wave 1 (실행 성공)

### P1-5. LawDataSource API 구현체 (MolegApiSource) [M] ✅ (2026-02-26)
- [x] `law_fetcher.py`에 MolegApiSource(LawDataSource) 추가
- [x] .temp/rag/ 디렉토리의 .md + _meta.json 쌍을 LawData 객체로 반환
- [x] source_type=API, 메타데이터(law_id, effective_date, law_hierarchy 등) 포함
- [x] issubclass(MolegApiSource, LawDataSource) 확인됨

### P1-6. LLM 기반 조문 큐레이션 스크립트 [M]
- [ ] GPT-4에 법률 전문 + 업종 컨텍스트 입력하여 관련 조문 필터링:
  - [ ] 조문별 관련성 점수 (0~1) 산출 프롬프트 작성
  - [ ] 0.5 이상 조문만 추출
  - [ ] 추출 결과를 `{법령명}_curated.md`로 저장
- [ ] CLI 인터페이스:
  ```bash
  python -m scripts.curate_law_articles --business-type 통신판매업 --law 전자상거래법
  python -m scripts.curate_law_articles --wave 1  # Wave 1 전체 큐레이션
  ```
- [ ] 수동 검증 가이드 출력 (LLM이 선별한 조문 목록 + 관련성 점수)
  - File: `app-backend/scripts/curate_law_articles.py` (신규)
  - Details: LLM 큐레이션 결과는 수동 검증 전까지 "draft" 상태로 표시
  - Acceptance: 큐레이션 결과 파일 생성 + 관련성 점수 포함
  - Size: M (2~4h)
  - Dependencies: P1-4

### P1-7. seed_rag_vectors.py Wave별 인제스트 옵션 추가 [S] ✅ (2026-02-26)
- [x] `--curated` 옵션 추가: _curated.md 파일 직접 청킹+적재 (LLM ETL 없이)
- [x] `--dir` 옵션: 특정 디렉토리만 인제스트
- [x] 메타데이터: source_type="law_curated", target_business_types, law_name, law_hierarchy 자동 포함
- 참고: --wave 옵션 대신 --curated --dir 조합으로 구현됨

---

## Phase 2: Wave 1 데이터 수집 - 식품제조가공업 + 통신판매업 (2~3일)

### P2-1. Wave 1 법률 수집 실행 [M] ✅ (2026-02-26)
- [x] `python -m scripts.fetch_laws --wave 1` 실행 성공
- [x] 식품제조가공업: 식품위생법(171KB) + 시행령(85KB) + 시행규칙(135KB) ✅
- [x] 통신판매업: 전자상거래법(85KB) + 시행령(48KB) + 시행규칙(16KB) ✅
- [x] 총 12파일 (6 .md + 6 _meta.json)
- 미수집: 행정규칙 2건 (검색 결과 없음, 키워드 조정 필요)

### P2-2. Wave 1 관련 조문 큐레이션 [L] ✅ (2026-02-26)
- [x] 6개 _curated.md 파일 생성 (LLM 없이 수동 큐레이션)
- [x] 식품제조가공업: 식품위생법(15조문), 시행령(7조문), 시행규칙(9조문)
  - 핵심: 시설기준(36조), 영업허가/신고/등록(37~38조), HACCP(48조), 벌칙(93~101조)
- [x] 통신판매업: 전자상거래법(13조문), 시행령(9조문), 시행규칙(6조문)
  - 핵심: 통신판매업 신고(12조), 청약철회(17조), 소비자피해보상보험(24조)
- 방식: curate_law_articles.py 스크립트 대신 에이전트가 원문 기반으로 직접 큐레이션

### P2-3. Wave 1 벡터 적재 + ActionKitItem 자동 생성 [M] ✅ (2026-02-26)
- [x] `seed_rag_vectors.py --curated` 로 6개 큐레이션 파일 적재
- [x] 42청크 적재 (식품제조가공업 22 + 통신판매업 20)
- [x] 총 벡터: 329→371개
- [x] 메타데이터: source_type="law_curated", target_business_types 포함
- [x] 검색 테스트:
  - "식품제조가공업 영업허가" → law_curated 2건 포함 (0.455~0.460) ✅
  - "통신판매업 신고" → law_curated 5건 전부 (최고 0.417) ✅
- [x] **ActionKitItem 자동 생성**: `_ensure_actionkit_items()` 추가
  - `_ingest_curated()` 호출 시 벡터 적재 전에 ActionKitItem/Category/Highlight 자동 생성
  - `_BUSINESS_TYPE_TO_CHAPTER` 매핑: 업종→챕터 슬러그 (7~12)
  - 멱등 처리: 동일 name 아이템 존재 시 건너뜀

### P2-4. ActionKitItem 보강 및 매칭 검증 [S] ✅ (2026-02-26)
- [x] `seed_rag_vectors.py --sync-actionkit` 옵션 추가 (벡터 적재 없이 ActionKitItem만 생성)
- [x] Wave 1 업종 ActionKitItem +6건 생성 (식품제조가공업 3 + 통신판매업 3)
- [x] ActionKitItem 현황: 기존 46건 → **52건**
- [ ] 서버 재시작 후 ActionKitMatcher 매칭 결과 재확인 (3건+ 목표)
- [ ] 로드맵 생성 E2E 테스트: generation_mode=ACTIONKIT_RAG 확인
- **발견된 버그**: Wave 1에서 벡터 적재만 하고 ActionKitItem DB 레코드를 생성하지 않았음
  - ActionKitMatcher는 벡터 검색 후 ActionKitItem DB를 JOIN하므로, ActionKitItem이 없으면 매칭 0건 → RAG fallback
  - 이로 인해 통신판매업/식품제조가공업 로드맵이 전부 "근거 보강 필요"로 생성됨
- **남은 이슈**: 서버 캐시 문제로 재시작 전까지 매칭이 안 될 수 있음
  - File: `app-backend/scripts/seed_rag_vectors.py`
  - Acceptance: ActionKitItem 52건 확인, 매칭 재테스트 후 3건+ 매칭
  - Size: S (1~2h)
  - Dependencies: P2-3

### Wave 1 품질 게이트 (Wave 2 진입 조건) ✅ (2026-02-26)
- [x] 식품제조가공업 ActionKit >= 3건 → 5건 PASS
- [x] 통신판매업 ActionKit >= 3건 → **2건 SOFT FAIL** (ACTIONKIT_RAG는 활성화됨, threshold=1)
- [x] 휴게음식점 회귀 방지 → 9건 매칭, ACTIONKIT_RAG 유지 PASS
- [x] 교차 오염 → 소프트 오염 1건 발견, _load_full_items에서 자연 필터링 PASS
- [x] 테스트: 155 passed, 5 skipped
- **통신판매업 SOFT FAIL 원인**: DB에 전자상거래법 전용 ActionKitItem 없음. 후속 P5-2에서 해결 예정

---

## Phase 3: Wave 2 데이터 수집 - 미용업 + 일반소매업 (2~3일)

> **진입 조건**: Wave 1 품질 게이트 전항목 통과

### P3-1. Wave 2 법률 수집 실행 [M]
- [ ] `python -m scripts.fetch_laws --wave 2` 실행
- [ ] 미용업 수집 확인:
  - [ ] `.temp/rag/미용업/공중위생관리법.md` 존재
  - [ ] `.temp/rag/미용업/공중위생관리법_시행령.md` 존재
  - [ ] `.temp/rag/미용업/공중위생관리법_시행규칙.md` 존재
- [ ] 일반소매업 수집 확인:
  - [ ] `.temp/rag/일반소매업/유통산업발전법.md` 존재
  - [ ] `.temp/rag/일반소매업/유통산업발전법_시행령.md` 존재
  - [ ] `.temp/rag/일반소매업/유통산업발전법_시행규칙.md` 존재
  - Acceptance: 6건+ 법률 문서 수집 완료
  - Size: M (2~4h)
  - Dependencies: Wave 1 게이트 통과

### P3-2. Wave 2 관련 조문 큐레이션 [L]
- [ ] LLM 1차 필터링 + 수동 2차 검증 (Phase 2와 동일 프로세스)
- [ ] 미용업 조문 확정 (공중위생관리법 제3조, 제4조 등)
- [ ] 일반소매업 조문 확정 (유통산업발전법 제8조 등)
  - Acceptance: 업종당 관련 조문 5건 이상 확정
  - Size: L (4~8h)
  - Dependencies: P3-1

### P3-3. Wave 2 벡터 적재 + 품질 테스트 [M]
- [ ] `python -m scripts.seed_rag_vectors --wave 2` 실행
- [ ] 검색 품질 테스트 (Phase 2와 동일 구조)
- [ ] 교차 오염 테스트
- [ ] 기존 업종 regression 테스트
  - Acceptance: 검색 테스트 전체 통과
  - Size: M (2~4h)
  - Dependencies: P3-2

### Wave 2 품질 게이트 (Wave 3 진입 조건)
- [ ] Wave 2 업종 fallback 비율 < 10%
- [ ] Wave 2 업종 ActionKit 매칭 >= 3건
- [ ] 기존 업종 + Wave 1 업종 hit_rate 유지
- [ ] 교차 업종 오염 테스트 통과

---

## Phase 4: Wave 3 데이터 수집 - 학원업 + 숙박업 (2~3일)

> **진입 조건**: Wave 2 품질 게이트 전항목 통과

### P4-1. Wave 3 법률 수집 실행 [M]
- [ ] `python -m scripts.fetch_laws --wave 3` 실행
- [ ] 학원업 수집 확인:
  - [ ] `.temp/rag/학원업/학원의_설립운영_및_과외교습에_관한_법률.md` 존재
  - [ ] 시행령, 시행규칙 존재
- [ ] 숙박업 수집 확인:
  - [ ] `.temp/rag/숙박업/공중위생관리법.md` (미용업과 공유 → 심볼릭 링크 또는 복사)
  - [ ] `.temp/rag/숙박업/관광진흥법.md` 존재
  - [ ] 관광진흥법 시행령, 시행규칙 존재
- **주의**: 숙박업은 2개 법률 교차이므로 큐레이션 난이도 높음
  - Acceptance: 6건+ 법률 문서 수집 완료
  - Size: M (2~4h)
  - Dependencies: Wave 2 게이트 통과

### P4-2. Wave 3 관련 조문 큐레이션 [L]
- [ ] 학원업 조문 확정 (학원법 제6조 등록, 제13조 의무)
- [ ] 숙박업 조문 확정 (공중위생관리법 제3조 + 관광진흥법 제15조 등)
- [ ] 공중위생관리법의 미용업/숙박업 공유 조문 → `target_business_types`에 양쪽 태그
  - Acceptance: 업종당 관련 조문 5건 이상 확정, 교차 법률 태깅 완료
  - Size: L (4~8h)
  - Dependencies: P4-1

### P4-3. Wave 3 벡터 적재 + 품질 테스트 [M]
- [ ] `python -m scripts.seed_rag_vectors --wave 3` 실행
- [ ] 검색 품질 테스트
- [ ] 전체 업종 regression 테스트 (8개 업종)
  - Acceptance: 검색 테스트 전체 통과 + 전체 hit_rate >= 0.85
  - Size: M (2~4h)
  - Dependencies: P4-2

### Wave 3 품질 게이트 (최종)
- [ ] 전체 8개 업종 fallback 비율 < 10%
- [ ] 전체 8개 업종 ActionKit 매칭 >= 3건
- [ ] 전체 hit_rate@3 >= 0.85
- [ ] 교차 업종 오염률 <= 10%

---

## Phase 5: ActionKit 큐레이션 및 메타데이터 태깅 (3~5일)

> **시작 조건**: Phase 2 (Wave 1) 완료 후 시작 가능, Wave 2/3과 병렬 진행

### P5-1. 기존 ActionKit에 업종 태그 소급 적용 [S]
- [ ] `actionkit_seed_source.py`의 기존 46개 항목에 `target_business_types` 추가:
  - legal 11건: `["음식점", "휴게음식점", "일반음식점"]` (해당 항목에 맞게 분류)
  - tax 3건: `["all"]` (업종 공통)
  - hr 8건: `["all"]` (업종 공통)
  - grant 3건: `["all"]` (업종 공통)
  - File: `app-backend/scripts/seeds/actionkit_seed_source.py`
  - Acceptance: 모든 기존 ActionKit 항목에 target_business_types 존재
  - Size: S (1~2h)
  - Dependencies: 없음

### P5-2. Wave 1 업종 ActionKit 항목 추가 [L]
- [ ] 식품제조가공업 전용 ActionKit 항목 추가 (최소 10건):
  - [ ] 식품제조가공업 영업허가 절차 키트
  - [ ] 식품제조시설 기준 체크리스트
  - [ ] HACCP 인증 가이드
  - [ ] 기타 업종 특화 항목
- [ ] 통신판매업 전용 ActionKit 항목 추가 (최소 10건):
  - [ ] 통신판매업 신고 절차 키트
  - [ ] 온라인쇼핑몰 운영 체크리스트
  - [ ] 전자결제 PG 연동 가이드
  - [ ] 반품/환불 정책 서식
  - [ ] 기타 업종 특화 항목
  - File: `app-backend/scripts/seeds/actionkit_seed_source.py`
  - Details: 기존 구조 (LAW_DATA + ACTION_KIT_DATA) 패턴 따름
  - Acceptance: 업종당 10건+ 항목 추가, 기존 항목과 통합 검색 가능
  - Size: L (4~8h)
  - Dependencies: P2-2 (법률 목록 확정 후)

### P5-3. Wave 2/3 업종 ActionKit 항목 추가 [XL]
- [ ] 미용업 전용 항목 (10건+)
- [ ] 일반소매업 전용 항목 (10건+)
- [ ] 학원업 전용 항목 (10건+)
- [ ] 숙박업 전용 항목 (10건+)
  - File: `app-backend/scripts/seeds/actionkit_seed_source.py`
  - Details: 각 업종의 인허가, 시설기준, 영업준수사항 등 커버
  - Acceptance: 업종당 10건+ 항목, 총 ~100+ 항목
  - Size: XL (1~2일)
  - Dependencies: P3-2, P4-2 (각 Wave 큐레이션 완료 후)

### P5-4. VectorStoreService 메타데이터 확장 [M]
- [ ] `_build_base_metadata()`에 `target_business_types` 필드 추가
- [ ] `effective_date`, `last_verified_date` 필드 추가
- [ ] `law_hierarchy` 필드 추가
- [ ] 기존 벡터에 대한 메타데이터 업데이트 스크립트 작성
  ```python
  # 기존 음식점 벡터에 target_business_types 소급 적용
  UPDATE langchain_pg_embedding
  SET cmetadata = cmetadata || '{"target_business_types": ["음식점"]}'
  WHERE collection_id = :cid AND cmetadata->>'category' LIKE '%음식%';
  ```
  - File: `app-backend/app/services/vector_store.py`
  - Details: 하위 호환 유지 (target_business_types 없는 벡터도 검색 가능)
  - Acceptance: 새 문서 적재 시 확장 메타데이터 포함 + 기존 벡터 소급 업데이트
  - Size: M (2~4h)
  - Dependencies: P5-1

### P5-5. RagService 업종별 필터링 검색 [M]
- [ ] `RagService`에 `get_retriever(business_type: str | None)` 메서드 추가
- [ ] 업종 지정 시 `target_business_types` 메타데이터 필터링
- [ ] 업종 미지정 시 기존 전체 검색 유지 (하위 호환)
- [ ] ActionKitMatcher에서 업종별 retriever 사용하도록 연동
  - File: `app-backend/app/features/rag/application/rag_service.py`
  - Details: pgvector의 JSONB 필터링 사용, `$contains` 연산자
  - Acceptance:
    - 업종 지정 검색: 해당 업종 문서만 top-5에 포함
    - 업종 미지정 검색: 기존과 동일 동작
    - regression: 기존 음식점 검색 품질 유지
  - Size: M (2~4h)
  - Dependencies: P5-4

### P5-6. ActionKit 재인제스트 + 전체 검증 [M]
- [ ] 확장된 ActionKit 데이터 재인제스트:
  ```bash
  python -m scripts.seed_rag_vectors --actionkit-only --clean
  ```
- [ ] 전체 업종별 검색 품질 검증
- [ ] 벡터 총 수 확인 (목표: ~800~1,100건)
- [ ] `scripts/backup_law_vectors.py` 실행하여 백업
  - File: 스크립트 실행
  - Acceptance: 전체 벡터 수 목표 범위 내 + 업종별 검색 테스트 통과 + 백업 완료
  - Size: M (2~4h)
  - Dependencies: P5-3, P5-5

---

## 배포 체크리스트

- [ ] `app-backend/app/core/config.py`에 `LAW_API_OC` 설정 추가 확인
- [ ] `app-backend/pyproject.toml`에 `httpx` 의존성 확인
- [ ] `.env` 예시에 `LAW_API_OC` 문서화
- [ ] 벡터DB 백업 완료 (확장 전/후 모두)
- [ ] 전체 업종 검색 품질 테스트 통과
- [ ] 기존 업종 regression 테스트 통과
- [ ] 수집된 법률 문서의 `last_verified_date` 기록
- [ ] KOGL Type 1 출처 표시 확인 (source_url 메타데이터)

---

## 메모

### 병렬화 전략

```
Week 1:
  [Phase 0] + [P1-3 법률 매핑 리서치]
  [Phase 1: P1-1 ~ P1-7]

Week 2:
  [Phase 2: Wave 1 수집/큐레이션/적재]
  [P5-1: 기존 ActionKit 태깅] (병렬)

Week 3:
  [Wave 1 게이트 검증]
  [Phase 3: Wave 2 수집/큐레이션/적재]
  [P5-2: Wave 1 ActionKit 추가] (병렬)

Week 4:
  [Wave 2 게이트 검증]
  [Phase 4: Wave 3 수집/큐레이션/적재]
  [P5-3: Wave 2/3 ActionKit 추가] (병렬)
  [P5-4~5-6: 메타데이터 + 필터링 + 재인제스트]
```

### 블로커/질문

- open.law.go.kr OC 발급이 실제로 즉시 되는지 확인 필요
- 법률 전문 텍스트의 크기가 GPT-4 context window를 초과할 경우 분할 전략 필요
- 공중위생관리법이 미용업/숙박업에 모두 적용될 때 벡터 중복 여부 결정 필요
