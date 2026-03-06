# Cloudflare R2 파일 저장소 마이그레이션 - 계획 검증 보고서

> Review Date: 2026-03-06
> Reviewer: Claude Opus 4.6

---

## 1. 전체 평가 요약

| 구분 | 평가 |
|------|------|
| **계획 문서 품질** | 우수 - 상세하고 실제 코드와 높은 일치율 |
| **Phase 0~3 구현** | 계획과 완전 일치 |
| **Phase 4 구현** | 7/8 완료, 핵심 1개(4-2) 미완 |
| **Phase 4B 계획** | 심각한 설계 리스크 발견 (아래 상세) |
| **Phase 5 계획** | 보완 필요 |

---

## 2. 발견된 리스크 (심각도 순)

### CRITICAL #1: Phase 4B File 테이블 Polymorphic 설계의 JSON 쿼리 성능 문제

계획에서 `version`, `is_current`, `kind`를 `metadata` JSON 컬럼에 저장하려 하지만, ActionKitRepository에서 이 필드들로 자주 쿼리한다.

**현재 쿼리 (인덱스 활용):**
```python
SELECT ActionKitFile WHERE item_id IN (...) AND is_current = True
ORDER BY version DESC
```

**전환 후 (JSON 추출 + 형변환 필요):**
```python
SELECT File WHERE owner_type = "actionkit_item" AND owner_id IN (...)
  AND metadata->>'is_current' = 'true'
ORDER BY CAST(metadata->>'version' AS INTEGER) DESC
```

문제점:
- JSON 필드 쿼리는 B-tree 인덱스 사용 불가 -> Full scan
- PostgreSQL `GIN` 인덱스로 부분 대응 가능하나, `ORDER BY` + `CAST`에는 효과 없음
- 테스트 DB(SQLite)에서는 `jsonb_set()`, JSON 인덱스 모두 미지원 -> 테스트 불가능

권장 수정안: `version`, `is_current`, `kind`를 실제 컬럼으로 유지 (nullable), `metadata`는 확장 전용으로만 사용.

### CRITICAL #2: Phase 4B Cascade Delete 손실

현재 `GrowthClubPostAttachment`는 FK(`post_id -> growthclubpost.id`)로 CASCADE DELETE 동작. Polymorphic `files` 테이블은 DB 레벨 FK가 없으므로:

- 게시글 삭제 시 첨부파일 레코드가 자동 삭제되지 않음 -> orphan 레코드 누적
- `FileRepository.delete_by_owner(owner_type, owner_id)` 메서드를 반드시 추가하고, 모든 삭제 로직에서 명시적 호출 필요

영향 범위:
- Growth Club `delete_post()` - 현재는 cascade로 자동 처리
- ActionKit 아이템 삭제 - 현재 FK `SET NULL`이라 안전하지만, File 테이블 전환 후 orphan 가능
- Profile 사용자 삭제 - 프로필 이미지 레코드 orphan

### CRITICAL #3: RoadmapTemplateAction FK 재매핑 누락

계획 문서에 언급되지 않았지만, `RoadmapTemplateAction` 모델이 `ActionKitFile.id`를 FK로 참조:

```python
# roadmap_template.py
actionkit_file_id: Optional[int] = Field(
    foreign_key="actionkit_files.id", ondelete="SET NULL"
)
```

Phase 4B에서 `actionkit_files` 테이블을 `files`로 통합하면:
- 기존 FK 관계가 깨짐
- `actionkit_file_id` -> `files.id` 재매핑 필요
- ID 타입 변경 가능성 (기존 `int` -> 새 테이블이 `UUID` PK면 타입 불일치)

### HIGH #1: owner_id 타입 불일치 위험

계획서의 File 테이블 설계에서 `owner_id: UUID`로 명시되어 있지만, 현재 3개 소유자 모델 PK가 모두 INTEGER.

권장: `owner_id`를 `int`로 통일하거나 `VARCHAR`(문자열)로 범용 설계. 문서 수정 필요.

### HIGH #2: Task 4-2 Growth Club R2 업로드 흐름 설계 모호

계획서에 "Content-Type으로 분기: multipart/form-data -> 기존, application/json -> R2"로 명시되어 있으나 FastAPI는 동일 경로에서 Content-Type 분기를 네이티브로 지원하지 않음.

권장 구현 방식:
- 방안 A: 별도 엔드포인트 (명확, 권장)
- 방안 B: Request 객체 직접 파싱 (단일 엔드포인트 유지)

### HIGH #3: Presign 엔드포인트 MIME 타입 검증 부재

`POST /api/v1/storage/presign`에서 `content_type` 파라미터에 대한 검증이 없음. 임의의 문자열이 들어와도 presigned URL이 생성됨.

### HIGH #4: useFileUpload 훅 에러 처리 및 메모리 관리 미흡

1. Presigned URL 만료 시 재시도 로직 없음
2. XMLHttpRequest cleanup 없음 (컴포넌트 언마운트 시 state update 리스크)
3. apiClient.post() 응답 타입이 암묵적

### HIGH #5: useFileDownload의 fetch() 상태 코드 미검증

```typescript
const res = await fetch(opts.url);
blob = await res.blob();  // 404여도 Blob으로 변환됨
```

### MEDIUM #1: create_presigned_put_url()이 동기 메서드

put/get/delete는 모두 `asyncio.to_thread()`로 래핑했지만, 이 메서드만 동기. 패턴 일관성 깨짐.

### MEDIUM #2: resolveUploadUrl R2 모드 경로 정규화 버그 가능성

로컬 모드에서 DB에 저장된 경로가 `api/v1/uploads/image.jpg` 형태인 경우, R2 모드로 전환하면 잘못된 경로 생성. Phase 5 마이그레이션 시 DB object_key 값도 정규화 필요.

### MEDIUM #3: ActionKit 경로 정규화 코드 중복

`ActionKitLibraryView`와 `LawGuideView`에서 동일한 레거시 경로 변환 로직 반복.

### LOW #1: R2_BUCKET_NAME 기본값 불일치

config.py 기본값 `"stepzero-uploads"` vs 실제 R2 버킷 `"stepzero"`.

---

## 3. 계획 문서에 누락된 항목

| # | 누락 항목 | 영향도 | 해당 Phase |
|---|----------|--------|-----------|
| 1 | `RoadmapTemplateAction.actionkit_file_id` FK 재매핑 | Critical | 4B |
| 2 | Cascade Delete 손실 대응 (`delete_by_owner` 메서드) | Critical | 4B |
| 3 | JSON 메타데이터 쿼리 성능 vs 컬럼 분리 결정 | Critical | 4B |
| 4 | `owner_id` 타입 결정 (UUID vs INTEGER vs VARCHAR) | High | 4B |
| 5 | Growth Club Content-Type 분기 구현 방식 명시 | High | 4 |
| 6 | Presign MIME 타입 검증 | High | 2 |
| 7 | useFileUpload 에러 재시도/cleanup | High | 3 |
| 8 | Phase 5에서 DB object_key 값 정규화 필요성 | Medium | 5 |
| 9 | R2_BUCKET_NAME 기본값 vs 실제 버킷명 불일치 | Low | 0 |

---

## 4. 계획에서 잘못된 부분

| # | 잘못된 내용 | 올바른 내용 |
|---|-----------|-----------|
| 1 | File 테이블의 `id: UUID`, `owner_id: UUID` | 현재 소유자 모델 PK가 모두 `int` -> `owner_id: int` 권장 |
| 2 | `version`, `is_current`, `kind`를 `metadata` JSON에 저장 | 자주 쿼리/정렬/필터하는 필드 -> 실제 컬럼 유지 권장 |
| 3 | Content-Type 기반 단일 엔드포인트 분기 | FastAPI에서 네이티브 미지원 -> 별도 엔드포인트 or Request 직접 파싱 필요 |

---

## 5. Phase별 실행 리스크 평가

| Phase | 리스크 | 권장 사항 |
|-------|--------|----------|
| **4-2** (Growth Club R2) | 중간 | Content-Type 분기 방식 확정 후 구현. 별도 엔드포인트 권장 |
| **4B** (File 공통화) | 높음 | 설계 재검토 필수. 컬럼 분리, FK 재매핑, Cascade 대응 추가 |
| **5** (파일 마이그레이션) | 중간 | DB object_key 정규화, 버킷명 확인, dry-run 필수 |
