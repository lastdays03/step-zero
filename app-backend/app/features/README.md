# Backend Feature Ownership

도메인 단위 충돌 최소화를 위해 피처별 패키지 경계를 고정한다.

- `features/profile/`
- `features/actionkit/`
- `features/community/`
- `features/ops/`

각 피처는 아래 계층을 사용한다.
- `domain/`: 도메인 모델/규칙
- `application/`: 유스케이스/서비스

HTTP 라우팅 계층은 `app/api/v2/<feature>/`에 둔다.

공용 변경이 필요하면 기존 공용 모듈(`app/core`, `app/api/v2/schemas.py`)에 최소 변경 후 리뷰한다.
