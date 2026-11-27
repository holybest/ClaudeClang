#!/usr/bin/env bash
# 정적 분석 게이트: Cppcheck 지적 0건. 예외 처리(억제)는 허용하지 않는다.
source "$(dirname "$0")/common.sh"

if ! list_sources | grep -q .; then
  echo '<?xml version="1.0" encoding="UTF-8"?><results version="2"><cppcheck version="n/a"/><errors/></results>' > "$REPORTS/cppcheck.xml"
  not_applicable "Cppcheck"
fi
[ -f "$BUILD/compile_commands.json" ] || { echo "먼저 build.sh 를 실행해야 한다" >&2; exit 2; }

# 1) 억제 금지: 소스, 빌드 설정, 억제 파일 어디에도 억제 수단이 없어야 한다.
if grep -rnE 'cppcheck-suppress|--suppress|--inline-suppr|suppressions-list' \
     src include tests CMakeLists.txt cmake 2>/dev/null; then
  echo "[FAIL] Cppcheck 억제가 발견됨 — 예외 처리는 허용되지 않는다" >&2
  exit 1
fi
if ls .cppcheck* >/dev/null 2>&1; then
  echo "[FAIL] Cppcheck 설정/억제 파일(.cppcheck*)은 허용되지 않는다" >&2
  exit 1
fi

# 2) 분석 + 판정 (분석 실패는 통과로 처리하지 않는다)
python3 ci/scripts/cppcheck_gate.py --compile-db "$BUILD/compile_commands.json" \
        --xml "$REPORTS/cppcheck.xml"
