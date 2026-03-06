# PLAN: 대시보드 보완 + 알림 SSE 전환

Last Updated: 2026-03-06

## 1. Executive Summary

대시보드에 하드코딩된 거짓 데이터를 실제 데이터로 교체하고, 알림 시스템을 60초 폴링에서 SSE(Server-Sent Events) 실시간 푸시로 전환한다.
기존 Chat 기능에 구축된 SSE 인프라(FastAPI StreamingResponse + parseSSELine)를 최대한 재활용하여 구현 비용을 최소화한다.

## 2. Current State

### 하드코딩/모의 데이터 (거짓 정보)
- "프로 플랜 사용 중": 모든 사용자에게 동일 표시 (Sidebar, AccountMenu)
- ColdStartHero 소셜 프루프: "1,200+", "850+", "4.9/5" 정적 텍스트
- GrowthClub founders_online: 게스트=1250, 로그인=12 하드코딩
- GrowthClubCard 아바타: seed=A, seed=B 하드코딩
- Sidebar 아바타: dicebear만 사용 (UserProfile.profile_img 미연동)
- days_left: 30일 하드코딩 (goal_horizon_days DB 미저장)

### 알림 시스템 현재 상태
- FE: NotificationBell에서 60초 setInterval 폴링 (apiClient.get /notifications)
- BE: notifications.py — GET/POST/DELETE CRUD (동기 요청-응답만)
- 알림 생성: growth_club comments/posts, ops announcements에서 Notification INSERT
- 생성 후 클라이언트 통지 메커니즘 없음 (다음 폴링까지 최대 60초 지연)

### 참조할 기존 SSE 인프라
- BE: `chat/router.py` — `StreamingResponse(media_type="text/event-stream")`
- FE: `chat/utils/sse.ts` — `getApiBaseUrl()`, `getAuthHeaders()`, `parseSSELine()`, `tryRefreshToken()`
- FE: `chat/hooks/useChat.ts` — native fetch + ReadableStream 파싱 패턴

## 3. Proposed Future State

### Phase 1: 거짓 정보 제거/교정
- "프로 플랜" → 제거 또는 "무료" 표시
- ColdStartHero 소셜 프루프 → "Beta" 라벨로 교체
- GrowthClubCard → 하드코딩 아바타 제거, 익명 아이콘 사용
- Sidebar 아바타 → UserProfile.profile_img 연동 (있으면 실제 이미지, 없으면 dicebear 폴백)

### Phase 2: 데이터 연동 보강
- founders_online → 실제 최근 활동 사용자 집계 (DB 쿼리)
- Dashboard API 응답에 roadmap_id 포함
- useDashboard error 상태 UI 표시

### Phase 3: 알림 SSE 전환
- BE: `/api/v1/notifications/stream` SSE 엔드포인트 신규
- BE: 알림 생성 시 Redis Pub/Sub으로 이벤트 발행
- FE: useNotificationSSE 훅 — EventSource 또는 native fetch로 SSE 구독
- FE: NotificationBell에서 폴링 제거, SSE 훅으로 교체

### Phase 4: 접근성 + 테스트 보강
- 대시보드 전체 a11y 개선 (aria-label, sr-only, 키보드 네비게이션)
- MobileNav safe-area 적용
- 백엔드 대시보드 테스트 6개 시나리오 추가

## 4. Implementation Phases

### Phase 1: 거짓 정보 제거 [Effort: S, Risk: Low]

하드코딩된 가짜 데이터를 정직한 표시로 교체한다.
모든 변경은 프론트엔드 전용이며 API 변경 없음.

### Phase 2: 데이터 연동 보강 [Effort: M, Risk: Low]

백엔드 API 확장 + 프론트엔드 연동.
founders_online 실제 집계, roadmap_id 응답 포함, 에러 UI.

### Phase 3: 알림 SSE 전환 [Effort: L, Risk: Medium]

가장 큰 작업. 기존 Chat SSE 패턴을 재활용하되, 알림은 long-lived connection이므로 재연결/heartbeat 로직이 필요하다.

**아키텍처:**
```
[알림 생성] → Notification INSERT → Redis PUBLISH "notifications:{user_id}"
                                          ↓
[SSE 엔드포인트] ← Redis SUBSCRIBE → StreamingResponse → FE EventSource
```

- Redis Pub/Sub 선택 이유: 이미 app-redis 서비스 운영 중, ARQ 워커와 동일 인프라
- 폴링 완전 제거는 아님: SSE 연결 실패 시 폴링 폴백 유지 (graceful degradation)

### Phase 4: 접근성 + 테스트 [Effort: M, Risk: Low]

WCAG 2.1 AA 수준 접근성 개선 + 백엔드 테스트 커버리지 확대.

## 5. Risk Assessment

| 리스크 | 심각도 | 완화 |
|--------|--------|------|
| SSE 연결 끊김 (네트워크 불안정) | 중간 | 자동 재연결 + 폴링 폴백 |
| Redis Pub/Sub 메시지 유실 (구독 전 발행) | 낮음 | SSE 연결 시 최신 알림 초기 로드 |
| founders_online 쿼리 성능 | 낮음 | 캐싱 (30초 TTL) 또는 대시보드 호출 시에만 집계 |
| 프로필 이미지 경로 불일치 | 낮음 | STORAGE_LOCAL_ROOT 기반 URL 생성 확인 |
| 소셜 프루프 제거 시 ColdStartHero 심미성 저하 | 낮음 | "Beta" 라벨 + 참여 유도 문구로 대체 |

## 6. Success Metrics

- [ ] Grep "프로 플랜" in dashboard/ = 0건 (하드코딩 제거)
- [ ] ColdStartHero에 하드코딩된 수치(1200, 850, 4.9) = 0건
- [ ] founders_online이 DB 쿼리 결과 반환 (하드코딩 아님)
- [ ] Dashboard API 응답에 roadmap_id 포함
- [ ] 알림 SSE 엔드포인트 정상 작동 (연결 후 5초 이내 heartbeat 수신)
- [ ] 알림 생성 → FE 수신 지연 < 2초
- [ ] SSE 연결 실패 시 폴링 폴백 정상 작동
- [ ] pnpm lint + pnpm test 통과
- [ ] cd app-backend && make test 통과
- [ ] 대시보드 인터랙티브 요소 100% aria-label 보유
