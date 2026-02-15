#!/usr/bin/env python3
import re
import statistics
from collections import Counter
from pathlib import Path
import argparse

STATUS_SCORE = {"성공": 1.0, "부분성공": 0.5, "실패": 0.0}
IGNORE_MISSING = {"", "없음", "-", "N/A", "na", "none"}


def first_number(text: str):
    m = re.search(r"-?\d+(?:\.\d+)?", text)
    return float(m.group(0)) if m else None


def parse_entries(content: str):
    blocks = re.split(r"\n###\s+", content)
    entries = []
    for block in blocks:
        lines = block.strip().splitlines()
        if not lines:
            continue
        date = lines[0].strip()
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
            continue

        joined = "\n".join(lines[1:])
        rec = re.search(r"(?m)^-\s*복구 시간\(분\):[ \t]*(.*)$", joined)
        miss = re.search(r"(?m)^-\s*누락 정보 유형:[ \t]*(.*)$", joined)
        status = re.search(r"(?m)^-\s*이어서 작업 성공 여부:[ \t]*(.*)$", joined)

        recovery = first_number(rec.group(1).strip()) if rec else None
        missing = (miss.group(1).strip() if miss else "")
        success = (status.group(1).strip() if status else "")

        is_filled = (
            recovery is not None
            or success in STATUS_SCORE
            or (missing and missing not in IGNORE_MISSING)
        )

        entries.append(
            {
                "date": date,
                "recovery": recovery,
                "missing": missing,
                "success": success,
                "is_filled": is_filled,
            }
        )
    return entries


def normalize_missing(value: str):
    v = value.strip()
    if v in IGNORE_MISSING:
        return []
    parts = [p.strip() for p in re.split(r"[,/|]", v)]
    out = []
    for p in parts:
        if p and p not in IGNORE_MISSING:
            out.append(p)
    return out


def main():
    parser = argparse.ArgumentParser(
        description="Summarize docs/context/context-memory-validation-log.md"
    )
    parser.add_argument(
        "--file",
        default="docs/context/context-memory-validation-log.md",
        help="Path to validation log markdown",
    )
    parser.add_argument(
        "--target-days",
        type=int,
        default=7,
        help="Expected number of daily records",
    )
    args = parser.parse_args()

    path = Path(args.file)
    content = path.read_text(encoding="utf-8")
    entries = parse_entries(content)

    filled_entries = [e for e in entries if e["is_filled"]]

    recovery_vals = [e["recovery"] for e in filled_entries if e["recovery"] is not None]
    median = statistics.median(recovery_vals) if recovery_vals else None

    scores = [STATUS_SCORE[e["success"]] for e in filled_entries if e["success"] in STATUS_SCORE]
    success_rate = (sum(scores) / len(scores) * 100.0) if scores else None

    missing_counter = Counter()
    for e in filled_entries:
        for m in normalize_missing(e["missing"]):
            missing_counter[m] += 1

    top2 = missing_counter.most_common(2)

    print(f"기록 충족 여부({len(filled_entries)}/{args.target_days})")
    print(f"복구 시간 중앙값(분): {median if median is not None else 'N/A'}")
    print(
        f"이어서 작업 성공률(%): {round(success_rate, 2) if success_rate is not None else 'N/A'}"
    )
    print("누락 정보 유형 상위 2개:")
    if top2:
        for idx, (name, count) in enumerate(top2, start=1):
            print(f"{idx}. {name} ({count})")
    else:
        print("1. 없음")
        print("2. 없음")


if __name__ == "__main__":
    main()
