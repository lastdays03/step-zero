# 토큰 만료 테스트 가이드

## 테스트용 설정값

| 항목 | 프로덕션 | 테스트용 | 설정 위치 |
|------|---------|---------|-----------|
| Access Token 만료 | 30분 | **2분** | `app-backend/.env` → `ACCESS_TOKEN_EXPIRE_MINUTES=2` |
| Refresh Token 만료 | 7일 | **5분** | `app-backend/.env` → `REFRESH_TOKEN_EXPIRE_MINUTES=5` |
| Proactive Refresh 마진 | 만료 5분 전 | **만료 1분 전** | `app-frontend/src/lib/api-client.ts` → `PROACTIVE_REFRESH_MARGIN_MS` |

> `REFRESH_TOKEN_EXPIRE_MINUTES`가 설정되면 `REFRESH_TOKEN_EXPIRE_DAYS`보다 우선 적용됩니다.

## 타임라인 요약

```
0:00  로그인
1:00  Proactive Refresh 발동 (만료 1분 전 = 로그인 후 1분)
2:00  Access Token 만료 → 401 interceptor 발동
4:00  Proactive Refresh 발동 (갱신된 토큰 기준)
5:00  Refresh Token 만료 → 로그아웃
```

## 사전 준비

1. 백엔드 재시작 (설정 반영)
   ```bash
   # Docker 환경
   docker compose -f docker-compose.dev.yml restart app-backend app-worker

   # 로컬 환경
   cd app-backend && make run
   ```

2. 프론트엔드 재시작 (HMR이 반영하지만 확실히)
   ```bash
   cd app-frontend && pnpm dev
   ```

3. 브라우저 DevTools 준비
   - Console 탭 열기
   - Network 탭 열기 (XHR/Fetch 필터)
   - Application → Local Storage → `http://localhost:3000`

---

## 테스트 1: Proactive Refresh (백그라운드 갱신)

**목적:** Access Token 만료 전에 자동으로 갱신되는지 확인

### 절차

1. 로그인 후 대시보드 진입
2. **아무 조작 없이** 1분 대기
3. Network 탭 관찰

### 기대 결과

- [ ] 로그인 ~1분 후 `/auth/refresh` POST 요청 발생 (proactive)
- [ ] 응답 200, 새 `access_token` + `refresh_token` 반환
- [ ] Local Storage의 `token`, `refresh_token` 값이 갱신됨
- [ ] 콘솔에 에러 없음
- [ ] 사용자 화면 변화 없음 (무중단)

### 확인 방법

```javascript
// Console에서 토큰 만료 시각 확인
const token = localStorage.getItem('token');
const payload = JSON.parse(atob(token.split('.')[1]));
console.log('만료:', new Date(payload.exp * 1000).toLocaleTimeString());
console.log('현재:', new Date().toLocaleTimeString());
```

---

## 테스트 2: 401 Interceptor (Access Token 만료 후 자동 복구)

**목적:** Proactive Refresh가 실패했을 때 401 응답으로 갱신되는지 확인

### 절차

1. 로그인 후 대시보드 진입
2. Console에서 proactive refresh 타이머 제거:
   ```javascript
   // proactive refresh 비활성화 (401 interceptor 테스트용)
   // api-client.ts의 타이머를 우회하기 위해 토큰의 exp를 과거로 조작하지 않고
   // 단순히 2분 대기하면 access token이 만료됨
   ```
3. **2분 대기** (access token 만료 대기)
4. 만료 직전에 proactive refresh가 발동하므로, 이를 방지하려면:
   ```javascript
   // Local Storage에서 token을 만료된 값으로 교체
   // 1) 현재 refresh_token은 보존
   // 2) token만 만료된 JWT로 교체
   const oldToken = localStorage.getItem('token');
   const [header, payload, sig] = oldToken.split('.');
   const p = JSON.parse(atob(payload));
   p.exp = Math.floor(Date.now() / 1000) - 60; // 1분 전 만료
   const fakeToken = header + '.' + btoa(JSON.stringify(p)) + '.' + sig;
   localStorage.setItem('token', fakeToken);
   ```
5. 페이지에서 데이터 로딩 액션 수행 (메뉴 이동, 새로고침 등)

### 기대 결과

- [ ] API 요청 → 401 응답
- [ ] 자동으로 `/auth/refresh` POST 요청 발생
- [ ] 새 토큰 발급 후 원래 API 요청 자동 재시도
- [ ] 재시도 요청 성공 (200)
- [ ] 콘솔에 에러 없음
- [ ] 사용자 화면 정상 렌더링 (끊김 없음)

---

## 테스트 3: 동시 다발 401 (큐잉)

**목적:** 여러 API 호출이 동시에 401을 받았을 때 refresh가 1회만 실행되는지 확인

### 절차

1. 테스트 2와 동일하게 access token을 만료 상태로 만듦
2. 대시보드 페이지 새로고침 (여러 API 동시 호출 발생)

### 기대 결과

- [ ] `/auth/refresh` 요청이 **1회만** 발생
- [ ] 나머지 401 요청들은 큐에 대기 후 새 토큰으로 일괄 재시도
- [ ] Network 탭에서 재시도된 요청들이 모두 200
- [ ] 콘솔에 에러 없음

---

## 테스트 4: Refresh Token 만료 → 로그아웃

**목적:** Refresh Token도 만료되었을 때 안전하게 로그아웃되는지 확인

### 절차

1. 로그인
2. **5분 이상 대기** (refresh token 만료)
   - 이 동안 proactive refresh가 access token을 갱신하지만,
     refresh token 자체는 5분 후 만료
   - 또는 빠르게 테스트하려면:
   ```javascript
   // refresh_token을 잘못된 값으로 교체
   localStorage.setItem('refresh_token', 'expired-fake-token');
   // access_token도 만료된 값으로 교체 (테스트 2의 방법 사용)
   ```
3. 페이지에서 데이터 로딩 액션 수행

### 기대 결과

- [ ] API 요청 → 401
- [ ] `/auth/refresh` 시도 → 서버 401 응답 ("Invalid or expired refresh token")
- [ ] Local Storage의 `token`, `refresh_token`, `user`, `current_team_id` 모두 삭제됨
- [ ] **SessionExpiredBanner** 표시: "세션이 만료되었습니다. 다시 로그인해주세요."
- [ ] **콘솔에 AxiosError 없음** (에러 swallow 확인)
- [ ] 로그인 버튼 클릭 → 로그인 모달 정상 표시

---

## 테스트 5: 네트워크 단절 시 Refresh 재시도

**목적:** 네트워크 오류 시 최대 3회 재시도 후 로그아웃되는지 확인

### 절차

1. 로그인 후 access token 만료 상태로 만듦 (테스트 2 방법)
2. DevTools → Network 탭 → **Offline** 체크
3. 페이지에서 데이터 로딩 액션 수행
4. Network 탭 관찰 (재시도 간격: 1초, 2초, 3초)

### 기대 결과

- [ ] `/auth/refresh` 요청 3회 시도 (1초, 2초 간격으로 재시도)
- [ ] 3회 모두 실패 → `clearAuthState()` 호출
- [ ] SessionExpiredBanner 표시
- [ ] 콘솔에 AxiosError 없음

### 후속 확인

5. **Offline** 해제
6. 로그인 버튼 클릭 → 정상 로그인 가능

---

## 테스트 6: Refresh Token Reuse Detection (토큰 탈취 방어)

**목적:** 이미 사용(로테이션)된 refresh token 재사용 시 모든 세션이 강제 revoke되는지 확인

### 절차

1. 로그인 후 Console에서 현재 refresh_token 복사:
   ```javascript
   const oldRefreshToken = localStorage.getItem('refresh_token');
   console.log('OLD:', oldRefreshToken);
   ```
2. 정상적인 refresh 발생 대기 (1분 후 proactive refresh)
3. refresh 후 새 refresh_token이 발급됨 확인
4. 복사해둔 **이전** refresh_token으로 수동 갱신 시도:
   ```javascript
   fetch('{API_BASE_URL}/api/v1/auth/refresh', {
     method: 'POST',
     headers: { 'Content-Type': 'application/json' },
     body: JSON.stringify({ refresh_token: oldRefreshToken })
   }).then(r => r.json()).then(console.log).catch(console.error);
   ```

### 기대 결과

- [ ] 서버 응답 401: "Refresh token reuse detected. All sessions revoked."
- [ ] 해당 유저의 모든 refresh token이 DB에서 revoke됨
- [ ] 다른 탭/기기에서도 다음 refresh 시 로그아웃됨

---

## 테스트 후 원복

테스트 완료 후 반드시 프로덕션 값으로 복원:

```bash
# app-backend/.env
ACCESS_TOKEN_EXPIRE_MINUTES=30
# REFRESH_TOKEN_EXPIRE_MINUTES 라인 삭제 (기본값 7일 사용)

# app-frontend/src/lib/api-client.ts
# PROACTIVE_REFRESH_MARGIN_MS = 5 * 60 * 1000 으로 복원
```

서버 재시작 후 기존 세션의 토큰은 이전 만료 시각이 JWT에 인코딩되어 있으므로 영향 없음.
단, DB의 refresh token은 이미 짧은 TTL로 저장되었으므로 재로그인 필요.
