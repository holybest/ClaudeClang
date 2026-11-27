"""Human-in-the-Loop 주석 게이트 (CLAUDE.md 2.4절).

src/, include/ 의 모든 소스·헤더 파일은 `@file` Doxygen 블록에 아래 항목을 가져야 한다.

    @par AI 작성 이력      모델 / 일시 / 요청자
    @par 사용자 리뷰       상태(미완료|완료) / 일시 / 리뷰어   (완료이면 일시·리뷰어 필수)

사용: python hitl_check.py [--issues out.json] [경로...]   (기본 경로: src include)
종료 코드: 0 통과, 1 위반.
"""

import argparse
import json
import re
import sys
from pathlib import Path

EXT = {".c", ".cc", ".cpp", ".cxx", ".h", ".hpp"}
BLOCK_RE = re.compile(r"/\*\*(.*?)\*/", re.S)
EMPTY = {"", "-", "—", "<>", "n/a", "N/A"}


def field(text, name):
    """`- 이름: 값 // 설명` 형태의 첫 항목 값을 돌려준다. 없으면 None."""
    m = re.search(rf"^\s*\*?\s*-\s*{name}\s*:(.*)$", text, re.M)
    if not m:
        return None
    return m.group(1).split("//")[0].strip()


def check(path):
    text = path.read_text(encoding="utf-8", errors="replace")
    block = next((b for b in BLOCK_RE.findall(text) if "@file" in b), None)
    if block is None:
        return ["@file Doxygen 블록이 없다"]
    ai = re.search(r"@par\s+AI 작성 이력(.*?)(?=@par|\Z)", block, re.S)
    rv = re.search(r"@par\s+사용자 리뷰(.*?)(?=@par|\Z)", block, re.S)
    problems = []
    if not ai:
        problems.append("`@par AI 작성 이력` 항목이 없다")
    else:
        for name in ("모델", "일시", "요청자"):
            v = field(ai.group(1), name)
            if v is None or v in EMPTY:
                problems.append(f"AI 작성 이력의 `{name}`이 비어 있다")
    if not rv:
        problems.append("`@par 사용자 리뷰` 항목이 없다")
    else:
        status = field(rv.group(1), "상태")
        if status not in ("미완료", "완료"):
            problems.append("사용자 리뷰의 `상태`는 `미완료` 또는 `완료`여야 한다")
        elif status == "완료":
            for name in ("일시", "리뷰어"):
                v = field(rv.group(1), name)
                if v is None or v in EMPTY:
                    problems.append(f"리뷰 `완료`인데 `{name}`이 비어 있다")
    return problems


def write_empty_issues(path):
    if path:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        Path(path).write_text('{"issues": []}', encoding="utf-8")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--issues")
    ap.add_argument("paths", nargs="*", default=["src", "include"])
    args = ap.parse_args()

    files = sorted(p for root in args.paths if Path(root).exists()
                   for p in Path(root).rglob("*") if p.is_file() and p.suffix in EXT)
    if not files:
        write_empty_issues(args.issues)
        print("[N/A] HITL 주석 — 대상 없음")
        return 0

    issues = []
    for f in files:
        for msg in check(f):
            issues.append({"fileName": f.as_posix(), "lineStart": 1, "category": "HITL",
                           "type": "Comment", "severity": "HIGH", "message": msg})
            print(f"{f.as_posix()}: {msg}")
    if args.issues:
        Path(args.issues).parent.mkdir(parents=True, exist_ok=True)
        Path(args.issues).write_text(json.dumps({"issues": issues}, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
    print(f"HITL 주석: 파일 {len(files)}개 검사, 위반 {len(issues)}건")
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
