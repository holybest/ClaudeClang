"""소스코드 메트릭 게이트: 순환복잡도(CCN) 10 이하, 함수 라인 수 80 이하 (Lizard).

사용: python lizard_gate.py [--ccn 10] [--length 80] [--issues out.json] [경로...]
기본 경로는 src include. 위반은 Jenkins Warnings NG가 읽는 JSON(issues)으로도 쓴다.
종료 코드: 0 통과, 1 위반, 2 실행 오류.
"""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

WARN_RE = re.compile(
    r"^(?P<file>.+?):(?P<line>\d+): warning: (?P<func>.+?) has (?P<nloc>\d+) NLOC, "
    r"(?P<ccn>\d+) CCN, (?P<token>\d+) token, (?P<param>\d+) PARAM, (?P<length>\d+) length"
)


def write_empty_issues(path):
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text('{"issues": []}', encoding="utf-8")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--ccn", type=int, default=10)
    ap.add_argument("--length", type=int, default=80)
    ap.add_argument("--issues")
    ap.add_argument("paths", nargs="*", default=["src", "include"])
    args = ap.parse_args()

    paths = [p for p in args.paths if Path(p).exists()]
    if not paths:
        write_empty_issues(args.issues)
        print("[N/A] Lizard — 대상 없음")
        return 0

    proc = subprocess.run(
        [sys.executable, "-m", "lizard", "-C", str(args.ccn), "-L", str(args.length), "-w", *paths],
        capture_output=True, text=True)
    if proc.returncode not in (0, 1) and not proc.stdout.strip() and proc.stderr.strip():
        print(proc.stderr, file=sys.stderr)
        return 2

    issues = []
    for line in proc.stdout.splitlines():
        m = WARN_RE.match(line.strip())
        if not m:
            continue
        reasons = []
        if int(m["ccn"]) > args.ccn:
            reasons.append(f"순환복잡도 {m['ccn']} > {args.ccn}")
        if int(m["length"]) > args.length:
            reasons.append(f"함수 라인 수 {m['length']} > {args.length}")
        issues.append({
            "fileName": m["file"], "lineStart": int(m["line"]), "category": "Lizard",
            "type": "Metric", "severity": "HIGH",
            "message": f"{m['func']}: " + ", ".join(reasons or [line.strip()]),
        })

    if args.issues:
        Path(args.issues).parent.mkdir(parents=True, exist_ok=True)
        Path(args.issues).write_text(json.dumps({"issues": issues}, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
    for i in issues:
        print(f"{i['fileName']}:{i['lineStart']}: {i['message']}")
    print(f"Lizard: CCN ≤ {args.ccn}, 함수 라인 ≤ {args.length} — 위반 {len(issues)}건")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
