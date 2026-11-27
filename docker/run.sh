#!/usr/bin/env bash
# 개발용: 현재 저장소를 ClaudeCLangBuild 컨테이너에 마운트해서 명령을 실행한다.
# CI(Jenkins)와 같은 이미지를 쓰므로 로컬에 도구를 설치하지 않아도 된다.
#
#   docker/run.sh                                  # 대화형 셸
#   docker/run.sh cmake --build build               # 한 번 실행
#   docker/run.sh bash ci/scripts/run_all.sh        # CI 게이트 전체
set -euo pipefail
cd "$(dirname "$0")/.."
here="$(pwd -W 2>/dev/null || pwd)"   # Git Bash 에서는 Windows 경로, 그 외에는 일반 경로

tty=()
[ -t 0 ] && [ -t 1 ] && tty=(-it)

MSYS_NO_PATHCONV=1 docker run --rm "${tty[@]}" \
  -v "${here}:/work" -v claudeclang-ccache:/ccache -w /work \
  claudeclangbuild "${@:-bash}"
