---
trigger: always_on
---

# AGENTS.md Loader Rule

Before any analysis, code edit, or command execution, resolve and apply AGENTS instructions using this order:

1. Start from the target file/folder for the current task.
2. Walk upward directory-by-directory to repository root and collect **every** `AGENTS.md` found on that path.
3. Apply all collected files in precedence order: nearest (deepest path) first, then each parent `AGENTS.md` in order, then repository root `AGENTS.md`.
4. Do not skip intermediate parent folders if they contain `AGENTS.md`.
5. If no local `AGENTS.md` exists in the target path, apply repository root `AGENTS.md` if present.
6. If no `AGENTS.md` is found at all, proceed with global rules only.

Execution requirements:

- At the beginning of the response, explicitly state **all** `AGENTS.md` file(s) applied, in precedence order.
- If no local file is found, print: `no local AGENTS.md found`.
- If instructions conflict, prioritize nearest-to-target `AGENTS.md`, then parent folders in upward order, then repository root `AGENTS.md`, then this global rule.
- Never skip this lookup step.
