# Tasks: 대시보드 보완 + 알림 SSE 전환

Last Updated: 2026-03-06

## Phase 1: 거짓 정보 제거 [Effort: S]

- [ ] 1.1 "프로 플랜" 하드코딩 제거
  - `Sidebar.tsx`: "프로 플랜" 텍스트 → 제거 (사용자명 아래 부제 삭제)
  - `AccountMenu.tsx`: "프로 플랜 사용 중" → "계정 설정" 또는 제거
  - AC: Grep "프로 플랜" in dashboard/ = 0건

- [ ] 1.2 ColdStartHero 소셜 프루프 교체
  - "1,200+", "850+", "4.9/5" 하드코딩 수치 영역 제거
  - 대신 기능 설명 문구 3개로 교체: "AI 맞춤 로드맵", "법률/행정 가이드", "창업자 커뮤니티"
  - AC: Grep "1,200\|850\|4\.9" in ColdStartHero = 0건

- [ ] 1.3 GrowthClubCard 하드코딩 아바타 제거
  - `seed=A`, `seed=B` dicebear URL → lucide `Users` 아이콘 그룹으로 교체
  - AC: Grep "seed=A\|seed=B" in GrowthClubCard = 0건

- [ ] 1.4 Sidebar 아바타 → 실제 프로필 이미지 연동
  - useAuth의 user 객체에 profile_img 포함 여부 확인
  - 있으면: `/api/v1/profile/me/image` URL 사용
  - 없으면: 기존 dicebear 폴백 유지
  - AC: 프로필 이미지 업로드 후 Sidebar 아바타 갱신 확인

- [ ] 1.5 빌드/린트 검증
  - `pnpm lint` 통과
  - `pnpm build` 통과
  - AC: 에러 0건

---

## Phase 2: 데이터 연동 보강 [Effort: M]

- [ ] 2.1 founders_online 실제 집계
  - BE: `dashboard_service.py` — 하드코딩 12/1250 대신 DB 쿼리
  - 쿼리: growth_club_post 테이블에서 최근 7일 내 고유 author_id COUNT
  - 게스트: 동일 쿼리 사용 (게스트도 실제 수치 표시)
  - `roadmap_repository.py` 또는 별도 쿼리 추가
  - AC: founders_online 값이 실제 데이터 기반 (하드코딩 아님)
  - Deps: 없음

- [ ] 2.2 Dashboard API에 roadmap_id 포함
  - BE: `DashboardResult`에 `roadmap_id: str | None` 필드 추가
  - BE: `DashboardResponse` (schemas.py)에 `roadmap_id: str | None = None` 추가
  - BE: `dashboard_service.py` — latest_roadmap.id를 str로 변환하여 포함
  - FE: 변경 불필요 (기존에 activeRoadmapId로 관리)
  - AC: GET /dashboard 응답에 roadmap_id 필드 포함
  - Deps: 없음

- [ ] 2.3 useDashboard error 상태 UI 표시
  - FE: `DashboardView.tsx` — `useDashboard` 반환 error가 truthy일 때 상단 경고 배너 표시
  - 배너: "데이터를 불러오는 중 오류가 발생했습니다. 새로고침해 주세요." + 재시도 버튼
  - AC: 네트워크 에러 시 사용자에게 에러 상태 표시
  - Deps: 없음

- [ ] 2.4 빌드/린트/테스트 검증
  - `pnpm lint` + `pnpm test` 통과
  - `cd app-backend && make test` 통과
  - AC: 에러 0건

---

## Phase 3: 알림 SSE 전환 [Effort: L]

### 3-A: 백엔드 SSE 인프라

- [ ] 3.1 Redis Pub/Sub 알림 발행 유틸 생성
  - 신규: `app-backend/app/services/notification_publisher.py`
  - 함수: `async def publish_notification(user_id: int, notification: Notification)`
  - Redis PUBLISH `notifications:{user_id}` 채널에 JSON 발행
  - Redis 연결: 기존 `app.core.redis` 또는 `settings.REDIS_URL` 사용
  - AC: 알림 INSERT 후 Redis 메시지 발행 확인
  - Deps: 없음

- [ ] 3.2 알림 생성 코드에 Redis 발행 연동
  - `growth_club/comments.py:63,78` — 댓글/답글 알림 INSERT 후 publish_notification 호출
  - `growth_club/posts.py:453` — 좋아요 알림 INSERT 후 publish_notification 호출
  - `ops/growth_club.py:284` — 운영자 알림 INSERT 후 publish_notification 호출
  - `announcements/service.py:150` — 공지 알림 INSERT 후 publish_notification 호출
  - AC: 모든 알림 생성 지점에서 Redis 발행 확인 (Grep "publish_notification")
  - Deps: 3.1

- [ ] 3.3 SSE 스트림 엔드포인트 구현
  - `notifications.py`에 `GET /notifications/stream` 추가
  - 인증: `get_current_user` (게스트 접근 불가)
  - 로직:
    1. 초기 로드: 최신 알림 목록 전송 (`init` 이벤트)
    2. Redis SUBSCRIBE `notifications:{user_id}`
    3. 새 알림 수신 시 SSE 이벤트 전송 (`new` 이벤트)
    4. 30초마다 heartbeat (`: heartbeat\n\n`)
  - StreamingResponse(media_type="text/event-stream") 사용
  - 연결 종료 시 Redis UNSUBSCRIBE
  - AC: curl로 SSE 연결 후 heartbeat 수신, 알림 생성 시 즉시 이벤트 수신
  - Deps: 3.1

- [ ] 3.4 백엔드 테스트
  - SSE 연결 테스트 (응답 media_type 확인)
  - publish_notification 단위 테스트
  - AC: make test 통과
  - Deps: 3.3

### 3-B: 프론트엔드 SSE 연동

- [ ] 3.5 useNotificationSSE 훅 생성
  - 신규: `app-frontend/src/features/notifications/hooks/useNotificationSSE.ts`
  - native fetch + ReadableStream (chat/useChat.ts 패턴 재사용)
  - URL: `${getApiBaseUrl()}/notifications/stream`
  - 헤더: `getAuthHeaders()` 재사용
  - 이벤트 파싱: `parseSSELine()` 재사용
  - 자동 재연결: 연결 끊김 시 5초 후 재시도 (최대 3회, 이후 폴링 폴백)
  - 토큰 만료: `tryRefreshToken()` 후 재연결
  - 반환: `{ notifications, hasUnread, isConnected, markRead, markAllRead, deleteNotification }`
  - AC: SSE 연결 성공 시 isConnected=true, 알림 수신 시 notifications 업데이트
  - Deps: 3.3

- [ ] 3.6 NotificationBell에 SSE 훅 적용
  - 기존 60초 setInterval 폴링 로직 제거
  - useNotificationSSE 훅으로 교체
  - SSE 미연결 시 기존 폴링으로 폴백 (isConnected 기반)
  - AC: 알림 생성 → NotificationBell 즉시 반영 (< 2초)
  - Deps: 3.5

- [ ] 3.7 프론트엔드 테스트/빌드 검증
  - `pnpm lint` 통과
  - `pnpm test` 통과
  - `pnpm build` 통과
  - AC: 에러 0건
  - Deps: 3.6

---

## Phase 4: 접근성 + 테스트 보강 [Effort: M]

### 4-A: 접근성

- [ ] 4.1 aria-label 추가
  - NotificationBell 버튼: `aria-label="알림"`
  - MobileNav 각 항목: `aria-label={item.label}`
  - Sidebar 로그인 버튼: `aria-label="로그인"`
  - RoadmapStepper "전체 계획 보기": `aria-label="전체 로드맵 보기"`
  - AccountMenu trigger: `aria-label="계정 메뉴"`
  - AC: 모든 인터랙티브 요소에 aria-label 존재

- [ ] 4.2 sr-only 텍스트 추가
  - NotificationBell 아이콘: `<span className="sr-only">알림</span>`
  - 삭제 버튼 (X 아이콘): `<span className="sr-only">삭제</span>`
  - AC: 아이콘 전용 버튼에 스크린리더 대안 텍스트 존재

- [ ] 4.3 RoadmapStepper 키보드 접근성
  - tabIndex="0" + onKeyDown (ArrowLeft/ArrowRight) 스크롤
  - role="tablist" + role="tab" 적용
  - AC: 키보드 좌우 화살표로 스크롤 가능

- [ ] 4.4 MobileNav safe-area
  - `pb-8` → `pb-[max(2rem,env(safe-area-inset-bottom))]` 또는 Tailwind plugin 사용
  - viewport meta에 `viewport-fit=cover` 확인
  - AC: iPhone 홈 인디케이터 영역에서 네비게이션 가림 없음

### 4-B: 백엔드 테스트 보강

- [ ] 4.5 게스트 대시보드 테스트
  - 헤더 없이 GET /dashboard → status=GUEST 확인
  - AC: 테스트 통과

- [ ] 4.6 로드맵 없음 (READY) 테스트
  - 로드맵 없는 사용자 → status=READY, roadmap=[] 확인
  - AC: 테스트 통과

- [ ] 4.7 progress 계산 테스트
  - 3 step: 1 COMPLETED → progress=33 확인
  - AC: 테스트 통과

- [ ] 4.8 days_left 경계값 테스트
  - 생성 후 30일 초과 → days_left=0 확인
  - AC: 테스트 통과

- [ ] 4.9 invalid roadmap_id 테스트
  - `?roadmap_id=not-a-uuid` → 에러 없이 최신 로드맵 사용
  - AC: 테스트 통과

- [ ] 4.10 전체 검증
  - `pnpm lint` + `pnpm test` + `make test` 통과
  - AC: 에러 0건
