# Tooling Setup Runbook

목적: `docs/context/tooling-state.md`의 목표 상태를 새 PC에서 재현하기 위한 설치/인증/검증 절차.

## 0) 기준 문서
- 목표 목록(정답지): `docs/context/tooling-state.md`
- 정책/운영 규칙: `docs/context/ops-rules.md`, `AGENTS.md`

## 1) 사전 준비
1. 저장소 동기화
- `git fetch origin`
- `git pull --rebase`
2. Codex CLI 동작 확인
- `codex --help`
3. MCP 명령 확인(버전 차이 대응)
- `codex mcp --help`
- `codex mcp list`
4. GitHub CLI 로그인 확인
- `gh auth status`

## 2) MCP 서버 설정
원칙: `tooling-state.md`의 **MCP Servers** 목록을 기준으로, 누락된 서버만 추가/활성화한다.

1. 현재 상태 확인
- `codex mcp list`
2. 누락 서버 식별
- `tooling-state.md`의 체크된 항목과 비교
3. 서버 추가/활성화
- 사용 중인 Codex 버전에 맞는 명령으로 추가(예: `add`, `enable`, `login` 계열)
- 명령 형식이 다르면 반드시 `codex mcp --help` 결과를 우선
4. 인증 필요 서버 로그인
- 서버별 OAuth/PAT/API Key 요구사항에 따라 로그인
- 비밀값은 문서/채팅에 평문 기록 금지

## 3) Skills 설정
원칙: `tooling-state.md`의 **Skills (Always-on / On-demand)** 를 기준으로 로컬 설치 상태만 맞춘다.

1. 시스템 스킬 확인
- `skill-creator`, `skill-installer`는 기본 제공(`.system`)
2. 사용자 스킬 존재 확인
- `ls ~/.codex/skills`
3. 누락 스킬 설치
- 필요 시 `skill-installer` 스킬로 설치
- 설치 후 안내대로 Codex 재시작

## 4) 검증
1. MCP 검증
- `codex mcp list`
- `tooling-state.md` 기준 서버가 `enabled`로 보이는지 확인
2. Skills 검증
- `~/.codex/skills` 디렉터리에 대상 스킬 존재 확인
3. 기능 검증(선택)
- GitHub/Notion/Playwright 등 실제 연동이 필요한 서버는 최소 1회 호출 테스트

## 5) 실패 대응
1. 명령 미지원/형식 불일치
- `codex mcp --help` 기준으로 명령 재작성
2. 인증 실패
- 토큰 권한 범위(scope), 만료 여부, 계정 전환 상태 점검
3. 설치 후 미노출
- Codex 재시작 후 `codex mcp list` 재확인
4. 계속 실패 시
- 실패 명령/오류 메시지는 비밀값 마스킹 후 `docs/context/handoff.md`에 요약

## 6) 업데이트 규칙
1. 서버/스킬 목록 변경 시
- `docs/context/tooling-state.md` 체크박스/목록 갱신
2. 절차 변경 시
- 이 문서(`tooling-setup.md`)만 수정
3. 둘 다 변경이면
- 두 문서를 함께 업데이트하고 `handoff.md`에 변경 사실 기록
