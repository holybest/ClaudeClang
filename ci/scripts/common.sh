#!/usr/bin/env bash
# CI 스크립트 공통 설정. 각 스크립트가 `source "$(dirname "$0")/common.sh"` 로 읽는다.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT"
BUILD="${BUILD_DIR:-build}"
REPORTS="$BUILD/reports"
mkdir -p "$REPORTS"

# 품질 기준 (CLAUDE.md 2절). 한 곳에서만 정의한다.
CCN_MAX=10
FUNC_LINES_MAX=80
COMMENT_RATIO_MIN=20   # %

# 품질 기준의 대상 소스: src/, include/ (테스트 코드는 제외)
list_sources() {
  find src include -type f \( -name '*.c' -o -name '*.cc' -o -name '*.cpp' -o -name '*.cxx' \
       -o -name '*.h' -o -name '*.hpp' \) 2>/dev/null | sort || true
}

# 대상이 없으면 통과하되 "대상 없음"을 분명히 남긴다 (조용히 통과시키지 않는다).
not_applicable() { echo "[N/A] $1 — 대상 없음 (게이트는 대상이 생기면 자동으로 적용된다)"; exit 0; }
