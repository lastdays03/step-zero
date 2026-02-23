#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  echo "Usage: $0 <target-repo-path> <project-name> [standards-repo-path]"
  echo "Example: $0 /tmp/new-project my-project /tmp/team-standards"
  exit 1
fi

TARGET_DIR="$1"
PROJECT_NAME="$2"
STANDARDS_DIR="${3:-/tmp/team-standards}"
APPLY_SCRIPT="$STANDARDS_DIR/scripts/apply-standards.sh"

if [[ ! -d "$TARGET_DIR" ]]; then
  echo "Target repo path does not exist: $TARGET_DIR"
  exit 1
fi

if [[ ! -x "$APPLY_SCRIPT" ]]; then
  echo "Standards apply script not found: $APPLY_SCRIPT"
  echo "Prepare standards repo first, then retry."
  echo "Expected structure: <standards>/scripts/apply-standards.sh"
  exit 1
fi

"$APPLY_SCRIPT" "$TARGET_DIR" "$PROJECT_NAME"

echo ""
echo "Bootstrap completed."
echo "Next steps:"
echo "1) Review generated files in $TARGET_DIR"
echo "2) Record project-specific exceptions in docs/context/decisions.md"
echo "3) Commit the generated baseline"
