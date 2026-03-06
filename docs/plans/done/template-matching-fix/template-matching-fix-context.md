# 템플릿 매칭 수정 — 컨텍스트

Last Updated: 2026-03-02

## 핵심 파일 맵

### 수정 대상

| 파일 | 역할 | 핵심 라인 |
|------|------|----------|
| `app-backend/app/features/roadmaps/application/template_resolver.py` | 매칭 로직 | L20-90 `resolve()`, L168-194 `should_create_auto_draft()` |
| `app-backend/tests/services/test_template_resolver.py` | 단위 테스트 | L26-64 `_create_approved_template` 헬퍼 |

### 참조 (읽기 전용)

| 파일 | 역할 | 참조 포인트 |
|------|------|-----------|
| `app-backend/app/features/roadmaps/application/roadmap_generation_service.py` | 생성 서비스 | L208-214 resolve() 호출부 |
| `app-backend/app/models/roadmap_template.py` | DB 모델 | L1-40 RoadmapTemplate 정의 |
| `app-backend/app/api/v1/ops/roadmap_template_schemas.py` | API 스키마 | L78-82 UpdateRequest |
| `app-backend/app/features/ops/application/roadmap_templates/service.py` | 관리 서비스 | L109-196 create_template_from_roadmap() |
| `app-backend/alembic/versions/011_template_startup_type.py` | 마이그레이션 | startup_type 컬럼 추가 |

## 아키텍처 결정사항

### D-1: 5단계 우선순위 채택

**결정**: btype+stype를 2순위(btype+smethod)와 4순위(btype만) 사이 3순위로 배치

**근거**:
- startup_method(신규/양수양도/프랜차이즈)가 프로세스 단계에 더 큰 영향
- startup_type(개인사업자/법인)은 법률/세무 차이에 영향
- → smethod가 stype보다 높은 우선순위가 적절

### D-2: should_create_auto_draft() 미수정

**결정**: 현행 유지

**근거**:
- auto-draft는 exact 조합 기준으로 판단하는 것이 맞음
- 공통 템플릿(NULL 필드)이 있어도 특정 조합용 DRAFT를 생성하는 것이 유용
- 추후 관리자가 REVIEW → APPROVED로 승격하면 정확 매칭에 활용

### D-3: ISSUE-1(데이터 불일치) 별도 처리

**결정**: 이번 작업 범위에서 제외

**근거**:
- 이전 코드 버전에서 발생한 역사적 데이터
- 코드 수정으로 해결 불가, SQL 수동 수정 필요
- 이미 생성된 로드맵의 콘텐츠에는 영향 없음

## 의존성

```
template_resolver.py (수정)
    ↑ 호출
roadmap_generation_service.py:208-214 (변경 없음)
    ↑ 호출
app-worker / process_job() (변경 없음)
```

## DB 스키마 참조

```sql
-- roadmap_templates 테이블 (기존)
business_type   VARCHAR NOT NULL  -- 인덱싱됨
startup_method  VARCHAR NULL      -- 인덱싱됨
startup_type    VARCHAR NULL      -- 인덱싱됨 (011 마이그레이션)
status          VARCHAR NOT NULL  -- DRAFT/REVIEW/APPROVED/ARCHIVED

-- 복합 인덱스 (기존)
ix_roadmap_templates_btype_smethod_stype_status
    (business_type, startup_method, startup_type, status)
```

→ 새 3순위 쿼리(`btype + stype + smethod IS NULL`)도 복합 인덱스 활용 가능 (prefix 매칭)

## 테스트 환경

- DB: SQLite in-memory (`sqlite+aiosqlite`)
- `tests/conftest.py`에서 테스트 유저/팀 시드
- `_create_approved_template` 헬퍼로 테스트 데이터 생성
- 각 테스트에서 고유한 business_type 사용하여 격리
