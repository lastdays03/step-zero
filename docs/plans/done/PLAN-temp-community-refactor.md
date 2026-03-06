# Community Integration Refactor (Temp)

## 목적
- `feature/0-community-integration` 통합 코드의 운영 리스크를 우선순위대로 점검/개선한다.

## 진행 원칙
- 번호 순서대로 1개씩 처리한다.
- 각 항목은 `코드 수정 -> 검증 -> 상태 업데이트` 순서로 진행한다.

## 체크리스트
- [x] 1. 업로드 파일명 충돌 방지 (`time.time()` -> 고유 식별자)
- [x] 2. 업로드 파일 검증 추가 (확장자/용량/MIME)
- [x] 3. 작성자 지역/업종 데이터 소스 정합화
- [x] 4. 로드맵 생성 입력값 구조화 저장 (업종/지역/형태/오픈시점/예산/추가설명 분리)
- [x] 5. 파일 저장-DB 커밋 일관성 보강 및 삭제 시 파일 정리
- [x] 6. API 레이어 비즈니스 로직 분리 (application/repository)
- [x] 7. 구 `community` placeholder 코드 정리
- [x] 8. 프론트 업로드 URL 해석 로직 공통화

## 로그
- 2026-02-20: 플랜 생성, 1번부터 순차 진행 시작.
- 2026-02-20: 1번 완료. 업로드 파일명을 `uuid4` 기반으로 변경하고 저장 경로를 `growth-club/{kind}/{YYYY}/{MM}/...`로 세분화.
- 2026-02-20: 2번 완료. 백엔드/프론트 모두 업로드 검증(확장자/개수/개별 용량/총 용량)을 강제하고, 제한값을 ENV로 관리.
- 2026-02-20: 3번 완료. 글 작성 시 `UserProfile(region/category)`를 조회해 `neighborhood/industry` 스냅샷으로 저장, 공백/누락값 fallback 적용.
- 2026-02-20: 체크리스트 조정. 기존 4/5(프로필 자동연동/프로필 UI)는 보류로 제외하고, 로드맵 입력값 구조화 저장을 신규 4번으로 재정의.
- 2026-02-20: 4번 완료. 로드맵 입력값을 `description` 단일 문자열이 아닌 구조화 필드(형태/오픈시점/예산/추가설명)로 분리 저장하도록 API/모델/마이그레이션 반영.
- 2026-02-20: 5번 완료. 게시글 생성 시 파일 저장 후 DB 실패하면 파일 롤백, 게시글 삭제 시 첨부 파일 실제 삭제하도록 정합성 보강.
- 2026-02-20: 6번 완료. `growth_club/posts` 라우터의 게시글 생성/삭제 비즈니스 로직을 `features/growth_club/application/post_service.py`로 분리.
- 2026-02-20: 7번 완료. 사용되지 않는 레거시 `api/v1/community`, `features/community`, `frontend/features/community` placeholder를 제거하고 문서 경로를 `growth_club` 기준으로 정리.
- 2026-02-20: 8번 완료. 업로드 URL 해석 로직을 `features/growth-club/utils/upload-url.ts`로 분리하고 `PostCard`에서 공통 유틸을 사용하도록 정리.
