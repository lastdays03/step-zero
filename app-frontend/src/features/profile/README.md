# Profile Feature Package

소유 범위:
- `api/`: 프로필 API 클라이언트
- `hooks/`: 프로필 전용 훅
- `components/`: 프로필 UI 컴포넌트
- `types/`: 프로필 타입

작업 원칙:
- 이 패키지 외부에서 내부 경로 직접 import 금지
- 외부에는 `index.ts`(public API)만 노출
