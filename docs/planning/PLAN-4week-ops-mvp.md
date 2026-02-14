# StepZero 4주 운영 MVP 상세 실행 계획

## 1. 문서 목적
- 목표: 4주 내 "사용자 기능 데모" 수준을 넘어 실제 운영 가능한 최소 기능 세트를 구현한다.
- 기준:
- 기능 개발 범위를 축소하고 운영 필수 요소를 우선 반영한다.
- 고위험 리스크(잘못된 법령 안내)를 먼저 통제한다.

## 2. 이번 4주 범위 (In Scope)

### 2.1 사용자 프로필 관리
- 프로필 조회/수정:
- 이름, 지역, 업종, 창업 단계
- 프로필 완성도 계산(예: 필수 필드 기준 %)
- 접근 제어:
- 본인 프로필만 수정 가능
- 운영자(Admin)는 조회 가능

### 2.2 운영 최소 관리(Admin)
- 사용자 관리:
- 사용자 목록 조회, 상태 변경(활성/정지)
- 공지사항:
- 공지 생성/수정/게시/내림
- 커뮤니티 모더레이션:
- 신고 목록 조회
- 게시글/댓글 숨김 처리(soft delete)

### 2.3 액션키트 4개 상세 페이지
- 카테고리:
- 법률 / 세무 / 공고 / HR
- 상세 페이지 공통 요소:
- 제목, 요약, 적용 대상(지역/업종/단계), 근거 출처 링크, 최신 업데이트 일시
- 사용자 액션:
- 스크랩/즐겨찾기
- 오류 신고 버튼
- 고지:
- "정책/법령 최신성은 변동 가능" 경고 문구 상시 노출

### 2.4 커뮤니티 최소 실사용 기능
- 피드:
- 지역 기반/업종 기반 탭
- 게시글:
- 작성/수정/삭제(작성자), 태그(지역/업종/주제)
- 댓글/좋아요:
- 기본 상호작용 제공
- 신고:
- 신고 사유 선택 + 신고 접수
- 운영 처리:
- 운영자 숨김/복구

## 3. 이번 4주 제외 범위 (Out of Scope)
- 결제/구독/청구
- OCR 자동 심사
- 고급 추천/랭킹/멘토 매칭 고도화
- 다중 에이전트 도입
- 완전 자동 법령 최신화 파이프라인(이번엔 최소 게이트만)

## 4. 운영 리스크 기준 및 정책

### 4.1 최우선 리스크
- 리스크: "폐지/변경된 법령 또는 공고를 최신 정보처럼 안내"

### 4.2 치명 오류 정의
- 치명 오류(Fatal): 폐지/실효된 법령·공고를 유효한 안내로 제공한 경우

### 4.3 대응 정책 (합의안)
- 즉시 안내 중단 + 정정 공지
- 해당 카드/문서 노출 비활성화
- 운영 공지와 변경 이력 기록
- 재검수 완료 전 재게시 금지

### 4.4 품질 게이트 방식
- 자동 검증 + 고위험 항목 수동 검수
- 자동 검증:
- 만료일/시행일/공고 종료일 기본 체크
- 필수 메타 필드 누락 체크
- 고위험 수동 검수:
- 법률/공고 원문 변경 감지 시
- 사용자 신고 누적 임계치 초과 시

## 5. 정보구조(IA) 및 화면 요구사항

### 5.1 사용자 영역
- 내 프로필
- 대시보드
- 액션키트 목록/상세(4개 카테고리)
- 커뮤니티(지역/업종 피드)

### 5.2 운영자 영역
- 운영 대시보드(요약 지표)
- 사용자 관리
- 신고/모더레이션
- 공지 관리
- 액션키트 품질 상태(검수 대기/게시중/중단)

## 6. 데이터 모델 제안 (MVP)

### 6.1 프로필/사용자
- `profiles`:
- `user_id`, `region_id`, `industry_id`, `startup_stage`, `completion_score`, `updated_at`
- `users`:
- `status`(`active`/`suspended`)

### 6.2 액션키트
- `action_kits`:
- `id`, `category(law/tax/notice/hr)`, `title`, `summary`, `source_url`, `effective_from`, `effective_to`, `status(draft/published/paused)`
- `action_kit_targets`:
- `action_kit_id`, `region_id(nullable)`, `industry_id(nullable)`, `roadmap_step_id(nullable)`
- `action_kit_reports`:
- `id`, `action_kit_id`, `reported_by`, `reason`, `status(open/reviewed/resolved)`, `created_at`

### 6.3 커뮤니티
- `posts`:
- `id`, `author_id`, `region_id`, `industry_id`, `topic_tag`, `content`, `status(visible/hidden)`
- `comments`:
- `id`, `post_id`, `author_id`, `content`, `status(visible/hidden)`
- `reports`:
- `id`, `target_type(post/comment)`, `target_id`, `reason`, `reporter_id`, `status(open/reviewed/actioned)`

### 6.4 운영
- `announcements`:
- `id`, `title`, `body`, `status(draft/published)`, `published_at`
- `admin_audit_logs`:
- `id`, `admin_id`, `action`, `target_type`, `target_id`, `meta`, `created_at`

## 7. API 범위 (MVP)

### 7.1 프로필
- `GET /api/v2/profile/me`
- `PATCH /api/v2/profile/me`

### 7.2 액션키트
- `GET /api/v2/action-kits?category=&region=&industry=&stage=`
- `GET /api/v2/action-kits/{id}`
- `POST /api/v2/action-kits/{id}/scrap`
- `POST /api/v2/action-kits/{id}/report`

### 7.3 커뮤니티
- `GET /api/v2/community/posts?region=&industry=&tab=`
- `POST /api/v2/community/posts`
- `POST /api/v2/community/posts/{id}/comments`
- `POST /api/v2/community/posts/{id}/like`
- `POST /api/v2/community/reports`

### 7.4 운영(Admin)
- `GET /api/v2/admin/users`
- `PATCH /api/v2/admin/users/{id}/status`
- `GET /api/v2/admin/reports`
- `PATCH /api/v2/admin/reports/{id}` (처리 상태 변경)
- `POST /api/v2/admin/announcements`
- `PATCH /api/v2/admin/announcements/{id}`
- `POST /api/v2/admin/action-kits/{id}/pause`

## 8. 주차별 상세 계획

### Week 1: 기반 및 모델 정비
- 프로필/액션키트/커뮤니티/운영 최소 테이블 확정
- 마이그레이션 작성 및 검증 루프 구축
- Admin 권한 체크 미들웨어 최소 구현
- 산출물:
- 스키마 + 기본 CRUD API 골격 + 테스트 스캐폴딩

### Week 2: 프로필 + 액션키트 상세
- 프로필 조회/수정 UI/API 완료
- 액션키트 4개 카테고리 목록/상세 + 스크랩 + 오류 신고
- 품질 게이트 1차(자동 검증 필드 체크)
- 산출물:
- 사용자 경로에서 "실제 데이터 기반" 액션키트 조회 가능

### Week 3: 커뮤니티 + 운영 처리
- 지역/업종 피드, 글/댓글/좋아요/신고
- 운영자 신고 처리(숨김/복구)
- 공지 노출 연결
- 산출물:
- 신고 -> 운영자 처리 -> 사용자 노출 제어 루프 완성

### Week 4: 운영 콘솔 + 안정화
- 사용자 상태 관리/공지 관리 화면
- 액션키트 중단/재게시 운영 기능
- 로그/알림/핵심 지표 최소 대시보드
- 회귀 테스트 및 운영 체크리스트 정리
- 산출물:
- 운영자가 서비스 상태를 통제 가능한 최소 콘솔 확보

## 9. 완료 기준 (Definition of Done)
- 프로필 관리:
- 본인 프로필 조회/수정이 정상 동작
- 액션키트:
- 4개 카테고리 상세 페이지가 실제 데이터로 렌더링
- 출처/업데이트 일시/오류 신고 동작
- 커뮤니티:
- 글/댓글/좋아요/신고 동작
- 운영자 숨김 처리 즉시 반영
- 운영:
- 사용자 상태 변경 + 공지 게시 가능
- 감사 로그가 주요 운영 액션 기록
- 리스크 대응:
- 치명 오류 발생 시 해당 콘텐츠 즉시 중단 + 정정 공지 가능

## 10. 핵심 KPI (4주 MVP용)
- 프로필 완성률
- 액션키트 상세 조회수/스크랩률
- 신고 접수 후 처리 리드타임
- 잘못된 안내 신고 재발률
- 커뮤니티 주간 활성 사용자(WAU) 및 게시글 대비 댓글 비율

## 11. 결정 필요 사항 (다음 회의 안건)
- 운영자 권한 세분화 수준(1단계 단일 Admin vs 다중 역할)
- 액션키트 검수 기준의 임계치(자동 중단 조건)
- 공지 노출 규칙(전역/지역/업종 타겟팅 여부)
- 커뮤니티 신고 사유 표준셋 확정
