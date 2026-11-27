# ClaudeClang

Clang 툴체인과 CMake를 사용하는 C/C++ 프로젝트입니다.

## 환경
- OS: Windows 11 (Git Bash / PowerShell)
- 컴파일러: `clang` / `clang++`
- 빌드: CMake + Ninja, 빌드 디렉터리는 `build/` (git에 포함하지 않음)
- 포맷/린트: `clang-format` (`.clang-format`), `clang-tidy` (`.clang-tidy`)

## 자주 쓰는 명령
```sh
# 설정 (최초 1회 또는 CMakeLists.txt 변경 시)
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Debug \
  -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ \
  -DCMAKE_EXPORT_COMPILE_COMMANDS=ON

# 빌드
cmake --build build

# 테스트
ctest --test-dir build --output-on-failure

# 포맷 검사 / 적용
clang-format --dry-run --Werror <files>
clang-format -i <files>

# 정적 분석
clang-tidy -p build <files>
```

## 디렉터리 구조 (예정)
- `src/` — 소스 코드
- `include/` — 공개 헤더
- `tests/` — 테스트 코드
- `build/` — 빌드 산출물 (무시됨)

## 코딩 규칙
- C++20, 경고는 `-Wall -Wextra -Wpedantic`로 켜고 새 경고를 만들지 않는다.
- 소유권은 스마트 포인터(`std::unique_ptr` 우선)로 표현하고 raw `new`/`delete`는 쓰지 않는다.
- 커밋 전에 변경된 파일에 `clang-format`을 적용한다.
- 새 기능이나 버그 수정에는 테스트를 함께 추가한다.

## Claude 구성 (`.claude/`)
- 스킬: `/build`, `/test`, `/lint` — `.claude/skills/`
- 서브에이전트: `cpp-reviewer`, `build-fixer`, `test-writer` — `.claude/agents/`
- 대화 기록: Stop 훅(`.claude/hooks/log_conversation.py`)이 매 응답 후 `docs/conversation-log.md`에 프롬프트와 답변을 남긴다. 이 파일은 직접 고치지 않는다.
- 공유 설정: `.claude/settings.json` (개인 설정은 `.claude/settings.local.json`, git 무시)
