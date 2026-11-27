# 테스트 등록 도우미.
#
#   cc_add_test(<label> <name> SOURCES <files...> [LINK <targets...>])
#
# <label> : tdd | unit | integration   (CTest 라벨. 결과와 커버리지를 라벨별로 분리한다)
# 테스트 실행 파일은 GoogleTest/GoogleMock 에 링크되고, 케이스마다 CTest 항목으로 등록된다.
find_package(GTest REQUIRED)
include(GoogleTest)

function(cc_add_test label name)
  cmake_parse_arguments(ARG "" "" "SOURCES;LINK" ${ARGN})
  if(NOT label MATCHES "^(tdd|unit|integration)$")
    message(FATAL_ERROR "cc_add_test: label must be tdd, unit or integration (got '${label}')")
  endif()
  set(target "${label}_${name}")
  add_executable(${target} ${ARG_SOURCES})
  target_link_libraries(${target} PRIVATE GTest::gmock_main GTest::gtest ${ARG_LINK})
  gtest_discover_tests(${target}
    TEST_PREFIX "${label}."
    DISCOVERY_MODE PRE_TEST
    PROPERTIES LABELS "${label}")
endfunction()
