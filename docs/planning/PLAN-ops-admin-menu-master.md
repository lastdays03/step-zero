# PLAN: Ops Admin Menu Master

## Status
- In Progress

## 목적
- `/ops` 운영관리 전체 메뉴 구조를 확정하고, 화면별 구현 우선순위와 연계 플랜을 통합 관리한다.
- 운영자(MVP) 기준에서 누락 없는 최소 운영 콘솔을 정의한다.

## 운영관리 메뉴 구조 (MVP)
1. `/ops` 운영 홈(메뉴 허브)
2. `/ops/reports` 운영 리포트(요약 지표)
3. `/ops/users` 사용자 관리
4. `/ops/growth-club` 커뮤니티 모더레이션
5. `/ops/actionkit` 액션키트 운영
6. `/ops/announcements` 공지 관리
7. `/ops/audit-logs` 운영 감사로그

## 화면 역할 요약
1. Reports
- 운영 지표 요약 조회 및 운영 의사결정 보조
2. Users
- 사용자 상태/권한 관리(활성/정지, 운영자 권한 확인)
3. Growth Club
- 신고 큐 처리, 블라인드/해제/삭제 등 커뮤니티 조치
4. ActionKit
- 아이템/파일 버전 운영, 품질 상태 관리
5. Announcements
- 공지 작성/수정/게시/내림
6. Audit Logs
- 운영 조치 추적(누가/언제/무엇/왜)

## 공통 운영 원칙
1. 접근 제어
- 모든 `/ops/*` API/화면은 플랫폼 운영자(`is_superuser`)만 접근
- 실행 기준 네임스페이스는 `/api/v1/ops`로 통일한다. (`/api/v2/admin` 표기는 레거시 계획 참조용)
2. 감사 가능성
- 운영 상태를 바꾸는 액션은 감사로그 적재를 기본값으로 설계
3. UX 기본
- 모든 화면에 loading/error/empty 상태를 명시
4. API 응답 규격
- 목록: 필터/페이지네이션 구조 일관화
- 조치: 결과 + 최신 상태 + 감사로그 참조 ID 반환 권장

## 상세 플랜 연결
- `PLAN-ops-reports-dashboard.md`
- `PLAN-ops-users-admin-ui.md`
- `PLAN-ops-growth-club-moderation.md`
- `PLAN-ops-actionkit-admin-ui.md`
- `PLAN-ops-announcements-admin-ui.md`
- `PLAN-ops-audit-logs.md`

## 우선순위/구현 순서
1. 간접 기반: Ops 레이아웃/네비게이션 정리(메뉴 진입 구조, 공통 페이지 프레임)
2. 상세 플랜 공통 선행: `/ops` 권한 가드 일관화, 공통 API 클라이언트, 감사로그 기록 인프라(테이블/유틸)
3. 고리스크 조치: Growth Club, ActionKit (구현 시 감사로그 즉시 연동)
4. 운영 커뮤니케이션: Announcements (구현 시 감사로그 즉시 연동)
5. 추적 체계 조회면: Audit Logs 화면/필터
6. 보조 지표 고도화: Reports
7. 사용자 운영 고도화: Users

## 완료 기준 (DoD)
1. `/ops` 홈에서 6개 상세 메뉴 진입 가능
2. 각 상세 플랜이 API/UI/검증 항목을 포함하고 상태 관리 가능
3. 운영 상태 변경 액션에 대한 감사로그 정책이 문서로 확정

## 진행 체크
- [x] 간접 기반(Ops 홈 진입화면 정리): `announcements`, `audit-logs` 카드/라우트 반영
