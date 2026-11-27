---
name: build
description: CMake + Ninja + Clang으로 프로젝트를 빌드한다. 개발과 CI가 같은 claudeclangbuild 컨테이너와 같은 스크립트를 쓴다. "빌드해줘", "컴파일", "build" 요청이나 코드 변경 후 컴파일 확인이 필요할 때 사용한다.
---

# 빌드

개발 빌드와 CI 빌드는 **같은 이미지(`claudeclangbuild`)와 같은 스크립트(`ci/scripts/build.sh`)**를 쓴다. 로컬에 clang/cmake를 설치하지 않아도 된다.

1. 루트에 `CMakeLists.txt`가 없으면 빌드하지 말고 그 사실을 알린다.
2. 이미지가 없으면 만든다 (`docker images claudeclangbuild`로 확인):
   ```sh
   docker build -t claudeclangbuild -f docker/Dockerfile .
   ```
3. 컨테이너에서 빌드한다:
   ```sh
   bash docker/run.sh bash ci/scripts/build.sh
   ```
   - 설정(Ninja, Clang, `compile_commands.json`)과 빌드를 함께 수행하고, **경고는 오류로 취급**한다(CI 기준 "경고 없음").
   - Release 빌드가 필요하면 `BUILD_TYPE=Release`를 컨테이너 안 환경으로 넘긴다: `bash docker/run.sh env BUILD_TYPE=Release bash ci/scripts/build.sh`
4. 결과를 보고한다:
   - 성공: 생성된 타깃
   - 실패: 첫 번째 에러부터 `파일:줄` 형식으로 요약. 에러가 많거나 원인이 불분명하면 `build-fixer` 서브에이전트에 넘긴다. **경고 억제(`-Wno-*`, `#pragma`)로 해결하지 않는다.**

도커를 쓸 수 없는 환경에서만 로컬 `cmake`/`clang`으로 같은 명령(`bash ci/scripts/build.sh`)을 직접 실행하고, 그 사실을 보고에 적는다(CI와 결과가 다를 수 있다).
