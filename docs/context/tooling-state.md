# Tooling State

목적: 새 PC에서 환경을 맞출 때 "목록 기준"으로 빠르게 설치/연결 상태를 점검한다.

## 마지막 업데이트
- Date: 2026-02-22
- Updated by: Claude Code
- 환경: Claude Code v2.1.50 (Codex CLI → Claude Code로 전환됨)

## 참조 문서
- 설치/인증/검증 실행 절차: `docs/context/tooling-setup.md`

## MCP Servers (Claude Code `~/.claude.json` 기준)

| 서버 | 상태 | 비고 |
|------|------|------|
| `context7` | ✅ 설치됨 | stdio / npx @upstash/context7-mcp |
| `filesystem` | ✅ 설치됨 | stdio / npx @modelcontextprotocol/server-filesystem |
| `github-mcp-server` | ✅ 설치됨 | http / api.githubcopilot.com — gh auth token 자동 주입 |
| `linear` | ✅ 설치됨 | http / mcp.linear.app — OAuth 로그인 세션에서 완료 필요 |
| `notion-mcp` | ✅ 활성 | 세션 공급자(cokacdir)를 통해 자동 연결됨, ~/.claude.json에는 없음 |
| `playwright` | ✅ 설치됨 | stdio / npx @playwright/mcp@latest (구 명칭: playwright-mcp) |
| `sequential-thinking` | ✅ 설치됨 | stdio / npx @modelcontextprotocol/server-sequential-thinking |
| `pencil` | ❌ 미지원 | Claude Code 마켓플레이스에 없음 |
| `stitch` | ❌ 미지원 | Claude Code 마켓플레이스에 없음 |

## Skills (Claude Code 플러그인 기준)

> ⚠️ Codex CLI의 `~/.codex/skills` 체계와 다름.
> Claude Code는 `~/.claude/settings.json`의 `enabledPlugins`로 관리한다.
> 확인 기준: `cat ~/.claude/settings.json`

| 구 Codex Skill | Claude Code 플러그인 | 상태 |
|---------------|---------------------|------|
| `gh-address-comments` | `pr-review-toolkit` | ✅ 설치됨 |
| `gh-fix-ci` | `code-review` | ✅ 설치됨 |
| `security-best-practices` | `security-guidance` | ✅ 설치됨 |
| `security-threat-model` | `security-guidance` | ✅ 설치됨 (동일 플러그인) |
| `playwright` | playwright MCP | ✅ MCP로 대체됨 |
| `linear` | linear MCP | ✅ MCP로 대체됨 |
| — | `commit-commands` | ✅ 설치됨 (신규 추가) |
| — | `feature-dev` | ✅ 설치됨 (신규 추가) |
| — | `skill-creator` | ✅ 설치됨 (신규 추가) |
| `api-design-principles` | `wshobson/agents@api-design-principles` | ✅ 설치됨 (skills.sh) |
| `architecture-patterns` | `wshobson/agents@architecture-patterns` | ✅ 설치됨 (skills.sh) |
| `notion-meeting-intelligence` | `davila7/claude-code-templates@notion-meeting-intelligence` | ✅ 설치됨 (skills.sh) |
| `openai-docs` | `openai/skills@openai-docs` | ✅ 설치됨 (skills.sh) |
| `python-testing-patterns` | `wshobson/agents@python-testing-patterns` | ✅ 설치됨 (skills.sh) |

## Auth/Access Check
- [x] GitHub CLI 로그인 (`gh auth status` → `lastdays0301-max` 확인)
- [x] GitHub MCP (`github-mcp-server`) — gh auth token 헤더로 자동 주입
- [x] Notion 연동 — 세션에서 `notion-get-users` 호출 가능 확인
- [ ] Linear OAuth — 서버 등록 완료, 신규 세션에서 OAuth 로그인 필요 (브라우저)

## 새 PC 복구 시 사용 문구
`tooling-state.md 기준으로 MCP/Skills 설치 및 로그인 상태 점검해줘`

## Notes
- 비밀값(토큰/API 키)은 이 파일에 기록하지 않는다.
- 설치/연결 완료 시 체크박스/표를 갱신한다.
- MCP 확인 기준: `~/.claude.json`의 `mcpServers` 항목 존재 여부
- 플러그인(Claude Code 마켓플레이스) 확인 기준: `cat ~/.claude/settings.json`
- skills.sh 스킬 확인 기준: `.claude/skills/` 또는 `.agents/skills/` 디렉터리 존재 여부
- `github-mcp-server` 헤더의 토큰은 `gh auth token` 으로 자동 발급된 값이므로 토큰 갱신 시 재등록 필요
- skills.sh 스킬 재설치: `npx skills add <owner/repo@skill> --yes`
