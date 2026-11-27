#!/usr/bin/env bash
# 빌드 게이트: 경고 없이 빌드에 성공해야 한다 (경고는 오류로 취급한다).
source "$(dirname "$0")/common.sh"

[ -f CMakeLists.txt ] || { echo "CMakeLists.txt 가 없다" >&2; exit 1; }

cmake -S . -B "$BUILD" -G Ninja -DCMAKE_BUILD_TYPE="${BUILD_TYPE:-Debug}" \
  -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ \
  -DCMAKE_COMPILE_WARNING_AS_ERROR=ON \
  -DCMAKE_C_COMPILER_LAUNCHER=ccache -DCMAKE_CXX_COMPILER_LAUNCHER=ccache \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
cmake --build "$BUILD"
echo "[OK] 빌드 성공 (경고 없음)"
