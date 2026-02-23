# PLAN: Ops Audit Logs

## Status
- In Progress (Phase 1~5 구현 완료, 테스트/운영 정책 잔여)

## 목적
- 운영자 조치의 책임 추적을 위해 `/ops/audit-logs` 조회 화면과 기록 체계를 구축한다.

## 범위
1. Ops 메인 카드/진입 링크 추가
2. 감사로그 저장 모델 정의(`admin_audit_logs`)
3. 운영 액션 기록 유틸/미들웨어
4. 감사로그 조회 API
5. `/ops/audit-logs` 목록/필터 화면

## 진행 체크
- [x] Ops 메인 카드 및 `/ops/audit-logs` 진입 라우트 반영
- [x] 감사로그 저장 모델/마이그레이션 추가 (`admin_audit_logs`)
- [x] `record_admin_audit_log(...)` 공통 유틸 구현
- [x] `GET /api/v1/ops/audit-logs` 필터/페이지네이션 조회 API 구현
- [x] 핵심 운영 API 4종 로그 주입
- [x] `/ops/audit-logs` 프론트 목록/필터/상세 구현

## 우선 기록 대상(Phase 1)
1. 사용자 상태 변경
2. 공지 생성/수정/게시/내림
3. 그로스클럽 운영 조치(블라인드/해제/삭제)
4. 액션키트 운영 조치(업로드/상태변경)

## 로그 스키마 초안
- `admin_id`
- `action`
- `target_type`
- `target_id`
- `reason` (nullable)
- `meta` (before/after json)
- `created_at`

## 저장/보안/성능 정책 (Phase 1)
1. 보존 기간
- 운영 감사로그는 기본 180일 보관 후 아카이브 또는 삭제 정책 적용
2. 민감정보 마스킹
- `meta`에는 비밀번호/토큰/원문 민감값 저장 금지
- 필요 시 길이/포맷만 저장하고 값은 마스킹 처리
3. 인덱스 전략
- 조회 성능을 위해 `created_at`, `action`, `target_type`, `admin_id` 인덱스 부여

## API 작업
1. `GET /api/v1/ops/audit-logs?actor=&action=&target_type=&from=&to=&page=&size=`
2. (내부) `record_admin_audit_log(...)` 공통 유틸

## API 네임스페이스 기준
- 운영 API는 `/api/v1/ops/*` 기준으로 구현한다.

## IA/화면 구성
1. 필터 영역
- 기간, 운영자, 액션, 대상 타입
2. 목록 테이블
- 시각, 운영자, 액션, 대상, 사유
3. 상세 패널
- 변경 전/후 값(meta diff)

## 구현 단계
1. Ops 홈 카드/라우트 추가
2. 마이그레이션 + 모델 추가
3. 공통 로깅 유틸 추가
4. 핵심 운영 API 4종에 로그 주입
5. 조회 API + 프론트 화면 구현

## 전체 실행 플랜 (End-to-End)
1. Phase 0: 범위/용어/액션코드 확정
- 액션코드 네이밍 컨벤션 확정
  - 예: `user.status.updated`, `growth_club.post.blinded`, `actionkit.item.status.updated`
- `target_type` 허용값 확정
  - 예: `user`, `growth_club_post`, `actionkit_item`, `announcement`
- `meta.before / meta.after` 최소 필드 스키마 가이드 문서화

2. Phase 1: 저장 인프라 구축 (완료)
- `admin_audit_logs` 테이블/인덱스 마이그레이션
- ORM 모델 등록 및 메타데이터 로드 연결
- 감사로그 기본 조회 API 골격 구현

3. Phase 2: 공통 기록 유틸/정책 구축 (완료)
- `record_admin_audit_log(...)` 공통 함수 구현
- 서비스/라우터 레이어에서 재사용 가능한 호출 방식 정리
- 민감정보 마스킹 정책 적용 지점 정의(유틸 레이어)

4. Phase 3: 운영 액션 API 로그 주입 (완료)
- Users: 상태 변경 API + 감사로그 기록
- Growth Club: 블라인드/해제/삭제 API + 감사로그 기록
- ActionKit: 상태 변경 API + 감사로그 기록
- Announcements: 공지 도메인 저장 모델/CRUD 선행 후 동일 패턴 적용

5. Phase 4: 감사로그 조회 고도화 (완료)
- 필터/정렬/페이지네이션 표준 응답 통일
- `from/to` 기간 필터 경계 처리(타임존 정책 포함)
- 대량 데이터 대비 인덱스/쿼리 계획 점검

6. Phase 5: 프론트 `/ops/audit-logs` 구현 (완료)
- 필터 바(운영자/액션/대상/기간)
- 목록 테이블(시각/운영자/액션/대상/사유)
- 상세 패널(meta diff, before/after 시각화)
- loading/error/empty 상태 + 페이징 UX

7. Phase 6: 테스트/운영 검증
- API 단위 테스트: 정상/권한오류/존재하지 않는 대상/필터 조합
- 트랜잭션 테스트: 비즈니스 액션 실패 시 로그 롤백
- 중복 방지 정책 테스트: 동일 상태 재요청(no-op) 동작 검증

8. Phase 7: 릴리즈/운영
- 운영 가이드(조회 방법/주요 액션코드 표) 문서화
- 180일 보존/아카이브 정책 배치 설계
- 개인정보/민감정보 마스킹 점검 체크리스트 반영

## 현재 구현 메모 (2026-02-23)
1. 완료 항목
- `admin_audit_logs` 테이블 추가 및 인덱스 구성(`admin_id`, `action`, `target_type`, `created_at`)
- 감사로그 모델/ORM 등록 완료
- `record_admin_audit_log(...)` 유틸 구현 완료
- `GET /api/v1/ops/audit-logs` 구현 완료
  - 필터: `actor`, `action`, `target_type`, `from`, `to`
  - 페이징: `page`, `size`
  - 응답: `items`, `total`, `page`, `size`

2. 완료 항목(추가)
- 운영 액션 API 로그 주입 완료
  - 사용자 상태 변경
  - 그로스클럽 블라인드/해제/삭제
  - 액션키트 상태변경
  - 공지 생성/수정/상태변경
- `/ops/audit-logs` 프론트 구현 완료
  - 필터(운영자/액션/대상타입/기간), 목록, 상세(meta JSON), 페이지네이션

3. 잔여 항목(고도화)
- (완료) 액션 코드/대상 타입 enum 표준화
- (완료) meta 마스킹 유틸 강제 적용
- (완료) 기간 필터 타임존 정책 고정(입력 timezone 미지정 시 UTC 처리)
- (잔여) 대량 데이터 운영 관점 인덱스/쿼리 계획 재검증(실데이터 기준)

## 테스트 기준 (Phase 1 최소)
1. 정상 기록
- 상태 변경/게시/블라인드/업로드 조치 성공 시 로그 1건 생성
2. 실패 롤백
- 비즈니스 액션 실패(예외) 시 로그도 함께 롤백되어 생성되지 않음
3. 중복 방지
- 동일 요청 재시도 시 의도하지 않은 중복 로그가 누적되지 않음(멱등 또는 중복 방지 규칙 명시)

## 완료 기준 (DoD)
1. 우선 기록 대상 4영역에서 조치 시 감사로그가 생성된다.
2. 운영자가 `/ops/audit-logs`에서 필터 조회 가능하다.
3. 로그 누락/중복 없는지 기본 테스트로 검증된다.
