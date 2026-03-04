# PLAN: Ops Users Admin UI

## Status
- Draft

## 목적
- 운영자가 사용자 계정 상태와 운영 권한을 관리할 수 있는 `/ops/users` 화면을 구현한다.

## 범위
1. 사용자 목록 조회(최신 가입순)
2. 사용자 상태 변경(active/suspended)
3. 운영자 권한 상태 확인(읽기 전용)
4. 조치 사유 입력 및 감사로그 기록

## 비범위 (이번 단계)
- 역할 기반 세분 권한(RBAC) 전체 도입
- 운영자 권한 변경(role promotion/demotion)
- 대량 일괄 작업(batch)

## IA/화면 구성
1. 목록 영역
- 검색(이메일/이름), 상태 필터(active/suspended), 권한 필터(superuser/user)
2. 상세 패널
- 기본 정보(가입일, 계정 상태), 현재 상태, 조치 이력 요약
3. 조치 모달
- 상태 변경, 사유(reason) 입력, 확인

## API 네임스페이스 기준
- 운영 API는 `/api/v1/ops/*` 기준으로 구현한다.

## API 작업
### 현재
- `GET /api/v1/ops/users` (구현됨)

### 추가 필요
1. `PATCH /api/v1/ops/users/{user_id}/status`
2. `PATCH /api/v1/ops/users/{user_id}/role` (Phase 2 / On Hold)

## 감사로그 정책
- `USER_STATUS_UPDATED`
- `USER_ROLE_UPDATED` (Phase 2 / On Hold)

## 구현 단계
1. 목록 API 응답 확장(필터/페이지네이션)
2. 감사로그 기록 인프라(테이블/유틸) 선반영 여부 확인
3. 상태 변경 API + 감사로그 연동
4. 프론트 조치 모달 및 optimistic refresh
5. 권한/예외 UX 정리

## 구현 게이트
- 감사로그 기록 인프라가 준비되기 전에는 상태 변경 API를 오픈하지 않는다.

## 완료 기준 (DoD)
1. 운영자가 사용자 상태를 변경할 수 있다.
2. 조치 사유와 함께 감사로그가 남는다.
3. 로딩/오류/빈 상태가 명확하다.
