# Ops Audit Logs Guide

## 목적
- 운영자 조치 이력을 조회/추적하기 위한 기준 문서

## 조회 화면
- 경로: `/ops/audit-logs`
- 필터: 운영자 ID(`actor`), 액션 코드(`action`), 대상 타입(`target_type`), 기간(`from`, `to`), 페이지/사이즈
- 목록 컬럼: 시각, 운영자, 액션, 대상, 사유
- 상세: `meta.before` / `meta.after` 중심 JSON 확인

## API
- `GET /api/v1/ops/audit-logs`
- Query
  - `actor`: 운영자 ID
  - `action`: 액션 코드
  - `target_type`: 대상 타입
  - `from`, `to`: ISO8601 시각
  - timezone 없는 시각은 UTC로 처리
  - `page`, `size`: 페이지네이션
- Response
  - `items[]`, `total`, `page`, `size`

## 액션 코드
- `user.status.updated`
- `announcement.created`
- `announcement.updated`
- `announcement.drafted`
- `announcement.published`
- `announcement.archived`
- `growth_club.post.blinded`
- `growth_club.post.unblinded`
- `growth_club.post.deleted`
- `actionkit.item.status.updated`

## 대상 타입
- `user`
- `announcement`
- `growth_club_post`
- `actionkit_item`

## meta 마스킹
- 민감 키 포함 시 값은 `[REDACTED]`로 저장
- 예: `password`, `token`, `secret`, `api_key`, `authorization`, `cookie`, `client_secret`

## 보존 정책
- 기본 180일 보관
- 이후 아카이브 또는 삭제 배치로 정리 (정책 확정 후 스케줄러 반영)

## 운영 체크리스트
1. 상태 변경형 운영 API는 감사로그 연동 없이 배포하지 않는다.
2. 동일 상태 재요청(no-op)은 로그를 추가 생성하지 않는다.
3. 비즈니스 액션 실패 시 감사로그도 함께 롤백되어야 한다.
