# Handoff

## 마지막 업데이트
- Date: 2026-02-19
- Branch: `develop`
- Latest pushed commit: `46578c0`

## 이번 세션 완료
- 로드맵 생성 UX 단일화:
  - `/roadmap`, `/dashboard` 모두 동일 공통 패널(`RoadmapGenerationPanel`) 사용
  - 분리된 유도/생성 화면을 채팅형 단일 플로우(질문 수집 -> AI 검증 -> 사용자 확인 -> 생성)로 통합
- 비로그인 사용자 유도 개선:
  - 생성화면은 그대로 노출
  - 질문 입력/질문 진행/검증/생성 시도 시 기존 `SocialAuthModal` 즉시 오픈
  - 로그인 페이지 리다이렉트 제거
- 대시보드 필요 서류 연동:
  - `GET /roadmaps/latest/detail` 기반으로 `DOCUMENT` 액션 렌더링
  - 현재 단계 기준 문서만 표시
  - 문서 상태(필수/완료) 표시 + 다운로드 링크(`download_url/file_url/template_url/source_url`) 지원
- 로드맵 화면 기본 선택 개선:
  - 페이즈 기본 선택을 현재 진행중(`IN_PROGRESS`) 단계 페이즈로 설정
  - 진행중이 없으면 `PENDING` -> 미완료 -> 첫 페이즈 순으로 fallback

## 검증
- Frontend: `cd app-frontend && npm run lint` 통과
- Frontend: `cd app-frontend && npm run build` 통과

## 다음 세션 시작점
1. 대시보드 필요 서류 카드에서 전체 보기/로드맵 딥링크 여부 결정
2. 다운로드 링크 없는 문서 항목의 생성 규칙(백엔드 프롬프트/정규화) 보강
3. 채팅형 생성 UI 시각 디테일(버블/타이포/상태 메시지) 정제
4. OpenAPI 타입 동기화 및 미사용 컴포넌트 정리

## 리스크/메모
- 문서 다운로드 링크는 데이터 소스에 URL이 있어야 활성화됨
- 로드맵 생성은 `app-worker`/Redis 미기동 시 진행되지 않음
- 워킹트리에 다수 변경이 누적되어 있어 PR 분리 전략이 필요함
