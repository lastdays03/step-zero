# PLAN: ActionKit 데이터/파일 관리 전환

## Status
- Completed

## 목표
- `app-backend/app/features/actionkit/domain/data.py` 하드코딩 데이터를 DB 기반으로 전환한다.
- 파일 경로를 코드 하드코딩이 아닌 메타데이터(`object_key`) 기반으로 관리한다.
- 로컬 환경 기준으로 안정적으로 운영하고, 추후 외부 파일 스토리지로 전환 가능한 구조를 확보한다.

## 확정 규칙
1. 로컬 스토리지 루트는 `STORAGE_LOCAL_ROOT`를 사용한다.
2. `STORAGE_LOCAL_ROOT`가 비어 있으면 기본 경로는 `app-backend/uploads`를 사용한다.
3. ActionKit 파일 경로 규칙:
- Laws: `uploads/actionkit/laws/{chapter_slug}/{item_id}/v{version}/{filename}`
- Kits: `uploads/actionkit/kits/{category_slug}/{item_id}/v{version}/{filename}`
4. `all` 카테고리는 조회 전용이며 저장 경로에는 사용하지 않는다.
5. 날짜는 경로에 넣지 않고 DB 메타(`uploaded_at`)로 관리한다.

## 데이터 모델(초안)
1. `actionkit_categories`
- `id`, `domain`(`laws|kits`), `slug`, `title`, `sort_order`, `is_active`

2. `actionkit_items`
- `id`, `domain`, `category_id`, `chapter_slug`, `item_code`, `name`, `summary`, `tag`, `is_active`, `published_at`

3. `actionkit_item_highlights`
- `id`, `item_id`, `content`, `sort_order`

4. `actionkit_related_laws`
- `id`, `item_id`, `law_name`, `law_summary`, `sort_order`

5. `actionkit_files`
- `id`, `item_id`, `version`, `object_key`, `original_filename`, `mime_type`, `size_bytes`, `checksum`, `uploaded_at`, `uploaded_by`, `is_current`

## 버전/최신본 관리
1. 동일 `item_id` 내에서 `is_current=true`는 1건만 허용한다.
2. 신규 업로드 시 이전 current를 false 처리하고 신규 버전을 current로 저장한다.
3. API 응답은 항상 current 파일을 기준으로 `download_url`을 생성한다.

## API 전환 범위
1. `GET /actionkits/laws`
2. `GET /actionkits/kits`
3. `GET /actionkits/laws/{chapter_id}`
4. `GET /actionkits/kits/{category_id}`

전환 원칙:
- API 계층은 DB/정적 데이터에 직접 접근하지 않고 application service를 호출한다.
- 응답 스키마는 v1 호환을 유지한다.

## 구현 단계
1. Migration + 모델 추가 (`actionkit_*` 테이블)
2. Repository/Application Service 구현
3. 시드 스크립트(`domain/data.py` -> DB) 작성
4. API를 service 기반으로 교체
5. 다운로드 URL 생성 로직 단일화
6. 프론트 타입/다운로드 로직 정리

## 검증 계획
1. Backend: `cd app-backend && .venv/bin/pytest -q`
2. Frontend: `cd app-frontend && npm run lint`
3. 경로 정합성 체크:
- DB `object_key`와 실제 파일 존재 여부 대조 스크립트 실행

## 완료 결과
1. `actionkit_*` 테이블 마이그레이션 적용 완료
2. ActionKit repository/application service 기반 API 전환 완료
3. `domain/data.py`를 seed 전용 소스로 분리 완료
4. 로컬 스토리지 경로 규칙(`uploads/actionkit/...`) 적용 완료
5. 업로드 시 `version/mime/size/checksum` 메타 저장 파이프라인 추가 완료
6. 백엔드 테스트/마이그레이션 체크/프론트 lint 검증 완료
