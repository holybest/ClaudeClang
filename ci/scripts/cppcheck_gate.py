"""Cppcheck 게이트: 대상 소스(src/, include/)의 지적이 0건이어야 한다. 예외(억제)는 없다.

- compile_commands.json 의 모든 파일(테스트 포함)을 분석한다. 라이브러리 함수가 테스트에서만
  호출되어도 `unusedFunction` 오탈락이 생기지 않게 하려는 것이다.
- 보고·판정은 src/, include/ 아래에서 발생한 지적만 대상으로 한다.
- **분석이 정상적으로 끝나지 않으면 실패**다. (분석이 안 돌았는데 통과로 처리하지 않는다.)

사용: python cppcheck_gate.py --compile-db build/compile_commands.json --xml out.xml
종료 코드: 0 통과, 1 지적 있음, 2 분석 실패.
"""

import argparse
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

TARGETS = ("src", "include")


def in_target(path, root):
    try:
        rel = Path(path).resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return rel.parts and rel.parts[0] in TARGETS


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--compile-db", required=True)
    ap.add_argument("--xml", required=True)
    args = ap.parse_args()
    root = Path.cwd()

    cmd = ["cppcheck", f"--project={args.compile_db}", "--enable=all", "--inconclusive",
           "--check-level=exhaustive", "--xml", "--xml-version=2", "--quiet", "-j", "4"]
    proc = subprocess.run(cmd, capture_output=True, text=True)

    out = proc.stderr  # cppcheck 은 XML 을 stderr 로 낸다
    start = out.find("<?xml")
    if proc.returncode != 0 or start < 0 or "<results" not in out:
        print("[FAIL] Cppcheck 분석이 정상적으로 끝나지 않았다 (통과로 처리하지 않음)", file=sys.stderr)
        print(f"종료 코드 {proc.returncode}\n{out.strip()[:2000]}", file=sys.stderr)
        return 2
    try:
        tree = ET.fromstring(out[start:])
    except ET.ParseError as e:
        print(f"[FAIL] Cppcheck XML 을 해석할 수 없다: {e}", file=sys.stderr)
        return 2

    errors = tree.find("errors")
    kept = []
    for err in list(errors) if errors is not None else []:
        locs = [loc.get("file", "") for loc in err.findall("location")]
        if any(in_target(f, root) for f in locs):
            kept.append(err)
        else:
            errors.remove(err)

    Path(args.xml).parent.mkdir(parents=True, exist_ok=True)
    ET.ElementTree(tree).write(args.xml, encoding="utf-8", xml_declaration=True)

    for err in kept:
        loc = next((l for l in err.findall("location") if in_target(l.get("file", ""), root)), None)
        where = f"{loc.get('file')}:{loc.get('line')}" if loc is not None else "?"
        print(f"{where}: {err.get('severity')}: {err.get('msg')} [{err.get('id')}]")
    print(f"Cppcheck: 대상(src/, include/) 지적 {len(kept)}건 (기준: 0건)")
    return 1 if kept else 0


if __name__ == "__main__":
    sys.exit(main())
