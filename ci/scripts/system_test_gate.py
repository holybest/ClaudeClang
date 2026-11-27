"""시스템 테스트 게이트 (CLAUDE.md 2.1절): 요구사항 커버리지 100 %, 성공률 100 %.

입력 (tests/system/)
  *.json       sw-system-test-case 스킬의 입력 데이터 (test_basis, test_cases). Excel 은 이 JSON 에서 생성한다.
  results.csv  실행 결과. 열: test_case_id,result,executed_at,executor   (result: PASS | FAIL)
               같은 ID 가 여러 번 나오면 마지막 행이 최신 결과다.

판정
  1. 각 JSON 을 스킬의 검증(build_workbook.py --check-only)으로 먼저 통과시킨다.
  2. docs/requirements/ 에 정의된 모든 SWR 이 시험 가능(testable)한 베이시스로 등록되고,
     제안(suggested)이 아닌 테스트 케이스로 1개 이상 커버된다 → 요구사항 커버리지 100 %.
  3. 모든 테스트 케이스(제안 포함)에 최신 결과가 PASS 이다 → 성공률 100 %. 결과가 없으면(미실행) 실패다.

요구사항도 시스템 테스트 데이터도 없는 초기 상태만 N/A(통과)로 처리한다.

사용: python system_test_gate.py [--issues out.json]
종료 코드: 0 통과, 1 위반.
"""

import argparse
import csv
import json
import re
import subprocess
import sys
from pathlib import Path

SWR_HEADING = re.compile(r"^#{2,4}\s+(SWR-(?:FUN|QUA|LIM|CON)-\d+)\b", re.M)
SWR_ID = re.compile(r"^SWR-(?:FUN|QUA|LIM|CON)-\d+$")
BUILD_WORKBOOK = Path(".claude/skills/sw-system-test-case/scripts/build_workbook.py")


def defined_requirements():
    found = set()
    for md in Path("docs/requirements").glob("*.md"):
        found.update(SWR_HEADING.findall(md.read_text(encoding="utf-8")))
    return found


def read_results(path):
    latest = {}
    if path.exists():
        with open(path, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                tid = (row.get("test_case_id") or "").strip()
                if tid:
                    latest[tid] = (row.get("result") or "").strip().upper()
    return latest


def write_empty_issues(path):
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text('{"issues": []}', encoding="utf-8")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--issues")
    args = ap.parse_args()

    root = Path("tests/system")
    files = sorted(root.glob("*.json")) if root.is_dir() else []
    swr = defined_requirements()
    if not swr and not files:
        write_empty_issues(args.issues)
        print("[N/A] 시스템 테스트 — 대상 없음 (요구사항과 tests/system/*.json 이 모두 없음)")
        return 0

    problems = []
    cases, covered = {}, set()  # cases: id -> suggested?, covered: 제안이 아닌 케이스가 커버한 베이시스 ID
    testable = {}

    if not files:
        problems.append("tests/system/*.json 이 없다 — 요구사항 커버리지 0 % (/sw-system-test-case 로 만든다)")
    for jf in files:
        proc = subprocess.run([sys.executable, str(BUILD_WORKBOOK), str(jf), "--check-only"],
                              capture_output=True, encoding="utf-8", errors="replace")
        if proc.returncode != 0:
            tail = " / ".join(l for l in proc.stdout.splitlines() if l.startswith("[오류]"))[:600]
            problems.append(f"{jf.as_posix()}: 스킬 검증 실패 — {tail or proc.stderr.strip()[:300]}")
            continue
        data = json.loads(jf.read_text(encoding="utf-8-sig"))
        for b in data.get("test_basis", []):
            testable[b["id"]] = b.get("testable", True) is not False
        for tc in data.get("test_cases", []):
            cases[tc["id"]] = bool(tc.get("suggested"))
            if not tc.get("suggested"):
                covered.update(tc.get("basis_ids", []))

    # 1) 요구사항 커버리지
    for bid in sorted(testable):
        if SWR_ID.match(bid) and bid not in swr:
            problems.append(f"{bid}: 시스템 테스트가 참조하는 요구사항이 docs/requirements/ 에 없다")
    uncovered = [r for r in sorted(swr) if not (r in covered and testable.get(r, False))]
    for r in uncovered:
        reason = ("베이시스에 등록되지 않음" if r not in testable else
                  "시험 불가(testable=false)로 표시됨" if not testable[r] else
                  "제안이 아닌 테스트 케이스로 커버되지 않음")
        problems.append(f"{r}: 요구사항 커버리지 미달 — {reason}")
    cov_n = len(swr) - len(uncovered)
    cov_pct = 100.0 * cov_n / len(swr) if swr else 100.0
    print(f"요구사항 커버리지: {cov_n}/{len(swr)} = {cov_pct:.1f}% (기준 100%)")

    # 2) 성공률
    results = read_results(root / "results.csv")
    unrun = [t for t in sorted(cases) if t not in results]
    failed = [t for t in sorted(cases) if results.get(t) not in (None, "PASS")]
    passed = sum(1 for t in cases if results.get(t) == "PASS")
    for t in unrun:
        problems.append(f"{t}: 실행 결과가 없다 (tests/system/results.csv)")
    for t in failed:
        problems.append(f"{t}: 결과 {results[t]} (PASS 아님)")
    rate = 100.0 * passed / len(cases) if cases else 0.0
    print(f"시스템 테스트 성공률: {passed}/{len(cases)} = {rate:.1f}% (기준 100%)")

    issues = [{"fileName": "tests/system", "lineStart": 1, "category": "SystemTest",
               "type": "Gate", "severity": "HIGH", "message": p} for p in problems]
    if args.issues:
        Path(args.issues).parent.mkdir(parents=True, exist_ok=True)
        Path(args.issues).write_text(json.dumps({"issues": issues}, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
    for p in problems:
        print(p)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
