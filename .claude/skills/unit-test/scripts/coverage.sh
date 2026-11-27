#!/usr/bin/env bash
# LLVM source-based coverage (line / branch / region, optionally MC/DC) for a CMake + Ninja project.
#
# Usage: coverage.sh [--mcdc] [--build-dir DIR] [--line PCT] [--branch PCT] [--function PCT]
#                    [--mcdc-target PCT] [--ignore REGEX] [--label REGEX]
#   --mcdc            instrument for MC/DC (needs clang >= 18) and check MC/DC coverage
#   --build-dir DIR   coverage build directory (default: build-cov, kept apart from `build/`)
#   --line/--branch/--function   required percentage. A metric is only checked when given;
#                    with none given the script just measures and reports.
#   --mcdc-target     required MC/DC percentage when --mcdc is given (default 100)
#   --ignore REGEX    source files excluded from coverage (default: tests, third-party, build dirs)
#   --label REGEX     only run tests whose CTest label matches (e.g. "unit")
#
# Environment: LLVM_BIN=<dir> to use LLVM tools that are not on PATH.
# Exit code: 0 target met, 1 target missed, 2 setup/tool error.
set -euo pipefail

BUILD=build-cov; MCDC=0; LINE=""; BRANCH=""; FUNCTION=""; MCDC_TARGET=100; LABEL=""
IGNORE='(^|/)(tests?|test|third_party|_deps|build[^/]*|\.claude)/'
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

while [ $# -gt 0 ]; do
  case "$1" in
    --mcdc) MCDC=1 ;;
    --build-dir) BUILD="$2"; shift ;;
    --line) LINE="$2"; shift ;;
    --branch) BRANCH="$2"; shift ;;
    --function) FUNCTION="$2"; shift ;;
    --mcdc-target) MCDC_TARGET="$2"; shift ;;
    --ignore) IGNORE="$2"; shift ;;
    --label) LABEL="$2"; shift ;;
    -h|--help) sed -n '2,17p' "$0"; exit 0 ;;
    *) echo "unknown option: $1" >&2; exit 2 ;;
  esac
  shift
done

tool() { # resolve an LLVM tool, honoring LLVM_BIN
  if [ -n "${LLVM_BIN:-}" ] && [ -x "$LLVM_BIN/$1" ]; then echo "$LLVM_BIN/$1"
  elif [ -n "${LLVM_BIN:-}" ] && [ -x "$LLVM_BIN/$1.exe" ]; then echo "$LLVM_BIN/$1.exe"
  elif command -v "$1" >/dev/null 2>&1; then command -v "$1"
  else echo ""; fi
}
CLANG=$(tool clang); CLANGXX=$(tool clang++); PROFDATA=$(tool llvm-profdata); COV=$(tool llvm-cov)
PY=$(command -v python3 || command -v python || true)
CMAKE=$(command -v cmake || true); CTEST=$(command -v ctest || true)

missing=""
for pair in clang:$CLANG clang++:$CLANGXX llvm-profdata:$PROFDATA llvm-cov:$COV cmake:$CMAKE ctest:$CTEST python:$PY; do
  [ -z "${pair#*:}" ] && missing="$missing ${pair%%:*}"
done
if [ -n "$missing" ]; then
  echo "필요한 도구가 없다:$missing" >&2
  echo "설치: Windows 'winget install LLVM.LLVM Kitware.CMake Ninja-build.Ninja', Linux 'apt install clang llvm cmake ninja-build'" >&2
  echo "PATH에 없으면 LLVM_BIN=<LLVM bin 디렉터리>로 지정한다." >&2
  exit 2
fi

FLAGS="-O0 -g -fprofile-instr-generate -fcoverage-mapping"
if [ "$MCDC" = 1 ]; then
  ver=$("$CLANG" --version | sed -n 's/.*clang version \([0-9]*\).*/\1/p' | head -1)
  if [ -z "$ver" ] || [ "$ver" -lt 18 ]; then
    echo "MC/DC에는 clang 18 이상이 필요하다 (현재: ${ver:-알 수 없음})" >&2; exit 2
  fi
  FLAGS="$FLAGS -fcoverage-mcdc"
fi

echo "== 구성/빌드 ($BUILD) =="
"$CMAKE" -S . -B "$BUILD" -G Ninja -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_C_COMPILER="$CLANG" -DCMAKE_CXX_COMPILER="$CLANGXX" \
  -DCMAKE_C_FLAGS="$FLAGS" -DCMAKE_CXX_FLAGS="$FLAGS" \
  -DCMAKE_EXE_LINKER_FLAGS="-fprofile-instr-generate" -DCMAKE_EXPORT_COMPILE_COMMANDS=ON >/dev/null
"$CMAKE" --build "$BUILD"

echo "== 테스트 실행 =="
COVDIR="$BUILD/cov"; rm -rf "$COVDIR"; mkdir -p "$COVDIR"
ctest_args=(--test-dir "$BUILD" --output-on-failure)
[ -n "$LABEL" ] && ctest_args+=(-L "$LABEL")
LLVM_PROFILE_FILE="$PWD/$COVDIR/%p-%m.profraw" "$CTEST" "${ctest_args[@]}"

shopt -s nullglob; raw=("$COVDIR"/*.profraw); shopt -u nullglob
[ ${#raw[@]} -gt 0 ] || { echo "프로파일 데이터가 없다. 테스트가 실행되지 않았다." >&2; exit 2; }
"$PROFDATA" merge -sparse "${raw[@]}" -o "$COVDIR/all.profdata"

# Instrumented binaries = every executable that CTest runs
mapfile -t OBJS < <("$CTEST" --test-dir "$BUILD" --show-only=json-v1 ${LABEL:+-L "$LABEL"} |
  "$PY" -I -c '
import json, sys
seen = []
for t in json.load(sys.stdin).get("tests", []):
    cmd = t.get("command") or []
    if cmd and cmd[0] not in seen:
        seen.append(cmd[0])
print("\n".join(seen))')
[ ${#OBJS[@]} -gt 0 ] || { echo "CTest에 등록된 테스트 실행 파일이 없다." >&2; exit 2; }
obj_args=("${OBJS[0]}"); for o in "${OBJS[@]:1}"; do obj_args+=(-object "$o"); done

common=(-instr-profile="$COVDIR/all.profdata" --ignore-filename-regex="$IGNORE")

echo "== 커버리지 요약 =="
report_args=("${common[@]}")
[ "$MCDC" = 1 ] && report_args+=(-show-mcdc-summary)
"$COV" report "${obj_args[@]}" "${report_args[@]}"

"$COV" export "${obj_args[@]}" "${common[@]}" -summary-only >"$COVDIR/summary.json"
"$COV" export "${obj_args[@]}" "${common[@]}" -format=lcov >"$COVDIR/coverage.lcov"
show_args=("${common[@]}" -show-branches=count)
[ "$MCDC" = 1 ] && show_args+=(--show-mcdc)
"$COV" show "${obj_args[@]}" "${show_args[@]}" >"$COVDIR/detail.txt" 2>&1 || true

echo "== 목표 대비 =="
set +e
"$PY" -I "$HERE/cov_gaps.py" --summary "$COVDIR/summary.json" --lcov "$COVDIR/coverage.lcov" \
  ${LINE:+--line "$LINE"} ${BRANCH:+--branch "$BRANCH"} ${FUNCTION:+--function "$FUNCTION"}   $([ "$MCDC" = 1 ] && echo "--mcdc $MCDC_TARGET")
rc=$?
set -e
echo "상세(분기/MC·DC 조건별): $COVDIR/detail.txt"
exit $rc
