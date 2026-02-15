# Feature 개발 패키지 경계

목표: 주니어 개발자 4명이 동시에 작업해도 파일 충돌을 최소화한다.

## 담당별 수정 경로(Frontend)
- 프로필 담당: `app-frontend/src/features/profile/**`
- 액션키트 담당: `app-frontend/src/features/actionkit/**`
- 커뮤니티 담당: `app-frontend/src/features/community/**`
- 운영콘솔 담당: `app-frontend/src/features/ops/**`
- 공용 계약(리드 승인): `app-frontend/src/features/shared/contracts/**`

## 담당별 수정 경로(Backend)
- 프로필 담당: `app-backend/app/api/v2/profile/**`, `app-backend/app/features/profile/**`
- 액션키트 담당: `app-backend/app/api/v2/actionkit/**`, `app-backend/app/features/actionkit/**`
- 커뮤니티 담당: `app-backend/app/api/v2/community/**`, `app-backend/app/features/community/**`
- 운영콘솔 담당: `app-backend/app/api/v2/ops/**`, `app-backend/app/features/ops/**`
- 대시보드 담당: `app-backend/app/api/v2/dashboard/**`, `app-backend/app/application/dashboard_service.py`
- 로드맵 담당: `app-backend/app/api/v2/roadmaps/**`, `app-backend/app/application/roadmap_service.py`
- 공용 진입점(리드 관리): `app-backend/app/api/v2/api.py`

## 충돌 방지 규칙
- 피처 간 내부 경로 직접 import 금지
- 공용 타입/스키마 수정은 리드 승인 후 최소 변경
- 한 PR에서 2개 이상 피처 폴더 동시 수정 금지
- 공용 진입점 파일 변경 시 우선순위 높은 PR 먼저 머지
