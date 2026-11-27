---
name: build
description: CMake + Ninja + Clang으로 프로젝트를 설정하고 빌드한다. "빌드해줘", "컴파일", "build" 요청이나 코드 변경 후 컴파일 확인이 필요할 때 사용한다.
---

# 빌드

1. 루트에 `CMakeLists.txt`가 없으면 빌드하지 말고 그 사실을 알린다. 필요하면 최소 CMakeLists.txt를 만들지 사용자에게 제안한다.
2. `build/build.ninja`가 없거나 `CMakeLists.txt`가 그보다 최신이면 설정 단계를 실행한다:
   ```sh
   cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=${BUILD_TYPE:-Debug} \
     -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ \
     -DCMAKE_EXPORT_COMPILE_COMMANDS=ON
   ```
   인자로 `release`가 오면 `BUILD_TYPE=Release`를 쓴다.
3. 빌드한다: `cmake --build build`
4. 결과를 보고한다:
   - 성공: 생성된 타깃과 새로 생긴 경고 수
   - 실패: 첫 번째 에러부터 `파일:줄` 형식으로 요약. 에러가 많거나 원인이 불분명하면 `build-fixer` 서브에이전트에 넘긴다.
