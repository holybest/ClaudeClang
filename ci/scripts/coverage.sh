#!/usr/bin/env bash
# 커버리지 게이트 (LLVM). 라벨마다 목표가 다르고, 결과도 라벨별로 분리한다.
#   unit        MC/DC 100 % + 분기 100 %   (tests/unit 만으로 판정, TDD 테스트는 합산하지 않는다)
#               LLVM 의 MC/DC 는 조건 2개 이상인 결정식만 세므로 분기 커버리지를 함께 건다.
#   integration 함수 커버리지 100 %
#   tdd         측정·보고만 (목표 미정)
source "$(dirname "$0")/common.sh"

label="${1:?usage: coverage.sh <tdd|unit|integration>}"
total=$(ctest --test-dir "$BUILD" -N -L "^${label}\$" | sed -n 's/^Total Tests: *//p')
[ "${total:-0}" -gt 0 ] || not_applicable "$label 커버리지"
list_sources | grep -q . || not_applicable "$label 커버리지 (측정 대상 소스)"

case "$label" in
  unit)        opts=(--mcdc --mcdc-target 100 --branch 100) ;;
  integration) opts=(--function 100) ;;
  tdd)         opts=() ;;
  *) echo "알 수 없는 라벨: $label" >&2; exit 2 ;;
esac

out="$REPORTS/coverage/$label"; mkdir -p "$out"
rc=0
bash .claude/skills/unit-test/scripts/coverage.sh --label "^${label}\$" \
     --build-dir "build-cov-$label" "${opts[@]}" || rc=$?

# 리포트를 보존하고 Jenkins Coverage 플러그인이 읽는 Cobertura XML로 변환한다.
cov="build-cov-$label/cov"
cp -f "$cov"/summary.json "$cov"/coverage.lcov "$cov"/detail.txt "$out"/ 2>/dev/null || true
[ -f "$out/coverage.lcov" ] && lcov_cobertura "$out/coverage.lcov" --base-dir "$ROOT" \
     --output "$out/cobertura.xml" >/dev/null || true
exit $rc
