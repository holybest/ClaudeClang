#!/usr/bin/env bash
# 이미지에 들어 있는 도구와 버전을 한눈에 출력한다. (docker run --rm claudeclangbuild print-tools)
set -u
row() { printf '%-16s %s\n' "$1" "$2"; }
row clang        "$(clang --version | head -1)"
row llvm-cov     "$(llvm-cov --version | grep -m1 -i 'version')"
row llvm-profdata "$(llvm-profdata --version | grep -m1 -i 'version')"
row clang-format "$(clang-format --version)"
row clang-tidy   "$(clang-tidy --version | grep -m1 -i 'version')"
row cmake        "$(cmake --version | head -1)"
row ninja        "ninja $(ninja --version)"
row gtest/gmock  "$(dpkg-query -W -f='${Version}' libgtest-dev) / $(dpkg-query -W -f='${Version}' libgmock-dev)"
row cppcheck     "$(cppcheck --version)"
row lizard       "lizard $(lizard --version)"
row cloc         "cloc $(cloc --version)"
row pict         "$(pict 2>&1 | head -1)"
row doxygen      "doxygen $(doxygen --version)"
row ccache       "$(ccache --version | head -1)"
row python       "$(python3 --version)"
