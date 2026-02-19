---
trigger: always_on
---

# AGENTS.md Loader Rule

Before any analysis, code edit, or command execution, resolve and apply AGENTS instructions using this order:

1. Start from the target file/folder for the current task.
2. Walk upward directory-by-directory and find the nearest `AGENTS.md`.
3. If found, apply it as highest local instruction.
4. Continue upward to repository root and apply parent/root `AGENTS.md` as broader defaults.
5. If no local `AGENTS.md` exists in the target path, apply repository root `AGENTS.md`.
6. If no `AGENTS.md` is found at all, proceed with global rules only.

Execution requirements:

- At the beginning of the response, explicitly state which `AGENTS.md` file(s) were applied.
- If no local file is found, print: `no local AGENTS.md found`.
- If instructions conflict, prioritize the nearest `AGENTS.md`, then parent/root `AGENTS.md`, then this global rule.
- Never skip this lookup step.
