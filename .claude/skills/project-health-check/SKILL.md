---
name: project-health-check
description: "Run a comprehensive project health check and generate a Markdown report. Use this skill when the user asks to check project health, audit code quality, review project status, run a codebase checkup, or wants a periodic quality assessment. Also trigger when the user mentions 'health check', 'code quality report', 'project audit', 'technical debt check', or 'codebase review'. Proactively suggest this skill when the user starts a new session and wants to understand the current state of the project."
---

# Project Health Check

Generate a comprehensive project health report by analyzing the codebase, tests, dependencies, and development practices. The report is saved as a Markdown file for tracking over time.

## When to Use

- Periodic project quality assessment (weekly/sprint-end)
- Before major releases or milestones
- When onboarding to understand project state
- After large refactoring to verify nothing regressed
- When the user asks "how's the project looking?" or similar

## Report Generation Process

### Step 1: Gather Data

Run these checks in parallel where possible:

**Tests & Coverage**
```bash
# Backend
cd app-backend && uv run pytest -q --tb=no 2>&1 | tail -5

# Frontend
cd app-frontend && pnpm lint 2>&1 | tail -5
```

**Code Patterns**
Use Grep to count these across the codebase:
- `raise HTTPException` — legacy exception pattern (target: < 5)
- `except Exception:` with bare pass/continue — swallowed errors
- `# TODO` / `# FIXME` / `# HACK` — technical debt markers
- `type: ignore` / `noqa` — suppressed warnings

**Git Status**
```bash
git status --short
git log --oneline -10
```

**Dependencies**
```bash
# Check for outdated packages
cd app-backend && uv run pip list --outdated 2>&1 | head -20
```

**Structure Consistency**
- Check feature directories follow the convention (`features/{name}/domain/`, `features/{name}/application/`)
- Check API routes match feature structure (`api/v1/{feature}/`)
- Check for orphaned files (imports that reference deleted modules)

### Step 2: Analyze & Score

Rate each category on a simple scale:

| Score | Meaning |
|-------|---------|
| GREEN | Healthy, no action needed |
| YELLOW | Minor issues, address when convenient |
| RED | Needs immediate attention |

### Step 3: Generate Report

Save the report to `docs/plans/reports/REPORT-health-check-{YYYY-MM-DD}.md` using this template:

```markdown
# Project Health Check Report

> **Date:** {date}
> **Branch:** {branch}
> **Analyst:** Claude Code

## Summary

| Category | Status | Score |
|----------|--------|-------|
| Tests | {passed}/{total} passed | {GREEN/YELLOW/RED} |
| Lint | {errors} errors | {GREEN/YELLOW/RED} |
| Legacy Patterns | {count} remaining | {GREEN/YELLOW/RED} |
| Technical Debt | {todo_count} markers | {GREEN/YELLOW/RED} |
| Dependencies | {outdated_count} outdated | {GREEN/YELLOW/RED} |
| Code Structure | {assessment} | {GREEN/YELLOW/RED} |

## Overall Health: {HEALTHY / NEEDS_ATTENTION / CRITICAL}

---

## Details

### Tests & Coverage
- Backend: {X} passed, {Y} skipped, {Z} failed
- Frontend lint: {errors} errors, {warnings} warnings
- {Notable observations}

### Legacy Patterns
- `raise HTTPException`: {count} (target < 5)
- Bare `except Exception`: {count}
- {File-level breakdown if concerning}

### Technical Debt Markers
- TODO: {count}
- FIXME: {count}
- HACK: {count}
- {Top files with most markers}

### Dependencies
- Outdated packages: {list}
- Security advisories: {if any}

### Code Structure
- Feature directory compliance: {assessment}
- Naming consistency: {assessment}
- {Any structural anomalies}

---

## Recommendations

1. {Priority 1 recommendation}
2. {Priority 2 recommendation}
3. {Priority 3 recommendation}

---

## Trend (vs Previous)

{If a previous health check report exists in docs/plans/reports/, compare key metrics}

| Metric | Previous | Current | Trend |
|--------|----------|---------|-------|
| Test count | {prev} | {curr} | {up/down/same} |
| HTTPException count | {prev} | {curr} | {up/down/same} |
| TODO count | {prev} | {curr} | {up/down/same} |
```

## Key Principles

- **Be objective**: Report facts and numbers, not opinions. Let the scores speak.
- **Compare to previous**: If a prior health check exists, show the trend. Progress is motivating.
- **Actionable recommendations**: Each recommendation should be specific enough to act on. "Improve test coverage" is vague; "Add tests for `app/features/chat/` (0% coverage)" is actionable.
- **Don't alarm unnecessarily**: YELLOW doesn't mean broken. Reserve RED for things that actually block development or risk production issues.
- **Fast execution**: The whole check should complete in under 2 minutes. Don't run expensive operations.
