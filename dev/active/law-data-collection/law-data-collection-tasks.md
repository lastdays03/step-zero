# 법률 자료 수집 전략 - 태스크 체크리스트

> Last Updated: 2026-02-25

## 상태 범례

- [ ] 미시작
- [x] 완료
- [>>] 진행 중
- [!!] 블로커
- [--] 건너뜀

## 진행 요약

| Phase | 총 태스크 | 완료 | 진행률 |
|---|---|---|---|
| Phase 0: API 등록 | 4 | 0 | 0% |
| Phase 1: 수집 스크립트 | 8 | 0 | 0% |
| Phase 2: Wave 1 수집 | 6 | 0 | 0% |
| Phase 3: Wave 2 수집 | 4 | 0 | 0% |
| Phase 4: Wave 3 수집 | 4 | 0 | 0% |
| Phase 5: ActionKit 큐레이션 | 6 | 0 | 0% |
| **전체** | **32** | **0** | **0%** |

---

## Phase 0: API 등록 및 환경 설정 (0.5일)

### P0-1. open.law.go.kr 회원가입 + OC 발급 [XS]
- [ ] open.law.go.kr 접속하여 회원가입
- [ ] OC (Open API Code) 발급 확인 (이메일 ID = OC)
  - File: 없음 (외부 작업)
  - Details: OC는 등록 시 사용한 이메일의 @ 앞 부분이 됨
  - Acceptance: OC 코드 확보, API 호출 가능 상태
  - Size: XS (30분 이내)
  - Dependencies: 없음

### P0-2. 환경변수 및 설정 추가 [XS]
- [ ] `app-backend/.env`에 `LAW_API_OC=발급받은OC` 추가
- [ ] `app-backend/app/core/config.py`의 Settings 클래스에 `LAW_API_OC: str = ""` 추가
  - File: `app-backend/app/core/config.py`
  - Details: 기존 Pydantic BaseSettings 패턴 따름, Optional로 설정 (없으면 수집 스크립트만 비활성)
  - Acceptance: `get_settings().LAW_API_OC` 접근 가능
  - Size: XS (30분 이내)
  - Dependencies: P0-1

### P0-3. API 연결 테스트 [XS]
- [ ] curl 또는 httpie로 식품위생법 검색 요청 테스트
  ```bash
  curl "http://www.law.go.kr/DRF/lawSearch.do?OC={oc}&target=law&type=JSON&query=식품위생법&display=5"
  ```
- [ ] JSON 응답 파싱 확인 (법령일련번호, 법령명, 시행일자 존재)
  - File: 없음 (수동 테스트)
  - Details: 응답 구조 파악 후 P1-1 설계에 반영
  - Acceptance: HTTP 200 + JSON 응답 내 법령 목록 1건 이상
  - Size: XS (30분 이내)
  - Dependencies: P0-1

### P0-4. httpx 의존성 추가 [XS]
- [ ] `app-backend/pyproject.toml`에 `httpx` 의존성 추가
- [ ] `uv pip install -e .` 재실행으로 설치 확인
  - File: `app-backend/pyproject.toml`
  - Details: httpx는 async HTTP 클라이언트로, aiohttp 대비 타입 지원 우수
  - Acceptance: `import httpx` 성공
  - Size: XS (15분 이내)
  - Dependencies: 없음

---

## Phase 1: 수집 스크립트 개발 (2~3일)

### P1-1. 국가법령정보센터 API 클라이언트 래퍼 [M]
- [ ] `LawSearchResult` Pydantic 모델 정의 (법령일련번호, 법령명, 법령구분, 시행일자, 공포일자, 소관부처)
- [ ] `LawFullText` Pydantic 모델 정의 (전문 텍스트, 조문 목록)
- [ ] `LawApiClient` 클래스 구현:
  - [ ] `__init__(self, oc: str, rate_limit: float = 0.5)` - 인증 + rate limit 설정
  - [ ] `search_laws(query, display=20, page=1)` -> `list[LawSearchResult]`
  - [ ] `get_law_full_text(mst)` -> `LawFullText`
  - [ ] `get_law_articles(mst)` -> `list[LawArticle]`
  - [ ] `search_admin_rules(query)` -> `list[AdminRuleResult]`
  - [ ] Rate limiting: `asyncio.Semaphore(2)` + `asyncio.sleep(0.5)`
  - [ ] 에러 핸들링: 타임아웃, 파싱 에러, HTTP 에러
  - File: `app-backend/app/services/law_api_client.py` (신규)
  - Details: ~100~150줄의 thin wrapper, XML/JSON 자동 감지
  - Acceptance: 식품위생법 검색 + 본문 조회 + 조문 조회 모두 성공
  - Size: M (2~4h)
  - Dependencies: P0-2, P0-4

### P1-2. API 클라이언트 유닛 테스트 [S]
- [ ] `httpx.MockTransport`를 사용한 모킹 테스트 작성
  - [ ] 검색 응답 파싱 테스트
  - [ ] 본문 조회 응답 파싱 테스트
  - [ ] Rate limit 동작 확인 테스트
  - [ ] 에러 핸들링 테스트 (타임아웃, 404, 잘못된 JSON)
  - File: `app-backend/tests/services/test_law_api_client.py` (신규)
  - Details: CI에서 실행 가능하도록 외부 API 호출 없이 모킹
  - Acceptance: pytest 전체 통과
  - Size: S (1~2h)
  - Dependencies: P1-1

### P1-3. 업종별 법률 수집 설정 정의 [S]
- [ ] 업종별 수집 대상 법률 매핑 딕셔너리 작성:
  ```python
  WAVE_CONFIG = {
      1: {
          "식품제조가공업": [
              {"query": "식품위생법", "hierarchy": ["법률", "시행령", "시행규칙"]},
          ],
          "통신판매업": [
              {"query": "전자상거래", "hierarchy": ["법률", "시행령", "시행규칙"]},
          ],
      },
      2: { ... },
      3: { ... },
  }
  ```
- [ ] `target_business_types` 태그 매핑 정의
  - File: `app-backend/scripts/fetch_laws.py` 상단 또는 별도 config 파일
  - Details: 법률명→검색 키워드→업종 태그 매핑
  - Acceptance: 전체 3 Wave, 6 업종, 7~8 법률의 매핑 완성
  - Size: S (1~2h)
  - Dependencies: 없음 (리서치 작업, Phase 0과 병렬 가능)

### P1-4. 법률 수집 CLI 스크립트 [L]
- [ ] CLI 인터페이스 구현 (argparse):
  - [ ] `--wave {1,2,3}` - Wave별 일괄 수집
  - [ ] `--law {법률명}` - 단일 법률 수집
  - [ ] `--list` - 수집 대상 목록 출력
  - [ ] `--status` - 수집 현황 (완료/미수집) 출력
  - [ ] `--dry-run` - 실제 API 호출 없이 수집 대상 확인
- [ ] 수집 플로우 구현:
  - [ ] API 검색 → 법령일련번호(MST) 확보
  - [ ] 본문 조회 → Markdown 변환
  - [ ] `.temp/rag/{업종}/{법령명}.md` 저장
  - [ ] `{법령명}_meta.json` 메타데이터 저장
  - [ ] 중복 방지: 파일 이미 존재하면 skip (--force로 재수집)
- [ ] 수집 결과 리포트 출력:
  - [ ] 성공/실패/건수
  - [ ] 수집된 파일 경로 목록
  - File: `app-backend/scripts/fetch_laws.py` (신규)
  - Details: `law_api_client.py` 사용, async 실행
  - Acceptance:
    - `python -m scripts.fetch_laws --list` → 전체 수집 대상 출력
    - `python -m scripts.fetch_laws --wave 1 --dry-run` → Wave 1 대상 확인
    - `python -m scripts.fetch_laws --law 식품위생법` → 3건 (법률+시행령+시행규칙) 수집
  - Size: L (4~8h)
  - Dependencies: P1-1, P1-3

### P1-5. LawDataSource API 구현체 (MolegApiSource) [M]
- [ ] `law_fetcher.py`에 `MolegApiSource` 클래스 추가
- [ ] `LawDataSource` ABC의 `fetch_all_laws()` 구현:
  - [ ] 지정된 업종의 수집 완료 파일을 읽어 `LawData` 목록 반환
  - [ ] 메타데이터에 `target_business_types`, `effective_date`, `law_hierarchy` 포함
  - [ ] 기존 `LocalFileSource`와 동일한 출력 형식 보장
- [ ] `source_type=SourceType.API` 설정
  - File: `app-backend/app/services/law_fetcher.py`
  - Details: 실제 API 호출은 `fetch_laws.py`에서 수행, MolegApiSource는 수집된 파일을 읽는 역할
  - Acceptance: `MolegApiSource().fetch_all_laws()` → `list[LawData]` 반환, 기존 ETL 파이프라인 호환
  - Size: M (2~4h)
  - Dependencies: P1-4

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

### P1-7. seed_rag_vectors.py Wave별 인제스트 옵션 추가 [S]
- [ ] `--wave {1,2,3}` 옵션 추가: 해당 Wave 업종 디렉토리만 인제스트
- [ ] `--business-type {업종명}` 옵션 추가: 단일 업종만 인제스트
- [ ] 메타데이터에 `target_business_types` 자동 포함
  - File: `app-backend/scripts/seed_rag_vectors.py`
  - Details: 기존 `--source-dir` 옵션과 호환, Wave 옵션은 내부적으로 source-dir 설정
  - Acceptance: `python -m scripts.seed_rag_vectors --wave 1` → Wave 1 업종만 인제스트
  - Size: S (1~2h)
  - Dependencies: P1-5

---

## Phase 2: Wave 1 데이터 수집 - 식품제조가공업 + 통신판매업 (2~3일)

### P2-1. Wave 1 법률 수집 실행 [M]
- [ ] `python -m scripts.fetch_laws --wave 1` 실행
- [ ] 식품제조가공업 수집 확인:
  - [ ] `.temp/rag/식품제조가공업/식품위생법.md` 존재 + 내용 비어있지 않음
  - [ ] `.temp/rag/식품제조가공업/식품위생법_시행령.md` 존재
  - [ ] `.temp/rag/식품제조가공업/식품위생법_시행규칙.md` 존재
  - [ ] 각 파일의 `_meta.json` 존재 + 필수 필드 포함
- [ ] 통신판매업 수집 확인:
  - [ ] `.temp/rag/통신판매업/전자상거래법.md` 존재
  - [ ] `.temp/rag/통신판매업/전자상거래법_시행령.md` 존재
  - [ ] `.temp/rag/통신판매업/전자상거래법_시행규칙.md` 존재
  - File: 스크립트 실행 (코드 수정 없음)
  - Details: API 호출 대기 시간 포함 예상 30분~1시간
  - Acceptance: 6건+ 법률 문서 수집 완료, 모든 _meta.json 존재
  - Size: M (2~4h, API 대기 포함)
  - Dependencies: P1-4

### P2-2. Wave 1 관련 조문 큐레이션 [L]
- [ ] `python -m scripts.curate_law_articles --wave 1` 실행 (LLM 1차 필터링)
- [ ] 식품제조가공업 큐레이션 수동 검증:
  - [ ] 식품위생법 관련 조문 확인 (제36조 시설기준, 제37조 영업허가, 제44조 준수사항)
  - [ ] 식품제조가공업 특화 조문 누락 여부 확인
  - [ ] `target_business_types` 태그 정확성 확인
- [ ] 통신판매업 큐레이션 수동 검증:
  - [ ] 전자상거래법 관련 조문 확인 (제12조 신고, 제13조 신원정보)
  - [ ] 통신판매업 특화 조문 누락 여부 확인
- [ ] 큐레이션 완료 파일 확정 (`_curated.md` → `_final.md`로 이동)
  - File: 스크립트 실행 + 수동 검증
  - Details: 핵심 병목 단계, LLM 결과의 정확도에 따라 소요 시간 변동
  - Acceptance: 업종당 관련 조문 5건 이상 확정 + target_business_types 태그 완료
  - Size: L (4~8h, 수동 검증 포함)
  - Dependencies: P2-1

### P2-3. Wave 1 벡터 적재 [M]
- [ ] `python -m scripts.seed_rag_vectors --wave 1` 실행
- [ ] 적재 결과 확인:
  - [ ] 식품제조가공업 관련 벡터 존재 확인 (pgvector 쿼리)
  - [ ] 통신판매업 관련 벡터 존재 확인
  - [ ] 메타데이터에 `target_business_types` 포함 확인
- [ ] 검색 품질 테스트:
  - [ ] "식품제조가공업 영업허가" 검색 → 식품제조가공업 문서 top-3 포함
  - [ ] "통신판매업 신고" 검색 → 통신판매업 문서 top-3 포함
  - [ ] "미용업 신고" 검색 → 식품위생법/전자상거래법 미포함 (교차 오염 테스트)
  - [ ] 기존 "휴게음식점 영업신고" 검색 → hit_rate@3 >= 0.85 유지 (regression)
  - File: `app-backend/scripts/seed_rag_vectors.py`
  - Acceptance: 검색 테스트 4건 모두 통과
  - Size: M (2~4h)
  - Dependencies: P2-2

### Wave 1 품질 게이트 (Wave 2 진입 조건)
- [ ] Wave 1 업종 fallback 비율 < 10%
- [ ] Wave 1 업종 ActionKit 매칭 >= 3건
- [ ] Wave 1 업종 로드맵 생성 성공
- [ ] 기존 업종(음식점) hit_rate@3 >= 0.85 유지
- [ ] 교차 업종 오염 테스트 통과

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
