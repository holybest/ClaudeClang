#!/usr/bin/env bash
# 추적성 게이트: 요구사항 ↔ 이후 산출물 양방향 추적성 (check_traceability.py --until test).
# 요구사항 문서가 아직 없는 저장소 초기 상태만 N/A 로 처리한다.
source "$(dirname "$0")/common.sh"

ls docs/requirements/*.md >/dev/null 2>&1 || not_applicable "추적성 검사 (docs/requirements/)"
python3 -I .claude/skills/requirements-analysis/scripts/check_traceability.py --until test \
  | tee "$REPORTS/traceability.txt"
