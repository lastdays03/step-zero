# 법률 자료 수집 전략 (Law Data Collection Strategy) - 전략 계획

> Last Updated: 2026-02-25
> 상위 계획: `dev/active/roadmap-quality/roadmap-quality-plan-v2.md` Phase 2A~2C

## Executive Summary

현재 벡터DB에는 **식품위생법 중심 47개 문서**(laws 22 + kits 25)만 적재되어 있어,
음식점 외 업종(통신판매, 미용, 소매, 학원, 숙박)의 로드맵 생성이 불가능한 상태이다.
본 계획은 **국가법령정보센터 Open API**를 활용하여 6개 추가 업종의 법률 문서를 체계적으로
수집하고, 기존 RAG 파이프라인에 통합하여 벡터DB를 확장하는 전략을 정의한다.

핵심 병목은 법률 원문 수집이 아닌 **업종별 관련 조문 큐레이션**이며,
LLM 기반 관련성 스코어링 + 수동 검증의 2단계 큐레이션 프로세스를 제안한다.

---

## Current State Analysis

### 벡터DB 현황

| 항목 | 수치 |
|---|---|
| 총 고유 문서 | 47개 (laws 22 + kits 25) |
| 적재된 벡터 수 | 314개 (ActionKit) + 샘플 3건 (법률) |
| 대상 업종 | 음식점 업종만 (휴게음식점, 일반음식점) |
| 법률 범위 | 식품위생법, 건축법, 소방법, 행정법 등 |
| 비음식 업종 지원 | **불가** |

### 기존 파이프라인 구조

```
[데이터 소스] → [ETL] → [벡터 적재]

LocalFileSource (.temp/rag/*.pdf, *.md)
    → LawETLProcessor (GPT-4 가이드 변환)
    → VectorStoreService (청킹 600/100 + text-embedding-3-small)
    → pgvector law_vectors 컬렉션

ActionKitDataSource (actionkit_seed_source.py)
    → ActionKitETLBridge
    → VectorStoreService
    → pgvector law_vectors 컬렉션
```

### 기존 파이프라인의 한계

1. **LocalFileSource만 지원** - 수동으로 PDF를 `.temp/rag/`에 넣어야 함
2. **API 소스 미구현** - `LawDataSource` ABC에 `SourceType.API`가 정의되어 있으나 구현체 없음
3. **메타데이터 부족** - `target_business_types`, `effective_date`, `last_verified_date` 미포함
4. **업종별 필터링 불가** - 벡터 검색 시 업종 구분 없이 전체 검색

---

## 데이터 소스 분석

### 국가법령정보센터 Open API

| 항목 | 내용 |
|---|---|
| URL | `http://www.law.go.kr/DRF/lawSearch.do` (검색), `http://www.law.go.kr/DRF/lawService.do` (본문) |
| 인증 | OC (Open API Code) = 이메일 ID, 즉시 발급 |
| 응답 형식 | XML / JSON |
| 라이선스 | KOGL Type 1 (공공누리 제1유형, 출처 표시) |
| 요청 제한 | 개발용 10,000건/일, 0.5초 rate limit 권장 |
| 조문 단위 | `target=lawjosub` 엔드포인트로 조문별 조회 가능 |
| 행정규칙 | `target=admrul` 엔드포인트로 고시/훈령/예규 조회 |

### 엔드포인트 상세

```
# 법령 검색 (목록)
GET http://www.law.go.kr/DRF/lawSearch.do
  ?OC={oc}&target=law&type=JSON&query={검색어}&display=20&page=1

# 법령 본문 (전문)
GET http://www.law.go.kr/DRF/lawService.do
  ?OC={oc}&target=law&type=JSON&MST={법령일련번호}

# 조문 단위
GET http://www.law.go.kr/DRF/lawService.do
  ?OC={oc}&target=lawjosub&type=JSON&MST={법령일련번호}

# 행정규칙
GET http://www.law.go.kr/DRF/lawSearch.do
  ?OC={oc}&target=admrul&type=JSON&query={검색어}
```

### data.go.kr (대안)

- 동일 데이터, 다른 인증 방식 (serviceKey)
- 승인 절차가 있어 즉시성이 떨어짐
- 1차적으로 law.go.kr 사용, fallback으로 활용

---

## 법률 계층 구조 (수집 범위)

각 업종별로 아래 3단계 + 행정규칙까지 수집한다:

```
법률 (법률)
  └── 시행령 (대통령령)
       └── 시행규칙 (부령/총리령)
            └── [선택] 행정규칙 (고시/훈령/예규)
```

**업종당 필요 문서 수**: 법률 1 + 시행령 1 + 시행규칙 1 = 최소 3건,
행정규칙 포함 시 4~6건

---

## 대상 업종 및 법률 매핑

### Wave 1 (파일럿, 기존 법률 활용도 높음)

| 업종 | 핵심 법률 | 수집 문서 (예상) | 비고 |
|---|---|---|---|
| **식품제조가공업** | 식품위생법 | 3건 (기존 chapter-2 확장) | 기존 벡터 활용, 난이도 低 |
| **통신판매업** | 전자상거래법 + 통신판매업 신고 관련 | 6건+ | 수요 높음, 신규 법률 |

### Wave 2

| 업종 | 핵심 법률 | 수집 문서 (예상) | 비고 |
|---|---|---|---|
| **미용업** | 공중위생관리법 | 3건+ | 1인 창업 수요 높음 |
| **일반소매업** | 유통산업발전법 | 3건+ | 편의점/소매점 |

### Wave 3

| 업종 | 핵심 법률 | 수집 문서 (예상) | 비고 |
|---|---|---|---|
| **학원업** | 학원의 설립운영 및 과외교습에 관한 법률 | 3건+ | 규제 복잡 |
| **숙박업** | 공중위생관리법 + 관광진흥법 | 6건+ | 2개 법률 교차 |

### 총 예상 수집 규모

| 항목 | 수량 |
|---|---|
| 대상 법률 (고유) | 7~8개 |
| 수집 문서 (법률+시행령+시행규칙) | 24~30건 |
| 행정규칙 포함 시 | 35~45건 |
| 예상 벡터 수 (청킹 후) | 500~800건 |
| 현재 벡터 수 | ~317건 |
| 확장 후 예상 총 벡터 | ~800~1,100건 |

---

## Implementation Phases

### Phase 0: API 등록 및 환경 설정 (0.5일)

**목표**: 국가법령정보센터 API 접근 가능 상태 확보

**태스크**:
- [ ] open.law.go.kr 회원가입 + OC 발급 - Size: XS
- [ ] `.env`에 `LAW_API_OC` 환경변수 추가 - Size: XS
- [ ] `app-backend/app/core/config.py`에 `LAW_API_OC` 설정 추가 - Size: XS
- [ ] API 연결 테스트 (curl로 식품위생법 검색) - Size: XS

**AC**: curl로 법령 검색 응답 200 + JSON 파싱 성공

---

### Phase 1: 법령 수집 스크립트 개발 (2~3일)

**목표**: 국가법령정보센터 API를 호출하여 법률 전문을 수집하는 재사용 가능한 스크립트 구현

#### P1-1. API 클라이언트 래퍼 (thin wrapper) [M]

- **파일**: `app-backend/app/services/law_api_client.py` (신규)
- 기능:
  - 법령 검색 (`search_laws`)
  - 법령 본문 조회 (`get_law_full_text`)
  - 조문 단위 조회 (`get_law_articles`)
  - 행정규칙 검색 (`search_admin_rules`)
- Rate limiting: 0.5초 간격, `asyncio.Semaphore(2)` 동시 요청 제한
- 응답 파싱: XML/JSON 자동 감지 + Pydantic 모델 변환
- 예상 코드량: ~100~150줄
- **Size**: M (2~4h)

#### P1-2. 법령 수집 CLI 스크립트 [L]

- **파일**: `app-backend/scripts/fetch_laws.py` (신규)
- 기능:
  - 업종별 법률 목록 설정 (YAML 또는 Python dict)
  - Wave별 일괄 수집
  - 수집 결과를 `.temp/rag/{업종}/` 디렉토리에 저장
  - JSON 메타데이터 파일 동반 생성 (`{법령명}_meta.json`)
  - 중복 수집 방지 (이미 파일이 존재하면 skip)
  - 수집 결과 리포트 (성공/실패/건수)
- CLI 인터페이스:
  ```bash
  python -m scripts.fetch_laws --wave 1        # Wave 1 법률 수집
  python -m scripts.fetch_laws --law 식품위생법  # 단일 법률 수집
  python -m scripts.fetch_laws --list           # 수집 대상 목록 출력
  python -m scripts.fetch_laws --status         # 수집 현황 출력
  ```
- **Size**: L (4~8h)

#### P1-3. LawDataSource API 구현체 [M]

- **파일**: `app-backend/app/services/law_fetcher.py` 확장
- `LawDataSource` ABC를 구현하는 `MolegApiSource` 클래스 추가
- `law_api_client.py`를 사용하여 `fetch_all_laws()` 구현
- 기존 `LocalFileSource`와 동일한 `LawData` 출력 보장
- 메타데이터 확장:
  ```python
  metadata = {
      "law_id": "MST 법령일련번호",
      "effective_date": "2026-01-01",
      "last_verified_date": "2026-02-25",
      "target_business_types": ["통신판매업", "온라인쇼핑몰"],
      "law_hierarchy": "법률",  # 법률/시행령/시행규칙/행정규칙
      "source_url": "https://www.law.go.kr/법령/전자상거래법",
  }
  ```
- **Size**: M (2~4h)

---

### Phase 2: Wave 1 데이터 수집 (2~3일)

**목표**: 식품제조가공업 + 통신판매업 법률 수집 및 벡터 적재

#### P2-1. Wave 1 법률 수집 실행 [M]

- `scripts/fetch_laws.py --wave 1` 실행
- 식품제조가공업: 식품위생법 (기존 확장), 식품위생법 시행령, 식품위생법 시행규칙
- 통신판매업: 전자상거래법, 전자상거래법 시행령, 전자상거래법 시행규칙 + 통신판매업 신고 관련 고시
- 수집 결과 검증: 파일 존재 + 내용 비어있지 않음
- **Size**: M (2~4h, API 호출 대기 시간 포함)

#### P2-2. 관련 조문 큐레이션 (핵심 병목) [L]

- 수집된 법률 전문에서 업종별 관련 조문 선별
- LLM 기반 1차 필터링:
  - GPT-4에 법률 전문 + 업종 컨텍스트 입력
  - 조문별 관련성 점수 (0~1) 산출
  - 0.5 이상 조문만 추출
- 수동 2차 검증:
  - LLM이 선별한 조문의 실제 관련성 확인
  - 누락 조문 보충
  - `target_business_types` 태그 확정
- 큐레이션 결과를 `.temp/rag/{업종}/{법령명}_curated.md`로 저장
- **Size**: L (4~8h, 수동 검증 포함)

#### P2-3. Wave 1 벡터 적재 [M]

- 기존 `seed_rag_vectors.py` 확장하여 새 문서 적재
- 메타데이터에 `target_business_types` 포함
- 적재 후 검증:
  - similarity search로 업종별 문서 검색 테스트
  - 교차 업종 오염 테스트 (통신판매업 검색 시 식품위생법 미포함 확인)
- **Size**: M (2~4h)

---

### Phase 3: Wave 2 데이터 수집 (2~3일)

**목표**: 미용업 + 일반소매업 법률 수집 및 벡터 적재

#### P3-1~3. Wave 2 수집/큐레이션/적재

- Phase 2와 동일 구조 반복
- 미용업: 공중위생관리법 + 시행령 + 시행규칙
- 일반소매업: 유통산업발전법 + 시행령 + 시행규칙
- **진입 조건**: Wave 1 품질 게이트 통과
  - [ ] Wave 1 업종 fallback 비율 < 10%
  - [ ] Wave 1 업종 ActionKit 매칭 >= 3건
  - [ ] 기존 업종(음식점) hit_rate@3 >= 0.85 유지

---

### Phase 4: Wave 3 데이터 수집 (2~3일)

**목표**: 학원업 + 숙박업 법률 수집 및 벡터 적재

#### P4-1~3. Wave 3 수집/큐레이션/적재

- Phase 2와 동일 구조 반복
- 학원업: 학원의 설립운영 및 과외교습에 관한 법률 + 시행령 + 시행규칙
- 숙박업: 공중위생관리법(미용업과 공유) + 관광진흥법 + 시행령 + 시행규칙
- **진입 조건**: Wave 2 품질 게이트 통과
- **주의**: 숙박업은 2개 법률 교차이므로 큐레이션 난이도 높음

---

### Phase 5: ActionKit 시드 데이터 큐레이션 (3~5일)

**목표**: 업종별 ActionKit 항목 확장 + 벡터 메타데이터 태깅

#### P5-1. ActionKit 시드 데이터 확장 [XL]

- **파일**: `app-backend/scripts/seeds/actionkit_seed_source.py` 확장
- 현재: 음식점 중심 46개 항목 (legal 11, tax 3, hr 8, grant 3)
- 목표: 업종별 최소 10개 항목 추가 (총 ~100+ 항목)
- 업종별 ActionKit 구조:
  - `LAW_DATA` 딕셔너리에 업종별 카테고리 추가
  - `ACTION_KIT_DATA`에 업종 공통 + 업종 특화 항목 분리
- 각 항목에 `target_business_types` 메타데이터 추가
- **Size**: XL (1~2일)

#### P5-2. 벡터 메타데이터 태깅 [M]

- **파일**: `app-backend/app/services/vector_store.py` 수정
- `_build_base_metadata()`에 `target_business_types` 필드 추가
- 기존 벡터에 업종 태그 소급 적용 (migration 스크립트)
- **Size**: M (2~4h)

#### P5-3. 업종별 벡터 필터링 검색 [M]

- **파일**: `app-backend/app/features/rag/application/rag_service.py` 수정
- retriever에 메타데이터 필터 적용:
  ```python
  self.retriever = self.vector_store.as_retriever(
      search_kwargs={
          "k": 5,
          "filter": {"target_business_types": {"$contains": business_type}}
      }
  )
  ```
- 업종 지정 없는 경우 전체 검색 (하위 호환)
- **Size**: M (2~4h)

---

## Risk Assessment

| # | 리스크 | 영향 | 확률 | 완화 방안 |
|---|---|---|---|---|
| R1 | **API Rate Limit 초과** | 중간 | 낮음 | 0.5초 간격 + asyncio.Semaphore(2), 일일 10,000건 한도 모니터링 |
| R2 | **법률 텍스트 파싱 오류** | 중간 | 중간 | XML 구조 사전 분석 + edge case 테스트, PDF fallback |
| R3 | **법률 유효성 (폐지/개정)** | 높음 | 중간 | `effective_date` + `last_verified_date` 메타데이터, 주기적 검증 스크립트 |
| R4 | **큐레이션 정확도** | 높음 | 높음 | LLM 1차 + 수동 2차 검증, 법률 전문가 리뷰 필요시 외부 자문 |
| R5 | **벡터 검색 정밀도 저하** | 높음 | 중간 | `target_business_types` 메타데이터 필터링, 교차 업종 오염 테스트 |
| R6 | **임베딩 비용 증가** | 낮음 | 높음 | text-embedding-3-small 유지 (저비용), 벡터 500~800건 추가는 ~$2 미만 |
| R7 | **LLM ETL 비용** | 중간 | 중간 | GPT-4 turbo 사용, 문서당 ~$0.05, 총 $1~2 수준 |
| R8 | **법률 저작권 문제** | 높음 | 낮음 | KOGL Type 1 (공공누리 1유형), 출처 표시만 하면 자유 이용 가능 |
| R9 | **stale 데이터 (법률 개정 후)** | 높음 | 중간 | `last_verified_date` 기반 90일 경과 경고, 분기별 재검증 프로세스 |
| R10 | **성숙한 Python 라이브러리 부재** | 낮음 | 확정 | 자체 thin wrapper 구현 (~100줄), 유지보수 부담 최소 |

---

## Success Metrics

| 지표 | 현재 | Phase 2 (Wave 1) | Phase 4 (Wave 3) | 비고 |
|---|---|---|---|---|
| 벡터DB 고유 문서 수 | 47 | 55+ | 80+ | 법률 + ActionKit |
| 벡터 수 (청킹 후) | ~317 | ~500 | ~1,000 | pgvector 인덱스 성능 모니터링 |
| 지원 업종 수 | 2 | 4 | 8 | 업종당 품질 게이트 통과 필요 |
| 업종당 법률 문서 수 | - | >= 3 | >= 3 | 법률+시행령+시행규칙 최소 |
| 검색 정밀도 (hit_rate@3) | 0.86 | >= 0.85 | >= 0.85 | regression 방지 |
| 교차 업종 오염률 | 미측정 | <= 10% | <= 10% | 비대상 업종 문서 검색 비율 |
| 업종별 fallback 비율 | 21% (음식점) | <= 10% | <= 10% | Wave별 품질 게이트 |
| 수집 자동화율 | 0% | 80%+ | 90%+ | 수동 큐레이션 제외 |

---

## Dependencies

### 코드 의존성

```
Phase 0 (독립)
└── API 등록 + 환경 설정

Phase 1 (독립, Phase 0 완료 후)
├── P1-1: API 클라이언트 래퍼 ← Phase 0
├── P1-2: 수집 CLI 스크립트 ← P1-1
└── P1-3: MolegApiSource 구현 ← P1-1

Phase 2 (Phase 1 완료 후)
├── P2-1: Wave 1 수집 실행 ← P1-2
├── P2-2: 관련 조문 큐레이션 ← P2-1
└── P2-3: Wave 1 벡터 적재 ← P2-2

Phase 3 (Wave 1 품질 게이트 통과 후)
├── P3-1~3: Wave 2 수집/큐레이션/적재 ← Phase 2 게이트

Phase 4 (Wave 2 품질 게이트 통과 후)
├── P4-1~3: Wave 3 수집/큐레이션/적재 ← Phase 3 게이트

Phase 5 (Phase 2 완료 후 시작 가능, Wave와 병렬)
├── P5-1: ActionKit 시드 확장 ← Phase 2 (법률 목록 확정 후)
├── P5-2: 벡터 메타데이터 태깅 ← P5-1
└── P5-3: 업종별 필터링 검색 ← P5-2
```

### 외부 의존성

| 의존성 | 상태 | 비고 |
|---|---|---|
| 국가법령정보센터 API | 미등록 | Phase 0에서 등록 |
| OpenAI API (GPT-4 turbo) | 운영 중 | ETL에 사용, 비용 ~$2 |
| OpenAI API (text-embedding-3-small) | 운영 중 | 임베딩에 사용 |
| PostgreSQL + pgvector | 운영 중 | law_vectors 컬렉션 |
| httpx (Python) | 미설치 | Phase 1에서 의존성 추가 |

### 상위 계획과의 관계

본 계획의 Phase 2~4 결과물은 `roadmap-quality-plan-v2.md`의 다음 태스크에 직접 입력된다:
- **P2A-2**: Wave 1 법률 문서 수집 + 벡터 적재
- **P2A-3**: Wave 1 매핑/Validate/쿼리 확장
- **P2B-1~3**: Wave 2 (동일 구조)
- **P2C-1~3**: Wave 3 (동일 구조)

---

## Timeline

| Phase | 예상 기간 | 우선순위 | 병렬 가능 |
|---|---|---|---|
| Phase 0: API 등록 | 0.5일 | 즉시 | - |
| Phase 1: 수집 스크립트 개발 | 2~3일 | Phase 0 후 | - |
| Phase 2: Wave 1 수집 | 2~3일 | Phase 1 후 | Phase 5와 병렬 |
| Phase 3: Wave 2 수집 | 2~3일 | Wave 1 게이트 후 | Phase 5와 병렬 |
| Phase 4: Wave 3 수집 | 2~3일 | Wave 2 게이트 후 | - |
| Phase 5: ActionKit 큐레이션 | 3~5일 | Phase 2 후 | Wave 2/3과 병렬 |

**총 예상**: ~12~17일 (병렬화 시 ~10~14일)

**크리티컬 패스**: Phase 0 → Phase 1 → Phase 2 → [게이트] → Phase 3 → [게이트] → Phase 4

---

## 기술 설계 메모

### law_api_client.py 핵심 구조 (예시)

```python
import httpx
import asyncio
from pydantic import BaseModel

class LawSearchResult(BaseModel):
    law_id: str           # MST 법령일련번호
    law_name: str         # 법령명
    law_type: str         # 법률/시행령/시행규칙
    effective_date: str   # 시행일자
    promulgation_date: str  # 공포일자

class LawApiClient:
    BASE_URL = "http://www.law.go.kr/DRF"

    def __init__(self, oc: str, rate_limit: float = 0.5):
        self.oc = oc
        self._semaphore = asyncio.Semaphore(2)
        self._rate_limit = rate_limit

    async def search_laws(self, query: str, ...) -> list[LawSearchResult]: ...
    async def get_law_full_text(self, mst: str) -> str: ...
    async def get_law_articles(self, mst: str) -> list[dict]: ...
    async def search_admin_rules(self, query: str) -> list[dict]: ...
```

### 메타데이터 스키마 (벡터 적재 시)

```python
{
    # 기존 필드
    "source": "law_etl" | "law_api",
    "title": "전자상거래 등에서의 소비자보호에 관한 법률",
    "category": "통신판매업",
    "summary": "...",
    "law_reference": "[전자상거래법] 제12조 (통신판매업자의 신고)",

    # 신규 필드
    "target_business_types": ["통신판매업", "온라인쇼핑몰"],
    "effective_date": "2026-01-01",
    "last_verified_date": "2026-02-25",
    "law_hierarchy": "법률",        # 법률/시행령/시행규칙/행정규칙
    "law_id": "MST_123456",         # 국가법령정보센터 ID
    "source_url": "https://www.law.go.kr/법령/전자상거래법",
    "chunk_index": 0,
    "total_chunks": 5,
}
```

### 디렉토리 구조 (수집 후)

```
app-backend/.temp/rag/
├── 음식점/           # 기존
│   ├── chapter-1/
│   └── chapter-2/
├── 식품제조가공업/     # Wave 1
│   ├── 식품위생법.md
│   ├── 식품위생법_시행령.md
│   └── 식품위생법_시행규칙.md
├── 통신판매업/         # Wave 1
│   ├── 전자상거래법.md
│   ├── 전자상거래법_시행령.md
│   └── 전자상거래법_시행규칙.md
├── 미용업/            # Wave 2
├── 일반소매업/         # Wave 2
├── 학원업/            # Wave 3
└── 숙박업/            # Wave 3
```
