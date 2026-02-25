# 실행 순서 가이드 - 로드맵 품질 개선 + 법률 데이터 수집

> Last Updated: 2026-02-25
> 이 문서는 두 트랙의 최적 병렬 실행 순서를 정리한 빠른 참조 문서이다.

---

## 병렬 트랙 구조

| 트랙 | 목표 | 상세 계획 |
|---|---|---|
| **Track A: 로드맵 품질 개선** | 기존 음식점 fallback 제거 + ACTIONKIT_RAG 활성화 | `roadmap-quality-plan-v2.md` |
| **Track B: 법률 데이터 수집** | 6개 업종 법률 문서 수집 + 벡터 적재 | `../law-data-collection/law-data-collection-plan.md` |

---

## 최적 진행 순서

```
시간 -->

[Track A: 로드맵 품질 개선]              [Track B: 법률 데이터 수집]
================================        ================================

구간 1 (2~3일) - 독립 병렬, 즉시 시작
--------------------------------        --------------------------------
P0-1: Baseline 스크립트                  API 등록 + 환경설정 (P0-1~4)
P0-2: 품질 메타 Migration               수집 스크립트 개발
P1-QW: FE Quick Win 3건                 (law_api_client.py, fetch_laws.py)
        |                                       |
        v                                       v

구간 2 (3~5일) - 핵심 개선 + 데이터 수집 병렬
--------------------------------        --------------------------------
P1-1: 비법률 fallback 개선               Wave 1 법률 수집
P1-2: ActionKit 쿼리 개선               (식품제조가공업 + 통신판매업)
P1-5: ACTIONKIT_RAG 해소                 수집 + 큐레이션 + 검증
P3-2: Fallback UX 개선                          |
        |                                       |
        v                                       v
============= 여기서 합류 ============================
        |
        v

구간 3 (5일/Wave) - 업종 확장 순차
--------------------------------
P2A: Wave 1 업종 확장
     벡터 적재 + 매핑 + Validate
        |
        v (품질 게이트 통과)
Wave 2 수집 --> P2B (미용업 + 소매업) --> 게이트
        |
        v
Wave 3 수집 --> P2C (학원업 + 숙박업) --> 게이트
```

---

## 구간별 상세

### 구간 1: 독립 병렬 (2~3일)

모든 작업이 상호 의존성 없으며, 즉시 시작 가능하다.

**Track A**
| 태스크 | 내용 | 크기 |
|---|---|---|
| P0-1 | 품질 평가 스크립트 + Baseline 측정 | S |
| P0-2 | 품질 메타데이터 태깅 + DB Migration (Alembic) | S |
| P1-QW | FE Quick Win 3건 (TimelinePhaseCard, SUGGESTIONS 통합, validate 에러) | XS |

**Track B**
| 태스크 | 내용 | 크기 |
|---|---|---|
| B-P0 | open.law.go.kr 회원가입, OC 발급, 환경변수 설정, httpx 추가 | XS |
| B-P1-1 | `law_api_client.py` API 클라이언트 래퍼 | M |
| B-P1-2~4 | `fetch_laws.py` CLI 스크립트 + 유닛 테스트 + 설정 | L |
| B-P1-5 | `MolegApiSource` 구현체 | M |

---

### 구간 2: 핵심 개선 + 데이터 수집 병렬 (3~5일)

Track A는 **기존 음식점 데이터만으로 충분**하며, 새 법률 데이터가 불필요하다.
Track B는 수집 스크립트 완성 후 Wave 1 실행 단계이다.

**Track A**
| 태스크 | 의존 | 내용 |
|---|---|---|
| P1-1 | P0-2 | 비법률 단계 fallback 로직 개선 (`_fallback_detail()` 외 3곳) |
| P1-2 | P0-1 | ActionKit 쿼리 개선 (다중 쿼리 전략, `asyncio.gather`) |
| P1-5 | P1-2 | ACTIONKIT_RAG 미활성 원인 분석 + 해소 |
| P3-2 | P0-2, P1-1 | Fallback UX 개선 (FE, P1-1과 동시 진행 가능) |

**Track B**
| 태스크 | 내용 |
|---|---|
| B-P2-1 | Wave 1 법률 수집 실행 (`fetch_laws --wave 1`) |
| B-P2-2 | 관련 조문 큐레이션 (LLM 1차 + 수동 2차) -- 핵심 병목 |
| B-P2-3 | Wave 1 벡터 적재 (`seed_rag_vectors --wave 1`) |

---

### 구간 3: 합류 - 업종 확장 (Wave당 5일)

Track B의 수집 결과물이 Track A의 업종 확장에 직접 입력된다.

**Wave 1 (식품제조가공업 + 통신판매업)**
| 태스크 | 내용 |
|---|---|
| P2A-2 | Wave 1 벡터 적재 (수집된 법률 문서 필요) |
| P2A-3 | 매핑/Validate/쿼리 확장 |
| 게이트 | fallback < 10%, ActionKit >= 3건, 기존 hit_rate >= 0.85, 교차 오염 통과 |

**Wave 2 (미용업 + 일반소매업)** -- Wave 1 게이트 통과 후
| 태스크 | 내용 |
|---|---|
| B-P3-1~3 | Wave 2 수집/큐레이션/적재 |
| P2B-1~3 | Wave 2 매핑/확장/검증 |

**Wave 3 (학원업 + 숙박업)** -- Wave 2 게이트 통과 후
| 태스크 | 내용 |
|---|---|
| B-P4-1~3 | Wave 3 수집/큐레이션/적재 |
| P2C-1~3 | Wave 3 매핑/확장/검증 |

---

### 구간 4: Phase 3 Ops (Phase 2A 완료 후 병렬 가능)

| 태스크 | 의존 | 내용 |
|---|---|---|
| P3-1 | P2A-1 (업종 목록 확정) | 업종 선택 가이드 FE (2-tier SUGGESTIONS) |
| P3-3 | P0-2 | 로드맵 품질 대시보드 (`/ops/roadmap-quality`) |
| P3-4 | P2A-2 (법률 적재) | 골든 데이터셋 확장 (업종당 3건+) |

---

## 데이터 수집 없이 먼저 할 수 있는 것

기존 DB와 코드만으로 즉시 착수 가능한 작업 목록이다.

| 태스크 | 성격 | 이유 |
|---|---|---|
| P0-1: Baseline 측정 | 백엔드 스크립트 | 기존 DB만 필요 |
| P0-2: 품질 메타 Migration | DB 스키마 | Alembic 컬럼 추가만 |
| P1-1: 비법률 fallback 개선 | 백엔드 로직 | 코드 분기 변경, 기존 데이터로 검증 |
| P1-2: ActionKit 쿼리 개선 | 백엔드 로직 | 기존 음식점 벡터로 검증 |
| P1-5: ACTIONKIT_RAG 해소 | 백엔드 로직 | 기존 데이터로 검증 |
| P1-QW: FE Quick Win 3건 | 프론트엔드 | 백엔드 의존 없음 |
| P3-2: Fallback UX 개선 | 프론트엔드 | P1-1 분류 기준만 필요 |

---

## 데이터 수집이 선행되어야 하는 것

Track B 결과물(수집된 법률 문서 + 벡터 적재)이 반드시 있어야 하는 작업이다.

| 태스크 | 필요한 데이터 |
|---|---|
| P2A-2, P2B-2, P2C-2: 업종 확장 벡터 적재 | 해당 Wave의 법률 문서 수집 완료 |
| P2A-3, P2B-3, P2C-3: 매핑/Validate 확장 | 해당 Wave의 벡터 적재 완료 |
| P3-1: 업종 선택 가이드 FE | 업종 목록 확정 (P2A-1) |
| P3-4: 골든 데이터셋 확장 | 법률 문서 적재 완료 |

---

## 일정 비교

| 방식 | 예상 기간 | 비고 |
|---|---|---|
| 순차 진행 (A 완료 후 B) | ~25일 | Track A Phase 1 (4일) + Track B 전체 (12~17일) + 업종 확장 (15일) |
| **병렬 진행 (권장)** | **~18일** | 구간 1~2에서 약 7일 단축 |

```
순차:  [--- Track A Phase 0~1 (4일) ---][--- Track B (14일) ---][--- 업종 확장 (15일) ---] = ~25일+

병렬:  [- 구간1 (3일) -][- 구간2 (5일) -][- 구간3: Wave1 (5일) -][- Wave2 (5일) -][- Wave3 (5일) -]
       A: P0 + QW        A: P1 전체        합류: P2A                 P2B               P2C
       B: P0 + P1        B: Wave1 수집      B결과 --> A에 입력
                                                                    = ~18일 (크리티컬 패스)
```

---

## 관련 문서

| 문서 | 경로 |
|---|---|
| 로드맵 품질 개선 상세 계획 | `dev/active/roadmap-quality/roadmap-quality-plan-v2.md` |
| 로드맵 품질 태스크 체크리스트 | `dev/active/roadmap-quality/roadmap-quality-tasks.md` |
| 법률 데이터 수집 상세 계획 | `dev/active/law-data-collection/law-data-collection-plan.md` |
| 법률 데이터 수집 태스크 체크리스트 | `dev/active/law-data-collection/law-data-collection-tasks.md` |
