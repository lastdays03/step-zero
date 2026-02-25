# 법률 자료 수집 전략 - 컨텍스트 및 의사결정

> Last Updated: 2026-02-25

## Status

- Phase: 계획 수립 완료, Phase 0 준비
- Progress: 0 / 22 tasks complete
- Last Updated: 2026-02-25

---

## Key Files

### 수정 대상 (Modified)

| 파일 | 역할 | 수정 Phase |
|---|---|---|
| `app-backend/app/core/config.py` | Settings에 LAW_API_OC 추가 | Phase 0 |
| `app-backend/app/services/law_fetcher.py` | MolegApiSource 구현체 추가 | Phase 1 |
| `app-backend/app/services/vector_store.py` | 메타데이터에 target_business_types 추가 | Phase 5 |
| `app-backend/app/features/rag/application/rag_service.py` | 업종별 필터링 검색 추가 | Phase 5 |
| `app-backend/scripts/seeds/actionkit_seed_source.py` | 업종별 ActionKit 항목 확장 | Phase 5 |
| `app-backend/scripts/seed_rag_vectors.py` | Wave별 인제스트 옵션 추가 | Phase 2~4 |

### 신규 생성 (New)

| 파일 | 역할 | 생성 Phase |
|---|---|---|
| `app-backend/app/services/law_api_client.py` | 국가법령정보센터 API thin wrapper | Phase 1 |
| `app-backend/scripts/fetch_laws.py` | 법률 수집 CLI 스크립트 | Phase 1 |
| `app-backend/scripts/curate_law_articles.py` | LLM 기반 조문 큐레이션 스크립트 | Phase 2 |
| `app-backend/tests/services/test_law_api_client.py` | API 클라이언트 테스트 | Phase 1 |
| `app-backend/tests/services/test_fetch_laws.py` | 수집 스크립트 테스트 | Phase 1 |

### 참조용 (Reference, 수정 없음)

| 파일 | 역할 |
|---|---|
| `app-backend/app/services/law_etl.py` | LLM 기반 ETL 프로세서 (GPT-4 turbo) |
| `app-backend/app/services/actionkit_data_source.py` | ActionKit 데이터 소스 |
| `app-backend/app/services/actionkit_etl.py` | ActionKit ETL 브릿지 |
| `app-backend/app/features/actionkit/application/file_pipeline.py` | 파일 유틸리티 (normalize, checksum 등) |
| `app-backend/scripts/backup_law_vectors.py` | 벡터 백업 스크립트 |
| `app-backend/scripts/verify_chunking.py` | 청킹 검증 스크립트 |

### 데이터 디렉토리

| 경로 | 역할 |
|---|---|
| `app-backend/.temp/rag/` | 수집된 법률 문서 저장 (LocalFileSource 루트) |
| `app-backend/.temp/backups/` | 벡터 백업 JSON |
| `app-backend/actionkits/files/` | ActionKit PDF/HWP 파일 |

---

## API 엔드포인트 상세

### 국가법령정보센터 Open API

#### 법령 검색

```
GET http://www.law.go.kr/DRF/lawSearch.do
  ?OC={oc}              # 인증코드 (이메일 ID)
  &target=law           # 검색 대상 (law: 법령, admrul: 행정규칙)
  &type=JSON            # 응답 형식 (XML 또는 JSON)
  &query={검색어}         # 법령명 또는 키워드
  &display=20           # 한 페이지 결과 수 (max 100)
  &page=1               # 페이지 번호

응답 (JSON):
{
  "LawSearch": {
    "totalCnt": "123",
    "page": "1",
    "law": [
      {
        "법령일련번호": "123456",
        "현행연혁코드": "현행",
        "법령명한글": "식품위생법",
        "법령약칭명": "",
        "법령ID": "12345",
        "공포일자": "20260101",
        "공포번호": "제21299호",
        "제개정구분명": "일부개정",
        "소관부처명": "식품의약품안전처",
        "법령구분명": "법률",
        "시행일자": "20260701"
      }
    ]
  }
}
```

#### 법령 본문 (전문)

```
GET http://www.law.go.kr/DRF/lawService.do
  ?OC={oc}
  &target=law
  &type=JSON
  &MST={법령일련번호}     # lawSearch 결과의 법령일련번호

응답: 법령 전문 (조문, 부칙 포함)
```

#### 조문 단위 조회

```
GET http://www.law.go.kr/DRF/lawService.do
  ?OC={oc}
  &target=lawjosub       # 조문 단위
  &type=JSON
  &MST={법령일련번호}

응답: 조문별 분리된 데이터
  - 조문번호, 조문제목, 조문내용, 항/호/목 세부 내용
```

#### 행정규칙 검색

```
GET http://www.law.go.kr/DRF/lawSearch.do
  ?OC={oc}
  &target=admrul         # 행정규칙
  &type=JSON
  &query={검색어}

응답: 고시, 훈령, 예규 목록
```

### Rate Limit 전략

- 권장 간격: 0.5초 (2 requests/sec)
- 일일 한도: 10,000건 (개발 쿼터)
- 구현: `asyncio.Semaphore(2)` + `asyncio.sleep(0.5)`
- 모니터링: 일일 요청 수 로깅, 8,000건 경과 시 경고

---

## 법률 계층 구조

```
법률 (National Assembly)
│   예: 식품위생법, 전자상거래법
│   - 국회에서 제정
│   - 가장 상위 법규
│
├── 시행령 (Presidential Decree, 대통령령)
│   예: 식품위생법 시행령, 전자상거래법 시행령
│   - 대통령이 제정
│   - 법률의 위임 사항 + 집행에 필요한 사항
│
├── 시행규칙 (Ministerial Ordinance, 부령/총리령)
│   예: 식품위생법 시행규칙
│   - 해당 부처 장관이 제정
│   - 구체적 절차, 서식, 기준 규정
│
└── 행정규칙 (Administrative Rules)
    예: 식품위생법 관련 고시, 훈령
    - 해당 행정기관이 제정
    - 법령 해석, 세부 기준, 내부 지침
    - 고시 > 훈령 > 예규 (구속력 순)
```

### 수집 범위 결정

| 계층 | 수집 여부 | 근거 |
|---|---|---|
| 법률 | **필수** | 핵심 의무/권리 규정 |
| 시행령 | **필수** | 구체적 기준/요건 규정 |
| 시행규칙 | **필수** | 절차/서식/세부기준 규정 |
| 행정규칙 (고시) | **선택** | 업종별 핵심 고시만 |
| 행정규칙 (훈령/예규) | **제외** | 내부 지침, 일반에게 직접 영향 적음 |

---

## 업종별 법률 매핑 상세

### Wave 1: 식품제조가공업

| 법률 | API 검색 키워드 | 핵심 조문 |
|---|---|---|
| 식품위생법 | "식품위생법" | 제36조 (시설기준), 제37조 (영업허가), 제44조 (영업자 준수사항) |
| 식품위생법 시행령 | "식품위생법 시행령" | 제21조 (영업의 종류), 제25조 (영업허가 등) |
| 식품위생법 시행규칙 | "식품위생법 시행규칙" | 제36조 (영업신고), 별표14 (시설기준) |

**기존 벡터와의 관계**: chapter-2 (영업 인허가 - 식품위생법 3건)를 확장하여 식품제조가공업 특화 조문 추가

### Wave 1: 통신판매업

| 법률 | API 검색 키워드 | 핵심 조문 |
|---|---|---|
| 전자상거래 등에서의 소비자보호에 관한 법률 | "전자상거래" | 제12조 (통신판매업자의 신고), 제13조 (신원정보 등의 제공) |
| 전자상거래법 시행령 | "전자상거래 시행령" | 제15조 (통신판매업 신고), 제16조 (신고 서류) |
| 전자상거래법 시행규칙 | "전자상거래 시행규칙" | 별지 서식 |
| [고시] 전자상거래 소비자보호 지침 | "전자상거래 소비자보호 지침" | 반품/환불/교환 기준 |

### Wave 2: 미용업

| 법률 | API 검색 키워드 | 핵심 조문 |
|---|---|---|
| 공중위생관리법 | "공중위생관리법" | 제3조 (영업신고), 제4조 (영업자 준수사항) |
| 공중위생관리법 시행령 | "공중위생관리법 시행령" | 제3조 (업종 분류), 제4조 (시설기준) |
| 공중위생관리법 시행규칙 | "공중위생관리법 시행규칙" | 별지 서식, 시설기준 |

### Wave 2: 일반소매업

| 법률 | API 검색 키워드 | 핵심 조문 |
|---|---|---|
| 유통산업발전법 | "유통산업발전법" | 제8조 (대규모점포 개설등록), 제12조의2 (전통시장 보호) |
| 유통산업발전법 시행령 | "유통산업발전법 시행령" | 제6조 (등록 기준) |
| 유통산업발전법 시행규칙 | "유통산업발전법 시행규칙" | 별지 서식 |

### Wave 3: 학원업

| 법률 | API 검색 키워드 | 핵심 조문 |
|---|---|---|
| 학원의 설립운영 및 과외교습에 관한 법률 | "학원의 설립" | 제6조 (학원 등록), 제13조 (학원 설립운영자 등 의무) |
| 학원법 시행령 | "학원 시행령" | 제7조 (시설기준), 제12조 (교습비 등) |
| 학원법 시행규칙 | "학원 시행규칙" | 별지 서식, 강사 자격 요건 |

### Wave 3: 숙박업

| 법률 | API 검색 키워드 | 핵심 조문 |
|---|---|---|
| 공중위생관리법 | (미용업과 공유) | 제3조 (영업신고) - 숙박업 분류 |
| 관광진흥법 | "관광진흥법" | 제15조 (관광숙박업 등록), 제19조 (사업계획 승인) |
| 관광진흥법 시행령 | "관광진흥법 시행령" | 제10조 (등록 기준) |
| 관광진흥법 시행규칙 | "관광진흥법 시행규칙" | 별지 서식 |

---

## 메타데이터 스키마

### 벡터 메타데이터 (law_vectors 컬렉션)

```python
# 현재 스키마 (기존)
{
    "source": "law_etl",           # str
    "title": "...",                # str
    "category": "...",             # str
    "summary": "...",              # str
    "law_reference": "...",        # str
    "filename": "...",             # str (LocalFileSource)
    "extension": "...",            # str
    "chunk_index": 0,              # int
    "total_chunks": 5,             # int
}

# 확장 스키마 (Phase 5에서 추가)
{
    # 기존 필드 유지 +
    "target_business_types": ["통신판매업"],  # list[str] - 대상 업종
    "effective_date": "2026-01-01",           # str - 시행일자
    "last_verified_date": "2026-02-25",       # str - 마지막 검증일
    "law_hierarchy": "법률",                   # str - 법률/시행령/시행규칙/행정규칙
    "law_id": "MST_123456",                   # str - 국가법령정보센터 ID
    "source_url": "https://...",              # str - 원본 URL
}
```

### 수집 메타데이터 (_meta.json)

```json
{
    "law_name": "전자상거래 등에서의 소비자보호에 관한 법률",
    "law_id": "MST_123456",
    "law_type": "법률",
    "effective_date": "2026-01-01",
    "promulgation_date": "2025-12-15",
    "promulgation_number": "제21000호",
    "ministry": "공정거래위원회",
    "target_business_types": ["통신판매업", "온라인쇼핑몰"],
    "collected_at": "2026-02-25T10:30:00+09:00",
    "api_source": "law.go.kr/DRF",
    "total_articles": 45,
    "curated_articles": [12, 13, 14, 15, 17, 20],
    "curation_method": "llm_gpt4_manual_review"
}
```

---

## Key Decisions

### D1. 데이터 소스 선택: 국가법령정보센터 Open API

- **결정**: law.go.kr/DRF API를 1차 데이터 소스로 사용
- **근거**:
  - 즉시 등록 가능 (OC = 이메일 ID)
  - XML/JSON 응답으로 파싱 용이
  - 조문 단위 조회 가능 (`target=lawjosub`)
  - KOGL Type 1 라이선스 (출처 표시만 하면 자유 이용)
- **대안**: data.go.kr (동일 데이터, serviceKey 인증, 승인 필요 → 느림)
- **Trade-off**: 성숙한 Python SDK가 없어 자체 wrapper 필요

### D2. 큐레이션 전략: LLM + 수동 하이브리드

- **결정**: LLM 기반 1차 필터링 → 수동 2차 검증
- **근거**:
  - 법률 전문은 수백 조문인데, 업종별 관련 조문은 5~15개 수준
  - 전체 적재 시 노이즈 증가 → 검색 정밀도 저하
  - LLM이 관련성 점수를 산출하면 수동 검증 효율 10배 이상 향상
- **대안 1**: 전체 적재 후 메타데이터 필터링 → 벡터 수 과다, 비용 증가
- **대안 2**: 완전 수동 큐레이션 → 시간 과다 (법률 1건당 2~3시간)
- **Trade-off**: LLM 큐레이션의 정확도가 낮을 경우 수동 보정 비용 발생

### D3. 라이선스: KOGL Type 1

- **결정**: 공공누리 제1유형으로 자유 이용
- **근거**: 국가법령정보센터는 공공데이터로, 출처 표시만 하면 상업적 이용 포함 자유 이용 가능
- **출처 표시 방식**: 벡터 메타데이터의 `source_url`에 원본 링크 포함
- **주의사항**: 법률 자체는 저작권 없음 (저작권법 제7조), 해설/주석은 별도

### D4. 기존 파이프라인 확장 vs 신규 파이프라인

- **결정**: 기존 파이프라인 확장 (LocalFileSource + LawETLProcessor 재사용)
- **근거**:
  - `LawDataSource` ABC가 이미 확장 가능하게 설계됨 (`SourceType.API` enum 정의됨)
  - `VectorStoreService`의 청킹/임베딩 로직 재사용 가능
  - `seed_rag_vectors.py`의 인제스트 플로우 재사용
- **영향**: API에서 수집한 데이터를 `.temp/rag/{업종}/`에 저장하면 기존 LocalFileSource 플로우 호환

### D5. 기존 Python 법률 API 라이브러리 부재

- **결정**: 자체 thin wrapper 구현 (~100~150줄)
- **근거**:
  - 검색 결과 성숙한 Python 라이브러리가 없음
  - 필요 기능이 단순 (검색, 본문 조회, 조문 조회) → 자체 구현 용이
  - 외부 의존성 최소화
- **유지보수**: API 스키마 변경 시 wrapper만 수정

### D6. 벡터 저장소 구조: 단일 컬렉션 + 메타데이터 필터링

- **결정**: 기존 `law_vectors` 컬렉션에 통합 저장, `target_business_types`로 필터링
- **근거**:
  - pgvector의 HNSW 인덱스는 단일 컬렉션에서 최적 성능
  - 메타데이터 JSONB 필터링으로 업종 분리 가능
  - 컬렉션 분리 시 검색 로직 복잡화
- **대안**: 업종별 별도 컬렉션 → 관리 복잡, 공통 법률(행정법 등) 중복 필요
- **Trade-off**: 1,000+ 벡터 시 HNSW 인덱스 재빌드 필요할 수 있음

### D7. Wave 단위 점진적 확장

- **결정**: 2개 업종씩 3 Wave로 분리 (Phase 2A~2C 구조 계승)
- **근거**: `roadmap-quality-plan-v2.md`의 품질 게이트 전략과 일치
- **게이트 조건**: fallback < 10%, ActionKit >= 3건, hit_rate >= 0.85
- **이점**: Wave 간 학습 효과, 리스크 분산, 롤백 용이

---

## 통합 포인트 (Integration Points)

### 1. seed_rag_vectors.py와의 통합

```
현재:
  python -m scripts.seed_rag_vectors --source-dir .temp/rag

추가:
  python -m scripts.seed_rag_vectors --source-dir .temp/rag/통신판매업 --include-actionkit
  python -m scripts.seed_rag_vectors --wave 1  # Wave 1 업종만 인제스트 (신규 옵션)
```

### 2. RagService와의 통합

```python
# 현재: 업종 무관 전체 검색
self.retriever = self.vector_store.as_retriever(search_kwargs={"k": 5})

# 확장: 업종별 필터링 검색
def get_retriever(self, business_type: str | None = None):
    search_kwargs = {"k": 5}
    if business_type:
        search_kwargs["filter"] = {
            "target_business_types": {"$contains": business_type}
        }
    return self.vector_store.as_retriever(search_kwargs=search_kwargs)
```

### 3. ActionKitMatcher와의 통합

```python
# roadmap-quality-plan-v2.md P2A-3에서 처리
# CATEGORY_TO_PHASE 매핑에 새 업종 추가
# match() 쿼리에 업종별 키워드 전략 적용
```

---

## Testing Notes

### API 클라이언트 테스트

- 유닛 테스트: `httpx.MockTransport`를 사용한 모킹
- 통합 테스트: 실제 API 호출 (환경변수 LAW_API_OC 필요, CI에서는 skip)
- Rate limit 테스트: 다수 요청 시 0.5초 간격 보장 확인

### 수집 스크립트 테스트

- 파일 생성 확인: `.temp/rag/{업종}/{법령명}.md` 존재
- 메타데이터 확인: `_meta.json` 필수 필드 존재
- 중복 방지 확인: 동일 법률 재수집 시 skip

### 벡터 적재 테스트

- similarity search 확인: 업종 키워드 검색 시 해당 업종 문서 top-3 포함
- 교차 오염 확인: 미용업 키워드 검색 시 식품위생법 미포함
- regression 확인: 기존 음식점 업종 hit_rate@3 >= 0.85 유지

---

## Known Issues & Future Enhancements

### Known Issues

1. **법령 XML 파싱 복잡성** - 법제처 XML 스키마가 복잡하여 edge case 존재 가능
2. **행정규칙 검색 정밀도** - "고시" 검색 시 관련 없는 결과가 다수 포함될 수 있음
3. **공중위생관리법 공유** - 미용업과 숙박업이 동일 법률 → 업종 태그 다중 지정 필요

### Future Enhancements

- **F-1**: 법률 개정 자동 감지 스크립트 (분기별 cron)
- **F-2**: data.go.kr fallback 소스 구현
- **F-3**: 법률 본문 요약 캐싱 (LLM ETL 비용 절감)
- **F-4**: 벡터 품질 자동 평가 (업종별 hit_rate 모니터링)
- **F-5**: 법률 변경 이력 추적 (effective_date 기반 버전 관리)
