# R2 스토리지 실전 통합 - 태스크 체크리스트

> Last Updated: 2026-03-06

---

## Phase 1: 인프라 연결 완성

- [x] **1-1** `config.py`에 R2 환경변수 추가 `[S]`
- [x] **1-2** `api.py`에 storage 라우터 등록 `[S]`
- [x] **1-3** `app-backend/.env.example`에 R2 변수 추가 `[S]`
- [x] **1-4** `app-frontend/.env.example`에 `NEXT_PUBLIC_STORAGE_URL=` 추가 `[S]`
- [x] ~~**1-5** `factory.py` — `getattr` 사용 중~~ — **Phase 1-1 완료 시 자동 해결 + `settings.STORAGE_BACKEND` 직접 접근으로 정리**

---

## Phase 2: 백엔드 서비스 → StorageBackend 전환

- [x] **2-1** ActionKit `service.py` — `storage.put()` 전환 `[M]`
- [x] **2-1b** Ops ActionKit `service.py` — `upload_file_for_item()` → `storage.put()` 전환 `[M]`
- [x] **2-2** ActionKit `file_pipeline.py` 리팩터 `[S]` — `save_upload_to_path()`, `file_checksum()` 제거
- [x] **2-3** GrowthClub `post_service.py` — 파일 저장 전환 `[M]`
- [x] **2-4** GrowthClub `post_service.py` — 파일 삭제 전환 `[S]`
- [x] **2-5** Profile `service.py` — 파일 저장 전환 `[S]`
- [x] **2-6** `main.py` — StaticFiles 조건부 마운트 `[S]`
- [x] **2-7** 테스트 통과 확인 `[S]` — 406 passed

---

## Phase 3: ActionKit 뷰어/다운로드 R2 대응

- [x] **3-1** `_resolve_file()` → StorageBackend 사용 `[M]`
- [x] **3-2** `/view` 엔드포인트 R2 대응 `[M]`
- [x] **3-3** `/download` 엔드포인트 R2 대응 `[S]`
- [x] **3-4** `_to_public_path()` R2 대응 `[S]`

---

## Phase 4: 프론트엔드 공통 모듈 적용

- [x] **4-1** `PostCard.tsx` import 변경 `[S]`
- [x] **4-2** `CommentSection.tsx` import 변경 `[S]`
- [x] **4-3** `profile/page.tsx` URL 생성 통일 `[S]`
- [x] **4-4** `ActionKitLibraryView.tsx` 다운로드 URL R2 분기 `[M]`
- [x] **4-5** `LawGuideView.tsx` 다운로드 URL R2 분기 `[S]`
- [x] **4-6** `growth-club/utils/upload-url.ts` re-export `[S]`
- [x] **4-7** ESLint 통과 확인 `[S]` — 0 errors

---

## Phase 5: R2 업로드 흐름 전환 (Presigned URL) — 부분 완료

> Phase 2 이후 백엔드 프록시 방식으로 R2 업로드가 이미 동작함 (FormData → backend → storage.put() → R2).
> Presigned URL 직접 업로드는 서버 대역폭 최적화로, 파일 최대 50MB이므로 현재는 불필요.

- [x] **5-4** presign 엔드포인트 `actionkit` kind 추가 `[S]`
- [ ] **5-1** `CreatePostForm.tsx` R2 모드 업로드 `[M]` — *deferred (optimization)*
- [ ] **5-2** `actionkit-edit-modal.tsx` R2 모드 업로드 `[M]` — *deferred*
- [ ] **5-3** `profile/page.tsx` R2 모드 업로드 `[M]` — *deferred*
- [ ] **5-5** Profile R2 메타데이터 API `[M]` — *deferred*
- [ ] **5-6** Growth Club `POST /posts/r2` 엔드포인트 `[M]` — *deferred*
- [ ] **5-7** 프론트엔드 `growthClubApi.createPostR2()` `[S]` — *deferred*

---

## Phase 6: 마이그레이션 실행 + E2E 검증

- [ ] **6-0** R2 버킷 CORS 설정 확인 `[S]`
- [ ] **6-1** Docker Compose R2 환경변수 설정 `[S]`
- [ ] **6-1b** Ops ActionKit `object_key` DB 정규화 `[S]`
- [ ] **6-2** R2 마이그레이션 스크립트 실행 `[M]`
- [ ] **6-3** 마이그레이션 검증 `[S]`
- [ ] **6-4** E2E: ActionKit 전체 흐름 `[M]`
- [ ] **6-5** E2E: Growth Club 전체 흐름 `[M]`
- [ ] **6-6** E2E: Profile 전체 흐름 `[S]`
- [ ] **6-7** E2E: 로컬 모드 검증 `[M]`
- [ ] **6-8** 롤백 절차 문서화 `[S]`

---

## Quality Gates

- [x] `cd app-backend && uv run pytest -q` — 406 passed
- [x] `cd app-frontend && pnpm lint` — 0 errors
- [x] `STORAGE_BACKEND=local` 기존 동작 100% 유지 (pytest 통과)
- [ ] `STORAGE_BACKEND=r2` 전환 시 전체 Feature 정상 — Phase 6에서 검증
- [x] 로컬 파일 직접 접근 코드 0곳 (서비스 레이어 기준, StorageBackend 내부 제외)

---

## 태스크 요약

| Phase | 태스크 수 | 완료 | 잔여 |
|-------|----------|------|------|
| Phase 1 | 5 | 5 | 0 |
| Phase 2 | 8 | 8 | 0 |
| Phase 3 | 4 | 4 | 0 |
| Phase 4 | 7 | 7 | 0 |
| Phase 5 | 7 | 1 | 6 (deferred) |
| Phase 6 | 9 | 0 | 9 |
| **총합** | **40** | **25** | **15** |
