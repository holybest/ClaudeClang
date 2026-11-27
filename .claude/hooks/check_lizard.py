"""Stop 훅: 구현이 끝났을 때(응답 종료 시) 변경된 소스를 Lizard로 검사한다. (CLAUDE.md 2.3절)

- 대상: git 에서 변경·추가된 src/, include/ 의 C/C++ 파일. 대상이 없으면 아무것도 하지 않는다.
- 기준: 순환복잡도 10 이하, 함수 라인 수 80 이하 (ci/scripts/lizard_gate.py — CI 와 같은 검사).
- 위반이 있으면 종료 코드 2 로 응답 종료를 막고 위반 내용을 Claude 에게 돌려보내 고치게 한다.
  이미 한 번 되돌려 보낸 뒤(stop_hook_active)에도 위반이면 무한 반복을 막기 위해 경고만 남긴다.
  최종 판정은 CI 가 한다.
- Lizard 는 호스트에 있으면 그것을, 없으면 ClaudeCLangBuild 이미지에서 실행한다.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

EXT = {".c", ".cc", ".cpp", ".cxx", ".h", ".hpp"}
GATE = "ci/scripts/lizard_gate.py"


def git_lines(root, *args):
    proc = subprocess.run(["git", *args], cwd=root, capture_output=True,
                          encoding="utf-8", errors="replace")
    return proc.stdout.splitlines() if proc.returncode == 0 else []


def changed_sources(root):
    names = set(git_lines(root, "diff", "--name-only", "HEAD", "--", "src", "include"))
    names |= set(git_lines(root, "ls-files", "--others", "--exclude-standard", "--", "src", "include"))
    return sorted(n for n in names if Path(n).suffix in EXT and (root / n).is_file())


def host_has_lizard():
    probe = subprocess.run([sys.executable, "-c", "import lizard"], capture_output=True)
    return probe.returncode == 0


def run_gate(root, files):
    if host_has_lizard():
        return subprocess.run([sys.executable, str(root / GATE), *files], cwd=root,
                              capture_output=True, encoding="utf-8", errors="replace")
    if shutil.which("docker"):
        return subprocess.run(
            ["docker", "run", "--rm", "-v", f"{root}:/work", "-w", "/work", "claudeclangbuild",
             "python3", GATE, *files], capture_output=True, encoding="utf-8", errors="replace",
            env={**os.environ, "MSYS_NO_PATHCONV": "1"})
    return None


def main():
    # Windows 콘솔의 기본 코드 페이지(cp949 등)와 무관하게 UTF-8 로 입출력한다.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    data = json.loads(sys.stdin.buffer.read().decode("utf-8") or "{}")
    root = Path(os.environ.get("CLAUDE_PROJECT_DIR") or data.get("cwd") or ".").resolve()
    if not (root / GATE).exists():
        return 0
    files = changed_sources(root)
    if not files:
        return 0

    proc = run_gate(root, files)
    if proc is None:
        print("[Lizard 훅] Lizard 도, Docker 도 없어 검사를 건너뛴다 (CI 에서 검사된다).", file=sys.stderr)
        return 0
    if proc.returncode == 0:
        return 0
    if proc.returncode == 2:  # 도구 오류는 구현을 막지 않는다
        print(f"[Lizard 훅] 검사를 실행하지 못했다: {proc.stderr.strip()[:300]}", file=sys.stderr)
        return 0

    report = (proc.stdout or "").strip()
    message = ("[Lizard 훅] 소스코드 메트릭 기준 위반 — 구현 단계에서 고쳐야 한다 "
               "(순환복잡도 10 이하, 함수 라인 80 이하).\n" + report +
               "\n함수를 더 작은 함수로 나눠서(단일 책임) 다시 검사를 통과시키세요.")
    if data.get("stop_hook_active"):
        print(json.dumps({"systemMessage": message}))
        return 0
    print(message, file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
