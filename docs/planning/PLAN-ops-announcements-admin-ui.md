# PLAN: Ops Announcements Admin UI

## Status
- Draft

## 목적
- 운영자가 공지를 작성/수정/게시/내림할 수 있는 `/ops/announcements` 화면을 구현한다.

## 범위
1. Ops 메인 카드/진입 링크 추가
2. 공지 목록(초안/게시/내림)
3. 공지 작성/수정 에디터
4. 게시/내림 상태 전환
5. 게시 이력 및 조치 사유 기록

## 비범위 (이번 단계)
- 다국어 공지
- 정교한 타겟팅(지역/업종/세그먼트)

## IA/화면 구성
1. 목록 탭
- 상태별 탭(draft/published/archived), 검색
2. 작성/수정 화면
- 제목, 본문, 상태, 게시 시각
3. 상태 전환 모달
- 게시/내림 시 확인 + 사유(reason)

## API 작업
1. `GET /api/v1/ops/announcements`
2. `POST /api/v1/ops/announcements`
3. `PATCH /api/v1/ops/announcements/{id}`
4. `POST /api/v1/ops/announcements/{id}/publish`
5. `POST /api/v1/ops/announcements/{id}/unpublish`

## API 네임스페이스 기준
- 운영 API는 `/api/v1/ops/*` 기준으로 구현한다.

## 감사로그 정책
- `ANNOUNCEMENT_CREATED`
- `ANNOUNCEMENT_UPDATED`
- `ANNOUNCEMENT_PUBLISHED`
- `ANNOUNCEMENT_UNPUBLISHED`

## 구현 단계
1. Ops 홈 카드/라우트 추가
2. 감사로그 기록 인프라(테이블/유틸) 선반영 여부 확인
3. 공지 도메인 모델/마이그레이션
4. CRUD + 상태 전환 API
5. 프론트 목록/에디터/모달
6. 사용자 노출면 연동(게시 공지만 노출)

## 구현 게이트
- 공지 생성/수정/게시/내림 API는 감사로그 연동 없이 배포하지 않는다.

## 완료 기준 (DoD)
1. 운영자가 공지를 작성/수정/게시/내림할 수 있다.
2. 상태 변경 액션이 감사로그에 기록된다.
