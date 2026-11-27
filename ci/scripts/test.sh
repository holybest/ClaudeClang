#!/usr/bin/env bash
# 테스트 게이트: 라벨(tdd | unit | integration)별로 실행하고 성공률 100 %를 요구한다.
# 결과는 라벨별로 분리된 JUnit XML(build/reports/<라벨>/junit.xml)로 낸다.
source "$(dirname "$0")/common.sh"

label="${1:?usage: test.sh <tdd|unit|integration>}"
case "$label" in tdd|unit|integration) ;; *) echo "알 수 없는 라벨: $label" >&2; exit 2 ;; esac

total=$(ctest --test-dir "$BUILD" -N -L "^${label}\$" | sed -n 's/^Total Tests: *//p')
[ "${total:-0}" -gt 0 ] || not_applicable "$label 테스트"

mkdir -p "$REPORTS/$label"
# ctest 는 실패가 하나라도 있으면 0이 아닌 값으로 끝난다 = 성공률 100 % 가 아니면 실패
ctest --test-dir "$BUILD" -L "^${label}\$" --output-on-failure \
      --output-junit "$ROOT/$REPORTS/$label/junit.xml"
echo "[OK] $label 테스트 $total 건 모두 성공 (성공률 100 %)"
