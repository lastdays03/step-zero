# 템플릿 매칭 수정 — 태스크 체크리스트

Last Updated: 2026-03-02

## Phase 1: 코드 수정 [Effort: S]

- [ ] **T-1** `template_resolver.py` — resolve() docstring을 5단계 우선순위로 업데이트
- [ ] **T-2** `template_resolver.py` — 3순위(btype+stype) 매칭 블록 삽입 (L71 이후)

## Phase 2: 테스트 추가 [Effort: M]

- [ ] **T-3** `test_template_resolver.py` — `_create_approved_template` 헬퍼에 `startup_type` 파라미터 추가
- [ ] **T-4** `test_resolve_partial_stype_match` — btype+stype 매칭 동작 검증
- [ ] **T-5** `test_resolve_exact_over_partial_stype` — 1순위(정확) > 3순위(btype+stype) 우선순위 검증
- [ ] **T-6** `test_resolve_smethod_over_stype` — 2순위(btype+smethod) > 3순위(btype+stype) 우선순위 검증
- [ ] **T-7** `test_resolve_stype_fallback_when_no_smethod` — smethod=None 입력 시 stype 매칭 검증
- [ ] **T-8** `test_resolve_common_fallback_still_works` — 4순위 공통 폴백 회귀 검증

## Phase 3: 검증 [Effort: S]

- [ ] **T-9** `pytest tests/services/test_template_resolver.py -v` — 대상 테스트 전체 통과
- [ ] **T-10** `pytest -q` — 전체 스위트 회귀 없음 확인

## Phase 4: 커밋 [Effort: S]

- [ ] **T-11** 변경사항 커밋 (`feat: template resolve()에 btype+stype 매칭 3순위 추가`)

---

## 의존성

```
T-1, T-2 → T-9 (코드 수정 후 테스트)
T-3 → T-4~T-8 (헬퍼 수정 후 테스트 작성)
T-4~T-8 → T-9 (테스트 작성 후 실행)
T-9 → T-10 → T-11
```
