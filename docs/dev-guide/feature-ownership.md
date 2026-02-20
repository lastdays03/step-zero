# Feature Ownership (Junior 4)

## 목적
- 작업 충돌을 줄이고 코드 리뷰 책임을 명확히 한다.

## 담당 매핑
1. Junior A
- Backend: `features/auth`, `features/profile`
- Frontend: `features/auth`, `features/profile`

2. Junior B
- Backend: `features/roadmaps`, `features/dashboard`
- Frontend: `features/roadmap`, `features/dashboard`

3. Junior C
- Backend: `features/actionkit`, `features/growth_club`
- Frontend: `features/actionkit`, `features/growth-club`

4. Junior D
- Backend: `features/ops`, `features/rag`
- Frontend: `ops` 화면 + 공통 API 연동

## 리뷰 규칙
- 담당자 본인 + 인접 도메인 담당자 1명 리뷰를 기본으로 한다.
- 경계 밖 파일 변경 시, 해당 도메인 담당자 승인 없이는 머지하지 않는다.

## 충돌 방지
- 같은 feature 동시 작업 시 작업 전 Slack/Linear에 "파일 잠금" 공지
- 공용 파일(`api/deps.py`, `core/*`, `schemas.py`) 변경은 사전 합의 후 진행
