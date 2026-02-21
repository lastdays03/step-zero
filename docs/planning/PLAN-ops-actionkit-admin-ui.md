# PLAN: Ops ActionKit 관리 UI

## Status
- In Progress

## 목적
- 운영자(슈퍼유저)가 ActionKit 데이터/파일을 UI에서 관리할 수 있도록 `/ops` 관리 화면을 구현한다.
- 현재 DB 기반 ActionKit 구조(`actionkit_*` 테이블, 파일 버전 관리)를 운영 플로우에 연결한다.

## 범위
1. 카테고리/아이템 목록 및 검색
2. 아이템 상세 편집(메타데이터)
3. 파일 업로드/버전 교체/버전 목록
4. 변경 이력(최소: 파일 업로드 히스토리)

## 정보 구조(IA)
1. `/ops/actionkit`
- 상위 탭: `법령 가이드(laws)` / `액션키트(kits)`
- 보조 필터: 카테고리, 상태(active/inactive), 검색어
- 상태 용어 매핑: 현재 스키마는 `is_active`를 사용하며, 운영 UI에서 `게시중/중단`으로 라벨링한다.

2. `/ops/actionkit/items/:id`
- 기본 정보 섹션: 이름, 요약, 태그, 정렬, 상태
- 부가 정보 섹션:
  - laws: highlights
  - kits: related laws
- 파일 섹션:
  - current version 배지
  - 버전 히스토리 테이블
  - 새 버전 업로드 버튼

## UX 요구사항
1. 업로드 플로우
- 파일 선택 -> 사전 검증(확장자/크기) -> 업로드 실행 -> 완료 토스트
- 성공 시 즉시 현재 버전/다운로드 링크 갱신

2. 안전장치
- 업로드/활성상태 변경은 확인 모달 노출
- 실패 시 원인 메시지와 재시도 액션 제공

3. 접근 제어
- `/ops` 공통 정책 유지(슈퍼유저만)

## API 작업
### 이미 구현됨
- `POST /api/v1/actionkits/items/{item_id}/files` (버전 업로드)

### 추가 구현 필요
1. `GET /api/v1/ops/actionkit/categories?domain=...`
2. `GET /api/v1/ops/actionkit/items?...` (검색/필터/페이지네이션)
3. `GET /api/v1/ops/actionkit/items/{item_id}`
4. `PATCH /api/v1/ops/actionkit/items/{item_id}` (메타 수정)
5. `GET /api/v1/ops/actionkit/items/{item_id}/files` (버전 히스토리)

## API 네임스페이스 기준
- 운영 API는 `/api/v1/ops/*` 기준으로 구현한다.
- 공개 사용자 API(`/api/v1/actionkits/*`)와 분리 유지한다.

## 구현 단계
1. Ops API 스펙/응답 타입 정의
2. 감사로그 기록 인프라(테이블/유틸) 선반영 여부 확인
3. 백엔드 Ops ActionKit endpoint 구현
4. 프론트 `/ops/actionkit` 목록 화면 구현
5. 프론트 상세/업로드 화면 구현
6. 통합 검증(권한/업로드/버전 반영)

## 구현 게이트
- 파일 업로드/활성상태 변경 API는 감사로그 연동 없이 배포하지 않는다.

## 검증 항목
1. 권한 없는 사용자 접근 차단 확인
2. 파일 업로드 후 `is_current` 단일성 유지 확인
3. 버전 증가 규칙(`v{n}`) 및 다운로드 경로 갱신 확인
4. `npm run lint`, `pytest -q` 통과

## 다음 액션
1. Ops ActionKit API 상세 스펙 문서화
2. 프론트 와이어프레임(목록/상세) 확정
3. 구현 브랜치 작업 단위 분할(backend-api / frontend-ui)

## 이전 플랜 잔여 작업 이관
다음 항목들은 `completed/PLAN-actionkit-data-file-management.md`에서 후속 과제로 남은 내용이며, 본 플랜에서 구현한다.

1. Ops용 ActionKit 관리 CRUD 화면 구현
- 카테고리/아이템 관리
- 파일 업로드/버전 교체/버전 히스토리 조회

2. 업로드 정책 강화(관리자 화면 연동 범위)
- 파일 타입/크기 제한(ENV 기반)
- 실패 사유 노출 및 재시도 UX

3. 메타데이터 운영 정합성 보강
- 파일 `mime_type`, `size_bytes`, `checksum`, `version`, `is_current` 표시/검증
- current 파일 단일성 보장 상태를 운영 화면에서 확인 가능하도록 제공

4. 런타임/시드 경계 유지
- 런타임은 DB 단일 소스 유지
- 시드 소스(`scripts/seeds/actionkit_seed_source.py`)는 운영 화면에서 직접 참조하지 않도록 경계 유지
