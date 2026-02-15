# Tooling State

목적: 새 PC에서 환경을 맞출 때 "목록 기준"으로 빠르게 설치/연결 상태를 점검한다.

## 마지막 업데이트
- Date: 2026-02-15
- Updated by: Codex

## MCP Servers
- [x] `context7`
- [x] `filesystem`
- [x] `github-mcp-server`
- [x] `linear`
- [x] `notion-mcp`
- [x] `pencil`
- [x] `playwright-mcp`
- [x] `sequential-thinking`
- [x] `stitch`

## Skills (Always-on, installed)
- [x] `gh-address-comments`
- [x] `gh-fix-ci`
- [x] `api-design-principles`
- [x] `architecture-patterns`
- [x] `linear`
- [x] `notion-meeting-intelligence`
- [x] `openai-docs`
- [x] `playwright`
- [x] `python-testing-patterns`

## Skills (On-demand, installed)
- [x] `security-best-practices`
- [x] `security-threat-model`

## Skills (Session-available in this repo)
- `api-design-principles`
- `architecture-patterns`
- `gh-address-comments`
- `gh-fix-ci`
- `linear`
- `notion-meeting-intelligence`
- `openai-docs`
- `playwright`
- `python-testing-patterns`
- `security-best-practices`
- `security-threat-model`
- `skill-creator`
- `skill-installer`

## Auth/Access Check
- [ ] GitHub CLI 로그인 (`gh auth status`)
- [ ] Codex MCP 로그인 (`codex mcp list` 확인 가능)
- [ ] Linear/Notion 연동 토큰 유효

## 새 PC 복구 시 사용 문구
`tooling-state.md 기준으로 MCP/Skills 설치 및 로그인 상태 점검해줘`

## Notes
- 비밀값(토큰/API 키)은 이 파일에 기록하지 않는다.
- 설치/연결 완료 시 체크박스를 갱신한다.
- 목록 기준:
- MCP는 `codex mcp list`에서 `enabled` 상태인 항목
- Skills는 `~/.codex/skills` 로컬 디렉터리 존재 기준으로 확인
- `skill-creator`, `skill-installer`는 시스템 스킬(`.system`)로 기본 제공
