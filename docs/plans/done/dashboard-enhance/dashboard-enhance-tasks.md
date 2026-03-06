# Tasks: 대시보드 보완 + 알림 SSE 전환

Last Updated: 2026-03-06

## Phase 1: 거짓 정보 제거 [Effort: S] -- DONE

- [x] 1.1 "프로 플랜" 하드코딩 제거
- [x] 1.2 ColdStartHero 소셜 프루프 교체 (기능 설명 문구로)
- [x] 1.3 GrowthClubCard 하드코딩 아바타 제거
- [x] 1.4 Sidebar 아바타 → 실제 프로필 이미지 연동
- [x] 1.5 빌드/린트 검증

---

## Phase 2: 데이터 연동 보강 [Effort: M] -- DONE

- [x] 2.1 founders_online 실제 집계 (7일 내 고유 author_id COUNT)
- [x] 2.2 Dashboard API에 roadmap_id 포함
- [x] 2.3 useDashboard error 상태 UI 표시
- [x] 2.4 빌드/린트/테스트 검증

---

## Phase 3: 알림 SSE 전환 [Effort: L] -- DONE

### 3-A: 백엔드 SSE 인프라
- [x] 3.1 Redis Pub/Sub 알림 발행 유틸 생성 (`notification_pubsub.py`)
- [x] 3.2 알림 생성 코드에 Redis 발행 연동
- [x] 3.3 SSE 스트림 엔드포인트 구현 (`GET /notifications/stream`)
- [x] 3.4 백엔드 테스트

### 3-B: 프론트엔드 SSE 연동
- [x] 3.5 useNotificationSSE 훅 생성
- [x] 3.6 NotificationBell에 SSE 훅 적용
- [x] 3.7 프론트엔드 테스트/빌드 검증

---

## Phase 4: 접근성 + 테스트 보강 [Effort: M] -- DONE

### 4-A: 접근성
- [x] 4.1 aria-label 추가
- [x] 4.2 sr-only 텍스트 추가
- [x] 4.3 RoadmapStepper 키보드 접근성
- [x] 4.4 MobileNav safe-area

### 4-B: 백엔드 테스트 보강
- [x] 4.5 게스트 대시보드 테스트
- [x] 4.6 로드맵 없음 (READY) 테스트
- [x] 4.7 progress 계산 테스트
- [x] 4.8 days_left 경계값 테스트
- [x] 4.9 invalid roadmap_id 테스트
- [x] 4.10 전체 검증

---

## Completion
- **PR**: #24 (merged to develop)
- **Commit**: 676f88f (feat: dashboard-enhance 전체 구현 Phase 1~4)
- **All phases complete**: 2026-03-06
