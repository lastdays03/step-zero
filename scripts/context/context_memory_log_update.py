#!/usr/bin/env python3
import argparse
import re
from datetime import date
from pathlib import Path


def upsert_line(block: str, label: str, value: str) -> str:
    pattern = re.compile(rf"(?m)^-\s*{re.escape(label)}:\s*.*$")
    replacement = f"- {label}: {value}"
    if pattern.search(block):
        return pattern.sub(replacement, block)
    return block.rstrip() + "\n" + replacement + "\n"


def main():
    parser = argparse.ArgumentParser(description="Update daily context validation entry")
    parser.add_argument("--file", default="docs/context/context-memory-validation-log.md")
    parser.add_argument("--date", dest="entry_date", default=date.today().isoformat())
    parser.add_argument("--recovery", required=True, help="복구 시간(분), 예: 7")
    parser.add_argument("--missing", required=True, help="누락 정보 유형, 예: 없음")
    parser.add_argument("--writing", required=True, help="문서 작성/갱신 시간(분)")
    parser.add_argument(
        "--success",
        required=True,
        choices=["성공", "부분성공", "실패"],
        help="이어서 작업 성공 여부",
    )
    parser.add_argument("--notes", required=True, help="보정 필요 사항")
    args = parser.parse_args()

    path = Path(args.file)
    content = path.read_text(encoding="utf-8")

    marker = f"### {args.entry_date}"
    start = content.find(marker)
    if start == -1:
        raise SystemExit(f"Entry date section not found: {args.entry_date}")

    next_idx = content.find("\n### ", start + len(marker))
    weekly_idx = content.find("\n## Weekly Summary", start + len(marker))
    candidates = [idx for idx in [next_idx, weekly_idx] if idx != -1]
    end = min(candidates) if candidates else len(content)

    block = content[start:end]
    block = upsert_line(block, "복구 시간(분)", args.recovery)
    block = upsert_line(block, "누락 정보 유형", args.missing)
    block = upsert_line(block, "문서 작성/갱신 시간(분)", args.writing)
    block = upsert_line(block, "이어서 작업 성공 여부", args.success)
    block = upsert_line(block, "보정 필요 사항", args.notes)

    new_content = content[:start] + block.rstrip() + "\n\n" + content[end:].lstrip("\n")
    path.write_text(new_content, encoding="utf-8")
    print(f"Updated daily entry: {args.entry_date} ({path})")


if __name__ == "__main__":
    main()
