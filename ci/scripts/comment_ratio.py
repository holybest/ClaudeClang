"""주석률 게이트 (CLOC): 주석 줄 ÷ (코드 줄 + 주석 줄) ≥ 20 %.

사용: python comment_ratio.py [--min 20] [--json out.json] [경로...]   (기본 경로: src include)
종료 코드: 0 통과, 1 미달, 2 실행 오류.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--min", type=float, default=20.0)
    ap.add_argument("--json")
    ap.add_argument("paths", nargs="*", default=["src", "include"])
    args = ap.parse_args()

    paths = [p for p in args.paths if Path(p).exists()]
    if not paths:
        print("[N/A] 주석률 — 대상 없음")
        return 0

    proc = subprocess.run(["cloc", "--json", "--include-lang=C,C++,C/C++ Header", *paths],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stderr, file=sys.stderr)
        return 2
    out = proc.stdout.strip()
    if not out:
        print("[N/A] 주석률 — CLOC이 소스를 찾지 못함")
        return 0
    data = json.loads(out)
    total = data.get("SUM")
    if not total:
        print("[N/A] 주석률 — 대상 없음")
        return 0

    code, comment = total["code"], total["comment"]
    ratio = 100.0 * comment / (code + comment) if (code + comment) else 100.0
    if args.json:
        Path(args.json).parent.mkdir(parents=True, exist_ok=True)
        Path(args.json).write_text(json.dumps(
            {"code": code, "comment": comment, "blank": total["blank"],
             "comment_ratio_percent": round(ratio, 2), "required_percent": args.min},
            indent=1), encoding="utf-8")
    ok = ratio + 1e-9 >= args.min
    print(f"주석률: 주석 {comment}줄 / (코드 {code} + 주석 {comment}) = {ratio:.2f}% "
          f"(기준 {args.min:g}% 이상) {'OK' if ok else 'NOT MET'}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
