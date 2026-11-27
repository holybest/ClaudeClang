cmake_minimum_required(VERSION 3.25)
project(ClaudeClang LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

add_compile_options(-Wall -Wextra -Wpedantic)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_SOURCE_DIR}/cmake")
include(CTest)
include(ClaudeTesting)

# 제품 코드: src/CMakeLists.txt 가 있으면 추가한다.
if(EXISTS "${CMAKE_SOURCE_DIR}/src/CMakeLists.txt")
  add_subdirectory(src)
endif()

# 테스트 4종은 폴더·CTest 라벨·결과를 서로 분리한다 (CLAUDE.md 1.5, 2.1).
foreach(kind tdd unit integration)
  if(EXISTS "${CMAKE_SOURCE_DIR}/tests/${kind}/CMakeLists.txt")
    add_subdirectory(tests/${kind})
  endif()
endforeach()
