# StepZero MCP 최소 구성 권장안 (2026-02-13)

## 1) 목적

MCP 서버가 많아질수록 컨텍스트 점유와 운영 복잡도가 커지므로,  
현재 보유 목록에서 **필수에 가까운 최소 세트만 유지**하는 기준을 정리한다.

---

## 2) 결론 (최종 선정 스킬 기준)

최종 선정 스킬(11개)을 제대로 활용하려면 아래 **6개를 최종 MCP 세트**로 권장:

1. `filesystem`
2. `github-mcp-server`
3. `context7`
4. `sequential-thinking`
5. `playwright-mcp` (신규 필요)
6. `notion-mcp` (신규 필요)

이 조합이면 코드/파일 작업, GitHub 협업, 문서 참조, 복잡한 추론, E2E 자동화, Notion 자동화까지 커버된다.

---

## 3) 현재 목록 비교표 (당신의 현재 구성 기준)

| MCP | 권장 상태 | 판단 |
| --- | --- | --- |
| `filesystem` | 유지 | 로컬 코드/문서 작업의 기본 축. 대체 불가에 가까움 |
| `github-mcp-server` | 유지 | PR/이슈/리뷰 자동화 핵심 |
| `context7` | 유지 | 라이브러리/프레임워크 문서 조회 효율 높음 |
| `sequential-thinking` | 유지 | 복잡한 설계/디버깅 시 추론 품질 개선 |
| `playwright-mcp` | 추가 필요 | `playwright` 스킬 핵심 자동화에 필요 |
| `notion-mcp` | 추가 필요 | `notion-meeting-intelligence` 자동 반영에 필요 |
| `linear` | 조건부 | Linear를 실제로 주간 운영하면 유지, 아니면 비활성화 |
| `pencil` | 조건부 | 디자인/프로토타이핑 작업이 있을 때만 활성화 |
| `mcp-mermaid` | 조건부 | 다이어그램 산출이 잦을 때만 활성화 |

---

## 4) 스킬별 MCP 매핑 (최종 선정 11개 기준)

| 스킬군 | 필요 MCP |
| --- | --- |
| GitHub 자동화 (`gh-fix-ci`, `gh-address-comments`) | `github-mcp-server` |
| E2E 자동화 (`playwright`) | `playwright-mcp` |
| Notion 자동화 (`notion-meeting-intelligence`) | `notion-mcp` |
| 문서/레퍼런스 강화 (`openai-docs`, `nextjs-anti-patterns`, `api-design-principles`, `python-testing-patterns`) | `context7` |
| 로컬 분석 중심 (`security-best-practices`, `security-threat-model`, `architecture-patterns`) | `filesystem` |

---

## 5) 왜 OpenAI Docs MCP를 필수에서 제외했나

- `context7`이 이미 문서 검색 역할을 상당 부분 대체 가능
- OpenAI API/모델 작업 비중이 높지 않다면 중복 투자 가능성이 큼
- 따라서 기본 Lean 세트에서는 제외, 아래 조건일 때만 추가 권장:
  - OpenAI API 파라미터/사양 정확도가 특히 중요한 주간
  - 팀이 OpenAI 문서 기반 구현/검증을 반복하는 구간

## 6) 운영 규칙 (컨텍스트 절약)

1. 상시 활성화는 최종 6개(`filesystem`, `github-mcp-server`, `context7`, `sequential-thinking`, `playwright-mcp`, `notion-mcp`) 유지
2. `linear`, `pencil`, `mcp-mermaid`는 필요 시점에만 켜는 온디맨드 방식 적용
3. 월 1회 사용 로그 기준으로 미사용 MCP는 기본 비활성화

---

## 7) 보안 메모

- MCP 설정 공유 시 토큰 값(PAT/API Key)은 문서/채팅에 평문 노출하지 않는다.
- 이미 노출된 키는 즉시 폐기(revoke) 후 재발급한다.
