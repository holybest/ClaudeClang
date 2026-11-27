---
name: lint
description: 변경된 C/C++ 파일에 clang-format과 clang-tidy를 실행한다. "포맷", "린트", "lint", 커밋 전 정리 요청 시 사용한다.
---

# 포맷 & 린트

1. 대상 파일을 정한다. 인자가 없으면 git에서 변경·추가된 C/C++ 파일을 쓴다:
   ```sh
   git diff --name-only --diff-filter=ACMR HEAD -- '*.c' '*.cc' '*.cpp' '*.cxx' '*.h' '*.hpp'
   git ls-files --others --exclude-standard -- '*.c' '*.cc' '*.cpp' '*.cxx' '*.h' '*.hpp'
   ```
   대상이 없으면 그렇게 보고하고 끝낸다.
2. 포맷: `clang-format -i <files>`. `.clang-format`이 없으면 적용 전에 사용자에게 알린다 (기본 스타일 LLVM).
3. 정적 분석: `build/compile_commands.json`이 있으면 `clang-tidy -p build <소스 파일>`을 실행한다. 없으면 `/build`로 먼저 설정하라고 안내한다.
4. clang-tidy 경고를 심각도별로 묶어 `파일:줄`과 함께 보고한다. 자동 수정(`--fix`)은 사용자가 요청할 때만 적용한다.
