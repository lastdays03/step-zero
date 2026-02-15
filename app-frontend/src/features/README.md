# Frontend Feature Ownership

충돌 최소화를 위해 피처별 작업 경계를 고정한다.

- `profile/`: 프로필 기능 전용
- `actionkit/`: 액션키트 기능 전용
- `community/`: 커뮤니티 기능 전용
- `ops/`: 운영콘솔 기능 전용
- `dashboard/`: 대시보드 기능 전용
- `roadmap/`: 로드맵 기능 전용
- `shared/contracts/`: 피처 간 공용 타입/계약 (리드 개발자 승인 후 변경)

규칙:
- 피처 간 직접 내부 경로 import 금지 (`../other-feature/...` 금지)
- 피처 외부 노출은 각 피처의 `index.ts`만 사용
- 공용 변경이 필요하면 먼저 `shared/contracts`에 추가하고 각 피처에서 소비
