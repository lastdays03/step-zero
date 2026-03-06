# 로드맵 템플릿 관리 시스템 — 수동 테스트 가이드

> 대상: Phase 2 + 3 (백엔드 + 프론트엔드)
> 브랜치: `feature/2-template-system`
> 최종 업데이트: 2026-03-02

---

## 0. 사전 준비

### 0-1. 서비스 시작

```bash
# 전체 스택 (DB + Redis + Backend + Worker + Frontend)
docker compose -f docker-compose.dev.yml up -d --build

# 또는 개별 실행
docker compose -f docker-compose.dev.yml up -d app-db app-redis  # DB + Redis
cd app-backend && make run                                        # 백엔드 (port 8000)
cd app-backend && make worker                                     # ARQ 워커
cd app-frontend && npm run dev                                    # 프론트엔드 (port 3000)
```

### 0-2. 마이그레이션 적용 확인

```bash
# Docker 환경
docker compose -f docker-compose.dev.yml exec app-backend python -m alembic upgrade head

# 로컬 환경
cd app-backend && make migrate-up
```

### 0-3. 테스트 계정

| 역할 | 이메일 | 비밀번호 | 조건 |
|------|--------|----------|------|
| **운영자 (superuser)** | 기존 테스트 계정 | - | `is_superuser=True` 필수 |
| **일반 사용자** | 기존 테스트 계정 | - | `is_superuser=False` |

> 운영 콘솔 접근은 `is_superuser=True`인 계정만 가능합니다.

### 0-4. 테스트용 로드맵 준비

템플릿 역생성 테스트를 위해 **기존 로드맵 1개 이상** 필요합니다.
- 로그인 → "나의 로드맵" → 새 로드맵 생성 (예: 업종 "카페", 지역 "서울시 강남구")
- 생성 완료 후 **로드맵 UUID** 메모 (URL에서 확인: `/roadmap/{UUID}`)

---

## 1. 진입 경로 테스트

### TC-1.1 Ops 홈 카드 확인

| 항목 | 내용 |
|------|------|
| **전제조건** | superuser 계정으로 로그인 |
| **경로** | 사이드바 "운영 콘솔" 클릭 → `/ops` |
| **확인사항** | |
| ✅ | 7개 카드 그리드에 **"로드맵 템플릿 관리"** 카드 존재 |
| ✅ | 설명: "업종별 로드맵 템플릿 검수 및 승인" |
| ✅ | "열기" 클릭 → `/ops/roadmap-templates` 이동 |

### TC-1.2 비운영자 접근 차단

| 항목 | 내용 |
|------|------|
| **전제조건** | 일반 사용자 계정으로 로그인 |
| **경로** | 주소창에 직접 `localhost:3000/ops/roadmap-templates` 입력 |
| **확인사항** | |
| ✅ | 접근 차단 플레이스홀더 표시 (OpsAccessPlaceholder) |
| ✅ | 템플릿 목록 노출 안 됨 |

---

## 2. 목록 페이지 테스트 (`/ops/roadmap-templates`)

### TC-2.1 초기 로딩

| 항목 | 내용 |
|------|------|
| **전제조건** | superuser 로그인, 템플릿 0개인 상태 |
| **확인사항** | |
| ✅ | 페이지 타이틀: "로드맵 템플릿 관리" + FileStack 아이콘 |
| ✅ | 통계 카드 5개 표시: 전체(0), 초안(0), 검토중(0), 승인(0), 보관(0) |
| ✅ | 상태 탭 5개: 전체, 초안, 검토중, 승인, 보관 |
| ✅ | 테이블에 "데이터가 없습니다." 또는 빈 행 표시 |
| ✅ | "로드맵에서 생성" 버튼 존재 (파란색) |
| ✅ | "새로고침" 버튼 존재 |

### TC-2.2 로드맵에서 템플릿 생성 (역생성)

| 항목 | 내용 |
|------|------|
| **전제조건** | 테스트용 로드맵 UUID 준비 |
| **조작** | "로드맵에서 생성" 버튼 클릭 |
| **확인사항** | |
| ✅ | Dialog 열림: "로드맵에서 템플릿 생성" 제목 |
| ✅ | 로드맵 ID 입력 필드 존재 |
| ✅ | 빈 상태에서 "생성" 버튼 클릭 → 유효성 에러 또는 API 에러 표시 |
| ✅ | **유효한 UUID 입력 → "생성" 클릭** |
| ✅ | 로딩 상태 (버튼 disabled, 텍스트 변경) |
| ✅ | 성공 → Dialog 자동 닫힘 |
| ✅ | 목록 자동 새로고침 → 방금 생성한 DRAFT 템플릿 표시 |
| ✅ | 통계 카드 업데이트: 전체 1, 초안 1 |
| **실패 케이스** | |
| ✅ | 존재하지 않는 UUID 입력 → 인라인 에러 메시지 ("Not found" 등) |
| ✅ | Dialog가 닫히지 않고 에러만 표시 |

### TC-2.3 상태 탭 필터

| 항목 | 내용 |
|------|------|
| **전제조건** | 템플릿 1개 이상 존재 (DRAFT 상태) |
| **조작** | 각 탭 클릭 |
| **확인사항** | |
| ✅ | "전체" 탭 → 모든 템플릿 표시 |
| ✅ | "초안" 탭 → DRAFT만 표시 |
| ✅ | "검토중" 탭 → 해당 없으면 빈 목록 |
| ✅ | 선택된 탭에 파란색 밑줄 표시 |
| ✅ | 하단 카운트: "총 N개 (전체 M개 중)" 형식 |

### TC-2.4 업종 필터

| 항목 | 내용 |
|------|------|
| **전제조건** | 서로 다른 업종의 템플릿 2개 이상 |
| **확인사항** | |
| ✅ | 업종 필터 드롭다운 표시됨 (업종 2개 이상일 때만) |
| ✅ | "전체 업종" 선택 → 모든 템플릿 표시 |
| ✅ | 특정 업종 선택 → 해당 업종만 표시 |
| ✅ | 상태 탭 + 업종 필터 동시 적용 |

### TC-2.5 목록 테이블 컬럼 확인

| 컬럼 | 확인사항 |
|------|----------|
| 업종 | business_type 표시 |
| 창업방식 | startup_method 표시, null이면 "-" |
| 제목 | 클릭 → 상세 페이지 이동 (`/ops/roadmap-templates/{id}`) |
| 상태 | 상태 배지 (색상별 구분: DRAFT=회색, REVIEW=노란색, APPROVED=초록색, ARCHIVED=회색) |
| 버전 | 숫자 표시 |
| 생성일 | 날짜 표시 |
| 액션 | 삭제 버튼 (DRAFT/REVIEW만), 상세 보기 버튼 |

### TC-2.6 삭제

| 항목 | 내용 |
|------|------|
| **전제조건** | DRAFT 상태 템플릿 존재 |
| **조작** | 삭제 버튼 클릭 |
| **확인사항** | |
| ✅ | 확인 다이얼로그 표시 (브라우저 confirm) |
| ✅ | "확인" → 삭제 성공 → 목록에서 제거 |
| ✅ | "취소" → 삭제 안 됨 |
| ✅ | APPROVED 상태 → 삭제 버튼 없음 (또는 비활성) |

---

## 3. 상세 페이지 테스트 (`/ops/roadmap-templates/{id}`)

### TC-3.1 헤더 영역

| 항목 | 내용 |
|------|------|
| **확인사항** | |
| ✅ | 뒤로가기 버튼 (←) → 목록 페이지로 이동 |
| ✅ | 템플릿 제목 표시 |
| ✅ | 상태 배지 표시 |
| ✅ | 버전 표시 (v1, v2 ...) |
| ✅ | 업종 / 창업방식 부제 표시 |

### TC-3.2 기본 정보 수정 (DRAFT/REVIEW만)

| 항목 | 내용 |
|------|------|
| **전제조건** | DRAFT 상태 템플릿 |
| **확인사항** | |
| ✅ | "기본 정보 수정" 카드 표시 (DRAFT/REVIEW에서만) |
| ✅ | 3개 필드: 제목, 업종, 창업방식 |
| ✅ | 기존 값이 input에 미리 채워짐 |
| ✅ | **제목 수정 → "저장" 클릭** |
| ✅ | 저장 중 버튼 "저장 중..." 표시 + disabled |
| ✅ | 성공 → 헤더 제목 즉시 반영 |
| ✅ | **업종 수정 → 저장 → 반영 확인** |
| ✅ | **창업방식 입력 → 저장 → 부제에 반영** |
| ✅ | APPROVED 상태 → "기본 정보 수정" 카드 안 보임 |

### TC-3.3 정보 카드

| 항목 | 내용 |
|------|------|
| **확인사항** | |
| ✅ | 예상 소요일 카드: 모든 스텝의 estimated_days 합산 |
| ✅ | 단계 수 카드: 스텝 개수 |
| ✅ | 총 액션 수 카드: 모든 스텝의 액션 합산 |

---

## 4. 상태 워크플로우 테스트

### TC-4.1 DRAFT → REVIEW (검토 요청)

| 항목 | 내용 |
|------|------|
| **전제조건** | DRAFT 상태 템플릿 상세 페이지 |
| **조작** | 헤더 우측 "검토 요청" 버튼 클릭 |
| **확인사항** | |
| ✅ | StatusChangeDialog 열림 |
| ✅ | "초안 → 검토중" 상태 변경 표시 (배지 2개 + 화살표) |
| ✅ | 사유 입력 Textarea 존재 (선택사항) |
| ✅ | 사유 입력 없이 "변경" 클릭 → 성공 |
| ✅ | 상태 배지 "검토중" (노란색)으로 변경 |
| ✅ | 상태 버튼이 "승인" + "반려" 로 변경됨 |

### TC-4.2 REVIEW → APPROVED (승인)

| 항목 | 내용 |
|------|------|
| **전제조건** | REVIEW 상태 템플릿 |
| **조작** | "승인" 버튼 클릭 |
| **확인사항** | |
| ✅ | StatusChangeDialog 열림: "검토중 → 승인" |
| ✅ | 사유 입력 후 "변경" 클릭 |
| ✅ | 상태 "승인" (초록색)으로 변경 |
| ✅ | "기본 정보 수정" 카드 사라짐 (편집 불가) |
| ✅ | 상태 버튼이 "보관 처리"만 남음 |

### TC-4.3 REVIEW → DRAFT (반려)

| 항목 | 내용 |
|------|------|
| **전제조건** | REVIEW 상태 템플릿 |
| **조작** | "반려 (초안으로)" 버튼 클릭 (빨간색 outline) |
| **확인사항** | |
| ✅ | StatusChangeDialog 열림: "검토중 → 초안" |
| ✅ | 사유 입력 → "변경" 클릭 |
| ✅ | 상태 "초안" (회색)으로 복귀 |
| ✅ | "기본 정보 수정" 카드 다시 표시 |

### TC-4.4 APPROVED → ARCHIVED (보관)

| 항목 | 내용 |
|------|------|
| **전제조건** | APPROVED 상태 템플릿 |
| **조작** | "보관 처리" 버튼 클릭 |
| **확인사항** | |
| ✅ | 상태 "보관" (회색)으로 변경 |
| ✅ | 모든 상태 변경 버튼 사라짐 (종료 상태) |

### TC-4.5 잘못된 상태 전이 차단

| 시나리오 | 기대 결과 |
|---------|----------|
| DRAFT → APPROVED 직접 전이 | UI에 해당 버튼 없음 (BE: 400 에러) |
| ARCHIVED → 다른 상태 | UI에 상태 버튼 없음 (종료 상태) |

---

## 5. 스텝 아코디언 테스트

### TC-5.1 스텝 표시

| 항목 | 내용 |
|------|------|
| **확인사항** | |
| ✅ | "단계 (N)" 섹션 타이틀에 스텝 수 표시 |
| ✅ | 각 스텝 카드: phase, title, objective, estimated_days, risk_notes 표시 |
| ✅ | 아코디언 접기/펼치기 동작 |
| ✅ | 펼치면 3개 카테고리 표시: 체크리스트, 법적 근거, 서류/양식 |

### TC-5.2 빈 카테고리 처리

| 항목 | 내용 |
|------|------|
| **전제조건** | DRAFT 상태, 특정 카테고리에 액션 0개 |
| **확인사항** | |
| ✅ | 편집 가능(DRAFT/REVIEW) → 빈 카테고리도 렌더링됨 (＋ 추가 가능) |
| ✅ | 편집 불가(APPROVED/ARCHIVED) → 빈 카테고리는 "등록된 액션이 없습니다." 또는 숨김 |

---

## 6. 액션 CRUD 테스트

### TC-6.1 액션 추가

| 항목 | 내용 |
|------|------|
| **전제조건** | DRAFT 상태 템플릿 → 스텝 아코디언 펼침 |
| **조작** | 체크리스트 섹션 하단 "＋ 추가" 버튼 클릭 |
| **확인사항** | |
| ✅ | 인라인 입력 폼 토글 (제목, 설명, URL 필드) |
| ✅ | 제목 빈 상태로 "저장" → 유효성 에러 (제목 필수) |
| ✅ | **제목 입력 → "저장" 클릭** |
| ✅ | 저장 중 버튼 disabled |
| ✅ | 성공 → 인라인 폼 닫힘 → 액션 목록에 새 항목 표시 |
| ✅ | action_type이 섹션에 맞게 자동 설정됨 (CHECKLIST/LEGAL_BASIS/DOCUMENT) |
| ✅ | "취소" 클릭 → 폼 닫힘, 저장 안 됨 |

### TC-6.2 액션 수정

| 항목 | 내용 |
|------|------|
| **전제조건** | DRAFT 상태, 기존 액션 1개 이상 |
| **조작** | 액션 행의 연필(Pencil) 아이콘 클릭 |
| **확인사항** | |
| ✅ | 해당 행이 편집 모드로 전환 (input 필드들) |
| ✅ | 기존 값이 미리 채워짐 (title, description, source_url) |
| ✅ | **제목 수정 → "저장" 클릭** |
| ✅ | 성공 → 편집 모드 해제 → 수정된 값 표시 |
| ✅ | "취소" → 편집 모드 해제, 원래 값 유지 |
| ✅ | APPROVED 상태 → 연필 아이콘 없음 (편집 불가) |

### TC-6.3 액션 삭제

| 항목 | 내용 |
|------|------|
| **전제조건** | DRAFT 상태, 기존 액션 1개 이상 |
| **조작** | 액션 행의 휴지통(Trash2) 아이콘 클릭 |
| **확인사항** | |
| ✅ | 삭제 확인 (confirm 또는 즉시 삭제) |
| ✅ | 삭제 후 목록에서 제거 |
| ✅ | 정보 카드의 "총 액션" 수 감소 |

---

## 7. API 직접 테스트 (Swagger UI)

> **URL**: `http://localhost:8000/docs` → "ops-roadmap-templates" 태그

### TC-7.1 통계 조회

```
GET /api/v1/ops/roadmap-templates/summary
Authorization: Bearer {admin_token}

기대 응답: { "total": N, "draft": N, "review": N, "approved": N, "archived": N }
```

### TC-7.2 목록 조회 (필터)

```
GET /api/v1/ops/roadmap-templates?status=DRAFT&business_type=휴게음식점
Authorization: Bearer {admin_token}

기대: 해당 조건의 템플릿 배열
```

### TC-7.3 상세 조회 (중첩 구조)

```
GET /api/v1/ops/roadmap-templates/{id}
Authorization: Bearer {admin_token}

기대 응답 구조:
{
  "id": 1,
  "business_type": "휴게음식점",
  "status": "DRAFT",
  "steps": [
    {
      "id": 1,
      "phase": "준비",
      "title": "사전 준비",
      "actions": [
        {
          "id": 1,
          "action_type": "CHECKLIST",
          "title": "사업자등록"
        }
      ]
    }
  ]
}
```

### TC-7.4 역생성

```
POST /api/v1/ops/roadmap-templates/from-roadmap
Authorization: Bearer {admin_token}
Content-Type: application/json

{ "roadmap_id": "UUID-HERE" }

기대: DRAFT 상태 템플릿 생성 + 원본 로드맵의 스텝/액션 복사
```

### TC-7.5 상태 변경

```
PATCH /api/v1/ops/roadmap-templates/{id}/status
Authorization: Bearer {admin_token}
Content-Type: application/json

{ "new_status": "REVIEW", "reason": "검토 요청합니다" }

기대: 유효 전이 → 200 + 변경된 상태, 무효 전이 → 400
```

### TC-7.6 비운영자 접근 차단

```
GET /api/v1/ops/roadmap-templates/summary
Authorization: Bearer {normal_user_token}

기대: 403 Forbidden
```

---

## 8. 파이프라인 통합 테스트

### TC-8.1 APPROVED 템플릿 기반 로드맵 생성

| 항목 | 내용 |
|------|------|
| **전제조건** | APPROVED 상태 템플릿 1개 (예: business_type="휴게음식점") |
| **조작** | 일반 사용자 로그인 → 새 로드맵 생성 (업종: "카페" → 정규화: "휴게음식점") |
| **확인사항** | |
| ✅ | 로드맵 생성 시간이 기존 대비 빨라짐 (LLM 호출 스킵) |
| ✅ | 생성된 로드맵의 스텝/액션이 템플릿 내용과 일치 |
| ✅ | DB에서 `roadmap.template_id`가 해당 템플릿 ID로 설정됨 |

### TC-8.2 템플릿 없는 업종 → 자동 DRAFT 등록

| 항목 | 내용 |
|------|------|
| **전제조건** | 해당 업종의 템플릿이 0개 |
| **조작** | 새 로드맵 생성 (처음 보는 업종) |
| **확인사항** | |
| ✅ | 기존 파이프라인 (ActionKit + RAG) 으로 로드맵 생성 |
| ✅ | Ops 콘솔에 해당 업종의 DRAFT 템플릿 자동 등록됨 |
| ✅ | 동일 업종으로 다시 생성 → 중복 DRAFT 미등록 |

### TC-8.3 템플릿 없는 기존 업종 → 기존 경로 100% 호환

| 항목 | 내용 |
|------|------|
| **전제조건** | APPROVED 템플릿이 없는 업종 |
| **확인사항** | |
| ✅ | 기존과 동일하게 ActionKit 매칭 → LLM 개인화 → 로드맵 생성 |
| ✅ | 에러 없음, 결과물 정상 |

---

## 9. 감사로그 확인

### TC-9.1 상태 변경 감사로그

| 항목 | 내용 |
|------|------|
| **조작** | 템플릿 상태 변경 수행 (DRAFT → REVIEW 등) |
| **확인사항** | |
| ✅ | `/ops/audit-logs` 페이지에서 `template.status.changed` 액션 확인 |
| ✅ | 대상: `roadmap_template`, target_id = 템플릿 ID |
| ✅ | meta에 before/after 상태 정보 포함 |
| ✅ | reason이 있으면 기록됨 |

---

## 10. 자동화 테스트 현황

### 백엔드 (pytest)

```bash
cd app-backend && .venv/bin/pytest -q
# 예상: 174 passed, 19 skipped
```

| 테스트 파일 | 테스트 수 | 내용 |
|-----------|:--------:|------|
| `tests/api/test_ops_roadmap_templates.py` | 9개 | summary, list, create-from-roadmap, detail, update-meta, status-transition(유효/무효), delete, 비운영자 접근 |
| `tests/services/test_template_resolver.py` | 6개 | exact match, common fallback, no match, to_steps_payload, auto-draft(미존재), auto-draft(이미존재) |

### 프론트엔드 (lint + build)

```bash
cd app-frontend && npm run lint    # 0 errors
cd app-frontend && npm run build   # 성공 (19 static pages)
```

---

## 11. 테스트 체크리스트 요약

| # | 테스트 | 상태 |
|---|--------|:----:|
| 1.1 | Ops 홈 카드 진입 | ☐ |
| 1.2 | 비운영자 접근 차단 | ☐ |
| 2.1 | 목록 초기 로딩 | ☐ |
| 2.2 | 로드맵에서 템플릿 생성 (역생성) | ☐ |
| 2.3 | 상태 탭 필터 | ☐ |
| 2.4 | 업종 필터 | ☐ |
| 2.5 | 테이블 컬럼 확인 | ☐ |
| 2.6 | 삭제 | ☐ |
| 3.1 | 상세 헤더 | ☐ |
| 3.2 | 기본 정보 수정 | ☐ |
| 3.3 | 정보 카드 | ☐ |
| 4.1 | DRAFT → REVIEW | ☐ |
| 4.2 | REVIEW → APPROVED | ☐ |
| 4.3 | REVIEW → DRAFT (반려) | ☐ |
| 4.4 | APPROVED → ARCHIVED | ☐ |
| 4.5 | 잘못된 상태 전이 차단 | ☐ |
| 5.1 | 스텝 아코디언 표시 | ☐ |
| 5.2 | 빈 카테고리 처리 | ☐ |
| 6.1 | 액션 추가 | ☐ |
| 6.2 | 액션 수정 | ☐ |
| 6.3 | 액션 삭제 | ☐ |
| 7.1~7.6 | API 직접 테스트 (Swagger) | ☐ |
| 8.1 | APPROVED 템플릿 기반 생성 | ☐ |
| 8.2 | 자동 DRAFT 등록 | ☐ |
| 8.3 | 기존 경로 호환성 | ☐ |
| 9.1 | 감사로그 확인 | ☐ |
