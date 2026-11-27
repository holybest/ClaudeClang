#!/usr/bin/env bash
# 모든 게이트를 순서대로 실행하고, 하나라도 실패하면 마지막에 실패로 끝낸다.
# Jenkins 와 같은 검사를 컨테이너 안에서 로컬로 돌릴 때 쓴다.
#   docker/run.sh bash ci/scripts/run_all.sh
cd "$(dirname "$0")/../.."
fail=()
run() { echo; echo "================ $1 ================"; shift; "$@" || fail+=("$1"); }

if bash ci/scripts/build.sh; then
  for label in tdd unit integration; do run "테스트($label)" bash ci/scripts/test.sh "$label"; done
  for label in tdd unit integration; do run "커버리지($label)" bash ci/scripts/coverage.sh "$label"; done
  run "Cppcheck"        bash ci/scripts/cppcheck.sh
else
  fail+=("빌드")
fi
run "Lizard"            python3 ci/scripts/lizard_gate.py --issues build/reports/lizard-issues.json
run "주석률(CLOC)"      python3 ci/scripts/comment_ratio.py --json build/reports/comment-ratio.json
run "HITL 주석"         python3 ci/scripts/hitl_check.py --issues build/reports/hitl-issues.json
run "시스템 테스트"      python3 ci/scripts/system_test_gate.py --issues build/reports/system-test-issues.json
run "추적성"            bash ci/scripts/traceability.sh

echo; echo "================ 결과 ================"
if [ ${#fail[@]} -eq 0 ]; then echo "모든 게이트 통과"; exit 0; fi
printf '실패: %s\n' "${fail[@]}"; exit 1
