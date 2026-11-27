"""Check bidirectional traceability recorded in docs/traceability/links.csv.

links.csv has the columns `parent_id,child_id`. IDs are typed by prefix:

    SWR  requirement        ARC  architecture component   IF  interface
    DD   detailed design    SRC  source file/function      UT  unit test
    IT   integration test

Rules (each `--until` stage includes the stages before it):
  req    every SWR is defined in docs/requirements/ (no links needed yet)
  arch   every SWR links down to an ARC; every ARC links up to an SWR
  design every ARC links down to a DD; every DD links up to an ARC
  code   every DD links down to a SRC; every SRC links up to a DD
  test   every SWR reaches a UT or IT; every UT/IT links up to an SWR/ARC/DD

Usage: python -I check_traceability.py [--root DIR] [--until req|arch|design|code|test]
Exit code 0 when no problem is found, 1 otherwise.
"""

import argparse
import csv
import re
import sys
from collections import defaultdict
from pathlib import Path

STAGES = ["req", "arch", "design", "code", "test"]
ID_RE = re.compile(r"\b(SWR-(?:FUN|QUA|LIM|CON)-\d+|ARC-\d+|IF-\d+|DD-\d+|UT-\d+|IT-\d+)\b")
HEADING_RE = re.compile(r"^#{2,4}\s+((?:SWR-(?:FUN|QUA|LIM|CON)|ARC|IF|DD)-\d+)\b", re.M)


def kind(node):
    return node.split("-", 1)[0]


def defined_ids(root):
    """IDs defined by a heading in docs/requirements, docs/architecture or docs/design."""
    found = set()
    for sub in ("requirements", "architecture", "design"):
        for md in (root / "docs" / sub).rglob("*.md"):
            found.update(HEADING_RE.findall(md.read_text(encoding="utf-8")))
    return found


def test_ids(root):
    """UT-/IT- IDs mentioned anywhere under tests/."""
    found = set()
    tests = root / "tests"
    if tests.is_dir():
        for p in tests.rglob("*"):
            if p.is_file() and p.suffix in {".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".md"}:
                found.update(i for i in ID_RE.findall(p.read_text(encoding="utf-8", errors="replace"))
                             if kind(i) in ("UT", "IT"))
    return found


def read_links(path):
    links = []
    if path.exists():
        with open(path, encoding="utf-8", newline="") as f:
            for row in csv.DictReader(f):
                if row.get("parent_id") and row.get("child_id"):
                    links.append((row["parent_id"].strip(), row["child_id"].strip()))
    return links


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to a legacy code page
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--until", choices=STAGES, default="test")
    args = ap.parse_args()
    root = Path(args.root)
    level = STAGES.index(args.until)

    links = read_links(root / "docs" / "traceability" / "links.csv")
    defined = defined_ids(root) | test_ids(root)
    down, up = defaultdict(set), defaultdict(set)
    for parent, child in links:
        down[parent].add(child)
        up[child].add(parent)

    problems = []
    for parent, child in links:
        for node in (parent, child):
            # SRC nodes name files/functions, so they cannot be checked against a heading
            if kind(node) != "SRC" and node not in defined:
                problems.append(f"알 수 없는 ID: {node} (링크 {parent} -> {child}, 정의 없음)")

    reqs = sorted(i for i in defined if kind(i) == "SWR")
    if not reqs:
        problems.append("정의된 SWR 요구사항이 없다 (docs/requirements/ 확인)")

    def need_down(nodes, child_kinds, label):
        for n in nodes:
            if not any(kind(c) in child_kinds for c in down[n]):
                problems.append(f"하향 누락: {n} -> {label} 없음")

    def need_up(nodes, parent_kinds, label):
        for n in nodes:
            if not any(kind(p) in parent_kinds for p in up[n]):
                problems.append(f"상향 누락: {n} <- {label} 없음")

    of = lambda k: sorted(i for i in defined if kind(i) == k)
    if level >= 1:
        need_down(reqs, {"ARC"}, "ARC")
        need_up(of("ARC"), {"SWR"}, "SWR")
    if level >= 2:
        need_down(of("ARC"), {"DD"}, "DD")
        need_up(of("DD"), {"ARC"}, "ARC")
    if level >= 3:
        need_down(of("DD"), {"SRC"}, "SRC")
        srcs = sorted({n for pair in links for n in pair if kind(n) == "SRC"})
        need_up(srcs, {"DD"}, "DD")
    if level >= 4:
        reach = lambda r: {c for c in down[r]} | {g for c in down[r] for g in down[c]}
        for r in reqs:
            if not any(kind(c) in ("UT", "IT") for c in reach(r)):
                problems.append(f"하향 누락: {r} -> UT/IT 시험 없음 (직접 또는 ARC/DD 경유)")
        tests = sorted(i for i in defined if kind(i) in ("UT", "IT"))
        need_up(tests, {"SWR", "ARC", "DD", "IF"}, "SWR/ARC/DD/IF")

    for p in problems:
        print(p)
    print(f"검사 범위: {args.until}, SWR {len(reqs)}개, 링크 {len(links)}개, 문제 {len(problems)}건")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
