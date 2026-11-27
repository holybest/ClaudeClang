"""Compare `llvm-cov export` totals with the coverage target and list what is still uncovered.

Usage: python -I cov_gaps.py --summary summary.json --lcov coverage.lcov
                             [--line 100] [--branch 100] [--mcdc 100]
Exit code 0 when every given target is met, 1 otherwise.
"""

import argparse
import json
import sys
from collections import defaultdict


def uncovered(lcov_path):
    """Return {file: {"lines": [...], "branches": [...]}} for entries with zero hits."""
    gaps = defaultdict(lambda: {"lines": [], "branches": []})
    current = None
    with open(lcov_path, encoding="utf-8", errors="replace") as f:
        for raw in f:
            line = raw.strip()
            if line.startswith("SF:"):
                current = line[3:]
            elif line.startswith("DA:") and current:
                num, hits = line[3:].split(",")[:2]
                if int(hits) == 0:
                    gaps[current]["lines"].append(int(num))
            elif line.startswith("BRDA:") and current:
                num, _blk, _br, taken = line[5:].split(",")[:4]
                if taken in ("-", "0"):
                    gaps[current]["branches"].append(int(num))
    return gaps


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to a legacy code page
    ap = argparse.ArgumentParser()
    ap.add_argument("--summary", required=True)
    ap.add_argument("--lcov", required=True)
    ap.add_argument("--line", type=float, default=100.0)
    ap.add_argument("--branch", type=float, default=100.0)
    ap.add_argument("--mcdc", type=float, default=None)
    args = ap.parse_args()

    with open(args.summary, encoding="utf-8") as f:
        totals = json.load(f)["data"][0]["totals"]

    targets = [("line", "lines", args.line), ("branch", "branches", args.branch)]
    if args.mcdc is not None:
        targets.append(("MC/DC", "mcdc", args.mcdc))

    failed = False
    for label, key, goal in targets:
        entry = totals.get(key)
        if entry is None:
            print(f"{label}: llvm-cov 출력에 {key} 항목이 없다 (LLVM 버전/계측 옵션 확인)")
            failed = True
            continue
        pct = entry.get("percent", 100.0 if entry.get("count", 0) == 0 else 0.0)
        ok = pct + 1e-9 >= goal
        failed |= not ok
        print(f"{label}: {entry['covered']}/{entry['count']} = {pct:.2f}% (목표 {goal:g}%) {'OK' if ok else 'NOT MET'}")

    gaps = uncovered(args.lcov)
    if gaps:
        print("\n미커버 위치 (이 위치를 실행하는 의미 있는 케이스를 설계해서 추가한다):")
        for path in sorted(gaps):
            g = gaps[path]
            if g["lines"]:
                print(f"  {path} 라인: {', '.join(map(str, sorted(set(g['lines']))))}")
            if g["branches"]:
                print(f"  {path} 분기 미통과 라인: {', '.join(map(str, sorted(set(g['branches']))))}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
