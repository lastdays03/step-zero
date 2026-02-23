# PLAN: 구현 코드 품질 보완

- 작성일: 2026-02-22
- 분류: 기술 부채 / 버그 / 보안
- 대상: 구현 완료된 코드 한정 (미구현 기능 제외)
- 상태: 검토 완료, 수정 대기

---

## 개요

전체 소스 리뷰를 통해 구현된 코드에서 발견된 보완 사항을 우선순위별로 정리한다.
미구현 피처(settings, billing, ops 하위 화면 등)는 별도 PLAN에서 다루며 이 문서에서는 제외한다.

---

## 🔴 High — 운영 중 문제가 될 수 있는 이슈

### H-1. `worker_queue.py` — 에러 묵살 및 연결 비효율

**파일:** `app/features/roadmaps/application/worker_queue.py`

**문제:**
```python
except Exception:
    return False   # 로그 없음
```
- Redis 연결 실패 등 모든 예외가 묵살됨
- `False` 반환은 `jobs.py`에서 FAILED 처리하지만, **왜 실패했는지 어디에도 기록되지 않음**
- 운영팀이 큐 장애 원인을 파악할 방법 없음
- 추가로 `create_pool()`을 매 enqueue 호출마다 신규 생성 → Redis 연결 재사용 없음

**보완 방향:**
- `except Exception as e:` 로 변경 후 `logger.error(...)` 로 원인 기록
- `create_pool()` 을 앱 수준에서 1회 초기화하고 재사용하거나, 최소한 컨텍스트 범위 내 재사용 검토

---

### H-2. Growth Club 좋아요 — 전량 메모리 로드 후 Python 집계

**파일:** `app/api/v1/growth_club/posts.py:125,146-148`

**문제:**
```python
selectinload(GrowthClubPost.likes)   # 모든 포스트의 모든 좋아요 레코드 전부 로드

post_read.likes_count = len(post.likes)                                           # Python 집계
post_read.is_liked = any(like.user_id == current_user.id for like in post.likes)  # O(n) 루프
```
- 포스트 목록 조회 시 모든 like 레코드를 Python 메모리에 적재
- 인기 게시글의 경우 수천 건의 레코드를 로드 후 순회
- 규모 성장 시 쿼리 성능 급격히 저하

**보완 방향:**
- `selectinload` 대신 `COUNT` 서브쿼리 및 `EXISTS` 서브쿼리로 대체
- DB 레벨에서 집계 후 반환

---

### H-3. `vector_store.py` — API 키 없을 때 무음 통과

**파일:** `app/services/vector_store.py:12-14`

**문제:**
```python
if not settings.OPENAI_API_KEY:
    pass  # 경고 없음, 초기화 그냥 진행
```
- 서비스 기동 시점이 아니라 실제 RAG 호출 시점에 에러 발생
- 원인 추적이 어려움

**보완 방향:**
- `pass` 대신 `logger.warning(...)` 또는 `raise RuntimeError(...)` 로 명시적 처리
- 운영 환경(`ENVIRONMENT=production`)에서는 기동 실패로 처리 권장

---

## 🟡 Medium — 기술 부채 / 코드 일관성

### M-1. `datetime.utcnow()` 전체 코드베이스 30곳 이상 사용

**문제:**
- `datetime.utcnow()`는 Python 3.12에서 deprecated
- 현재 Python 3.11 환경이라 동작하지만, 버전 업그레이드 시 일괄 수정 필요

**영향 파일 (주요):**
```
app/core/security.py                         (3곳)
app/models/user.py, roadmap.py, actionkit.py,
  growth_club.py, team.py, profile.py        (각 2-4곳)
app/repositories/roadmap_job_repository.py   (5곳)
app/features/dashboard, growth_club,
  profile/application/*.py                   (다수)
app/api/v1/ops/reports.py                    (1곳)
```

**보완 방향:**
- 전체 `datetime.utcnow()` → `datetime.now(timezone.utc)` 교체
- `from datetime import timezone` import 추가 필요

---

### M-2. `law_etl.py`, `law_fetcher.py` — `print()` 직접 사용

**파일:**
- `app/services/law_etl.py:93`
- `app/services/law_fetcher.py:57, 64, 80, 117`

**문제:**
```python
print(f"Error processing {law_data.title}: {e}")
print(f"Warning: Directory {self.root_dir} does not exist.")
print(f"Fetched {len(results)} documents from {self.root_dir}")
```
- 나머지 코드는 모두 `get_logger()` 기반 구조화 로깅 사용
- Docker 환경에서 `print()` 출력은 로그 레벨/컨텍스트 없이 stdout에 섞임
- 프로덕션 로그 수집 시 구분 불가

**보완 방향:**
- `from app.core.logging import get_logger` 후 `logger = get_logger(__name__)` 사용
- `print()` → `logger.info()` / `logger.warning()` / `logger.error()` 교체

---

### M-3. `auth_service.py` — Google 유저 비밀번호 고정 문자열

**파일:** `app/features/auth/application/auth_service.py:45`

**문제:**
```python
hashed_password=security.get_password_hash("SOCIAL_AUTH_GOOGLE"),
```
- 모든 Google 로그인 유저가 동일한 해시값을 DB에 저장
- 실제 비밀번호 인증 플로우에서는 사용하지 않지만, DB 유출 시 소셜 계정 즉시 식별 가능
- 보안 감사(audit) 시 지적 대상

**보완 방향:**
```python
import secrets
hashed_password=security.get_password_hash(secrets.token_hex(32)),
```
- 회원가입 시 랜덤값으로 해시 생성 (기존 사용자는 마이그레이션 불필요, 신규부터 적용)

---

### M-4. `post_service.py` — 파일 삭제를 DB commit 이후에 수행

**파일:** `app/features/growth_club/application/post_service.py`

**문제:**
- DB commit이 완료된 후 파일 삭제를 시도하는 순서
- 파일 삭제 실패 시: DB에는 삭제된 것으로 기록되어 있지만 파일은 파일시스템에 잔존
- 반대의 경우(DB rollback 후 파일 삭제 성공)는 첨부파일 orphan 발생

**보완 방향:**
- 파일 삭제 실패 시 최소한 `logger.error(...)` 로 기록하여 수동 정리 가능하도록
- 장기적으로는 soft-delete 패턴(DB 레코드 플래그) 후 별도 cleanup job 검토

---

### M-5. `roadmaps/jobs.py` — 동일 job에 DB 쿼리 2회 중복

**파일:** `app/api/v1/roadmaps/jobs.py`

**문제:**
```python
# enqueue 실패 시 1차 조회
job = await repo.get_for_team(job_id=job_id, team_id=current_team.id)
await repo.mark_failed(job, ...)

# 이후 무조건 2차 조회 (항상 실행)
job = await repo.get_for_team(job_id=job_id, team_id=current_team.id)
```
- 1차에서 가져온 `job` 객체를 재사용하면 2차 쿼리 불필요

**보완 방향:**
- enqueue 성공/실패 분기와 무관하게 job 객체를 단일 변수로 관리하도록 리팩터링

---

## 🟢 Low — 소규모 개선

### L-1. `api-client.ts` — 401 처리 시 roadmap Job 폴링 미정리

**파일:** `app-frontend/src/lib/api-client.ts:39-44`

**문제:**
- 401 응답 시 localStorage 클리어 + 페이지 이동 처리
- `useRoadmapJob`의 polling interval이 컴포넌트 unmount 전까지 계속 실행됨
- 불필요한 네트워크 요청 발생

**보완 방향:**
- 401 처리 시 전역 이벤트(CustomEvent 또는 상태)를 발행하여 polling hook이 이를 구독하고 정리하도록 연결

---

### L-2. `ops/users.py` — 페이지네이션 없이 limit 50 하드코딩

**파일:** `app/api/v1/ops/users.py`

**문제:**
```python
select(User).order_by(User.created_at.desc()).limit(50)
```
- 유저 50명 초과 시 이후 목록 조회 방법 없음

**보완 방향:**
- `offset: int = Query(default=0)` 쿼리 파라미터 추가
- 또는 cursor 기반 페이지네이션 (created_at 기준) 검토

---

## 수정 우선순위 요약

| ID | 파일 | 분류 | 우선순위 | 예상 규모 |
|----|------|------|----------|----------|
| H-1 | worker_queue.py | 에러 묵살 / 연결 | 🔴 High | Small |
| H-2 | growth_club/posts.py | 성능 | 🔴 High | Medium |
| H-3 | vector_store.py | 무음 초기화 | 🔴 High | Small |
| M-1 | 전체 모델/서비스/repositories | datetime 교체 | 🟡 Medium | Large (일괄 치환) |
| M-2 | law_etl.py, law_fetcher.py | 로깅 교체 | 🟡 Medium | Small |
| M-3 | auth_service.py | 보안 | 🟡 Medium | Small |
| M-4 | post_service.py | 정합성 | 🟡 Medium | Small |
| M-5 | roadmaps/jobs.py | 중복 쿼리 | 🟡 Medium | Small |
| L-1 | api-client.ts | 폴링 정리 | 🟢 Low | Small |
| L-2 | ops/users.py | 페이지네이션 | 🟢 Low | Small |

---

## 참고: AGENTS.md 체크리스트 기준 대조

| 규칙 | 위반 여부 | 해당 이슈 |
|------|-----------|----------|
| 입력 검증, 예외 처리, 에러 메시지 포함 | ⚠️ 부분 위반 | H-1, H-3, M-4 |
| DB 접근은 repository 계층 사용 | ✅ 준수 | - |
| 인증/권한 로직 우회 구현 금지 | ✅ 준수 | - |
| Never print secrets | ✅ 준수 | - |
| 구조화 로깅 (print 사용 금지 명시 없음, 관행) | ⚠️ 관행 위반 | M-2 |
