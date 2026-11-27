---
name: lint
description: 변경된 C/C++ 파일에 clang-format, clang-tidy, Cppcheck, Lizard(순환복잡도·함수 라인), 주석률, HITL 주석 검사를 CI와 같은 방식으로 실행한다. "포맷", "린트", "lint", "정적 분석", 커밋 전 정리 요청 시 사용한다.
---

# 포맷 · 정적 분석 · 메트릭

CI의 소스코드 품질 기준(CLAUDE.md 2절)을 **커밋 전에 미리** 확인한다. 모두 `claudeclangbuild` 컨테이너에서 CI와 같은 스크립트로 실행한다. 결과는 CI와 같아야 하므로 기준을 완화하지 않는다.

1. 대상 파일을 정한다. 인자가 없으면 git에서 변경·추가된 C/C++ 파일을 쓴다:
   ```sh
   git diff --name-only --diff-filter=ACMR HEAD -- '*.c' '*.cc' '*.cpp' '*.cxx' '*.h' '*.hpp'
   git ls-files --others --exclude-standard -- '*.c' '*.cc' '*.cpp' '*.cxx' '*.h' '*.hpp'
   ```
   대상이 없으면 그렇게 보고하고 끝낸다.
2. **포맷**: `bash docker/run.sh clang-format -i <files>` (`.clang-format` 사용).
3. **clang-tidy**: 먼저 `/build`로 `build/compile_commands.json`을 만든 뒤 `bash docker/run.sh clang-tidy -p build <소스 파일>`.
4. **Cppcheck (지적 0건, 예외 없음)**: `bash docker/run.sh bash ci/scripts/cppcheck.sh`
   - `cppcheck-suppress`, `--suppress`, `.cppcheck*` 파일은 허용되지 않는다. 지적은 억제하지 말고 코드를 고친다.
   - 분석이 정상 종료되지 않으면 통과가 아니라 실패다.
5. **Lizard (순환복잡도 ≤ 10, 함수 라인 ≤ 80)**: `bash docker/run.sh python3 ci/scripts/lizard_gate.py`
6. **주석률 (≥ 20 %)**: `bash docker/run.sh python3 ci/scripts/comment_ratio.py`
7. **HITL 주석**: `bash docker/run.sh python3 ci/scripts/hitl_check.py` — 모든 소스·헤더의 `@file` 블록에 AI 작성 이력과 사용자 리뷰 항목이 있는지 확인한다.
8. 결과를 항목별로(`파일:줄`, 심각도) 보고한다. 자동 수정(`clang-tidy --fix`)은 사용자가 요청할 때만 적용한다.
   - 메트릭 위반은 함수를 작은 함수로 나눠서(단일 책임) 해결한다.
   - 보고할 때 **HITL의 `사용자 리뷰` 상태를 AI가 `완료`로 바꾸지 않는다.**

참고: 구현이 끝났을 때 Stop 훅(`check_lizard.py`)이 6번 중 Lizard 검사를 자동으로 수행한다. 이 스킬은 나머지 항목까지 한꺼번에 확인하는 용도다.
