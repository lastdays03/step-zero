# Context: 대시보드 보완 + 알림 SSE 전환

Last Updated: 2026-03-06

## Key Files

### Phase 1: 거짓 정보 제거 (FE only)

| 파일 | 변경 내용 |
|------|----------|
| `app-frontend/src/features/dashboard/components/Sidebar.tsx` | "프로 플랜" 제거, profile_img 연동 |
| `app-frontend/src/features/dashboard/components/AccountMenu.tsx` | "프로 플랜 사용 중" 제거 |
| `app-frontend/src/features/dashboard/components/ColdStartHero.tsx` | 소셜 프루프 수치 → "Beta" 라벨 |
| `app-frontend/src/features/dashboard/components/GrowthClubCard.tsx` | seed=A/B 아바타 → 익명 아이콘 |

### Phase 2: 데이터 연동 보강

| 파일 | 변경 내용 |
|------|----------|
| `app-backend/app/features/dashboard/application/dashboard_service.py` | founders_online 실제 집계, roadmap_id 반환 |
| `app-backend/app/api/v1/schemas.py` | DashboardResponse에 roadmap_id 필드 추가 |
| `app-frontend/src/features/dashboard/components/DashboardView.tsx` | error 상태 배너 표시 |

### Phase 3: 알림 SSE 전환

| 파일 | 역할 | 변경 |
|------|------|------|
| `app-backend/app/api/v1/notifications.py` | 알림 CRUD 라우터 | SSE stream 엔드포인트 추가 |
| `app-backend/app/api/v1/chat/router.py` | SSE 참조 패턴 | 변경 없음 (참조만) |
| `app-frontend/src/features/chat/utils/sse.ts` | SSE 유틸 (재사용) | 변경 없음 |
| `app-frontend/src/features/notifications/hooks/useNotificationSSE.ts` | **신규** SSE 훅 |
| `app-frontend/src/features/notifications/components/NotificationBell.tsx` | 폴링 → SSE 교체 |

### Phase 3: 알림 생성 → Redis 발행 (발신측)

| 파일 | 현재 알림 생성 위치 |
|------|-------------------|
| `app-backend/app/api/v1/growth_club/comments.py:63,78` | 댓글/답글 알림 |
| `app-backend/app/api/v1/growth_club/posts.py:453` | 좋아요 알림 |
| `app-backend/app/api/v1/ops/growth_club.py:284` | 운영자 알림 |
| `app-backend/app/features/ops/application/announcements/service.py:150` | 공지사항 알림 |

### Phase 4: 접근성 + 테스트

| 파일 | 변경 내용 |
|------|----------|
| `app-frontend/src/features/dashboard/components/*.tsx` | aria-label, sr-only 추가 |
| `app-frontend/src/features/dashboard/components/MobileNav.tsx` | safe-area-inset-bottom |
| `app-frontend/src/features/dashboard/components/RoadmapStepper.tsx` | 키보드 스크롤 |
| `app-backend/tests/api/test_dashboard.py` | 6개 테스트 시나리오 추가 |

## Key Decisions

1. **SSE vs WebSocket**: SSE 선택 — 서버→클라이언트 단방향이면 충분, 기존 Chat SSE 인프라 재활용 가능, HTTP/2 자동 멀티플렉싱
2. **Redis Pub/Sub vs DB 폴링**: Redis Pub/Sub — 이미 app-redis 운영 중, 지연 시간 최소화 (~ms), 메모리 사용량 미미
3. **폴링 완전 제거 여부**: 유지 (폴백) — SSE 연결 실패 시 60초 폴링으로 graceful degradation
4. **profile_img URL 형식**: `/api/v1/profile/me/image` 엔드포인트 사용 (로컬 파일 직접 경로 노출 방지)
5. **founders_online 집계 방식**: growth_club_post 테이블에서 최근 7일 내 고유 author_id COUNT (실시간 온라인이 아닌 "활성 창업자" 개념으로 재정의)
6. **"프로 플랜" 대체**: 구독 시스템 미구현이므로 플랜 표시 자체를 제거. 향후 billing 구현 시 복원
7. **ColdStartHero 소셜 프루프 대체**: 구체적 수치 대신 "AI 기반 로드맵 설계" 등 기능 설명 문구로 교체

## Dependencies

- `app-redis` 서비스: Pub/Sub 채널 사용 (기존 ARQ 워커와 공존)
- `aioredis` / `redis.asyncio`: 백엔드 Redis async 클라이언트 (이미 설치됨 — ARQ용)
- `chat/utils/sse.ts`: parseSSELine, getAuthHeaders, tryRefreshToken 재사용
- `@/providers/AuthProvider`: useAuth 훅 — user 객체에서 profile_img 접근 필요

## Redis Pub/Sub 채널 설계

```
채널: notifications:{user_id}
메시지: JSON { "type": "new_notification", "data": { ...NotificationRead } }
```

- 알림 INSERT 직후 `PUBLISH notifications:{user_id} <json>` 호출
- SSE 엔드포인트에서 `SUBSCRIBE notifications:{user_id}` 구독
- 연결 종료 시 자동 UNSUBSCRIBE
