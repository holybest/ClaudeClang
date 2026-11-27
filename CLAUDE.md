# ClaudeClang

Clang 툴체인과 CMake를 사용하는 C/C++ 프로젝트입니다. 개발은 A-SPICE를 기준으로 하고, 개발 환경과 CI는 같은 Docker 이미지를 씁니다.

## 1. 개발 절차

### 1.1 기본 원칙
- 개발은 **A-SPICE**를 기준으로 한다.
- 개발은 기본적으로 **메인 에이전트**가 수행하고, 각 단계에 맞는 **스킬**을 사용한다.
- 생명주기는 **애자일**이다. 아래 7개 단계를 **하나의 이터레이션**으로 수행한다.

### 1.2 이터레이션 단계

| # | 단계 | 사용 스킬 | 산출물 위치 |
|---|------|-----------|-------------|
| 1 | 분석 | `/requirements-analysis` | `docs/requirements/`, 안전 요구사항은 `docs/safety/` |
| 2 | 아키텍처 설계 | `/architecture-design` | `docs/architecture/` |
| 3 | 상세 설계 | `/detailed-design` | `docs/design/` |
| 4 | 구현 | `/test-driven-development` + `/implementation` | `src/`, `include/`, TDD 테스트는 `tests/tdd/` |
| 5 | 단위 테스트 | `/unit-test` | `tests/unit/` |
| 6 | 통합 테스트 | `/integration-test` | `tests/integration/` |
| 7 | 시스템 테스트 | `/sw-system-test-case` | `tests/system/` (`*.json` 원본, `*.xlsx` 생성물, `results.csv` 실행 결과) |
| — | 리뷰 | `/review` (수행: `reviewer` 서브에이전트) | `docs/reviews/` |

### 1.3 단계 게이트
- 각 단계가 끝나면 `reviewer` 서브에이전트가 그 단계의 산출물을 리뷰한다.
- **부적합 사항(Minor 포함)을 모두 조치하고 재리뷰에서 승인**받아야 다음 단계로 진행한다. 승인 기준은 Fail·미확인 0건이다.

### 1.4 이터레이션 종료와 PR
1. 이터레이션의 7개 단계가 모두 승인되면, **사용자에게 결과를 보고하고 확인을 받는다.**
2. 사용자 확인 후에만 PR 절차(3절)를 진행한다. 확인 전에는 PR을 만들지 않는다.

### 1.5 구현은 TDD로 한다
- 구현 단계는 `test-driven-development` 스킬로 한다 (실패하는 테스트 → 최소 구현 → 리팩터링).
- **TDD 테스트는 단위 테스트와 분리한다.**
  - 코드: `tests/tdd/` (단위 테스트는 `tests/unit/`). CTest 라벨은 `tdd` (단위는 `unit`, 통합은 `integration`).
  - 결과: 단위 테스트와 별도의 결과 파일로 낸다 (`build/reports/tdd/`).
  - 커버리지: 별도로 측정한다 (`bash ci/scripts/coverage.sh tdd` → `build/reports/coverage/tdd/`). TDD 커버리지의 목표 수치는 **미정**이며, 지금은 측정·보고만 한다.
  - 단위 테스트의 MC/DC·분기 100 % 달성 여부는 TDD 테스트를 합산하지 않고 `tests/unit/` 테스트만으로 판정한다.

## 2. 소스코드 품질 기준

CI는 아래 기준을 모두 만족해야 통과한다.

### 2.1 테스트 커버리지

| 테스트 | 커버리지 | 성공률 |
|--------|----------|--------|
| 시스템 | **요구사항 커버리지 100 %** (모든 `SWR`이 시스템 테스트 케이스에 연결) | **100 %** |
| 통합 | **함수 커버리지 100 %** | **100 %** |
| 단위 | **MC/DC 커버리지 100 %** + **분기 커버리지 100 %** | **100 %** |

- 측정: 코드 커버리지는 LLVM(`llvm-cov`), MC/DC는 `-fcoverage-mcdc`. 스크립트는 `.claude/skills/unit-test/scripts/coverage.sh`(`--mcdc-target`, `--function`, `--line`, `--branch` — **지정한 항목만 판정**)이고, CI는 라벨별 래퍼 `ci/scripts/coverage.sh <unit|integration|tdd>`가 위 목표를 적용한다. 시스템 테스트는 `ci/scripts/system_test_gate.py`가 판정한다(아래).
- 의미 없는 테스트로 수치만 채우지 않는다 (`/unit-test`, `/integration-test` 규칙).
- **단위 게이트는 MC/DC와 분기 커버리지를 함께 건다.** LLVM의 MC/DC는 조건이 2개 이상인 결정식만 계산하므로, MC/DC만으로는 단일 조건 `if`나 한 번도 실행되지 않은 함수를 잡지 못한다 (실측: `if` 12개를 가진 함수가 한 번도 실행되지 않았는데도 MC/DC 100 %). MC/DC는 이론상 분기(결정) 커버리지를 포함하므로 의도와 모순되지 않는다.
- **시스템 테스트 게이트** `ci/scripts/system_test_gate.py`: `tests/system/*.json`(`/sw-system-test-case` 입력 데이터가 원본, Excel은 생성물)을 스킬의 검증으로 통과시키고, `docs/requirements/`의 모든 `SWR`이 제안이 아닌 케이스로 커버되는지(요구사항 커버리지 100 %), `tests/system/results.csv`(열: `test_case_id,result,executed_at,executor`, `PASS`/`FAIL`, 같은 ID는 마지막 행이 최신)에서 모든 케이스가 최신 `PASS`인지(성공률 100 %, 미실행은 실패) 판정한다.

### 2.2 정적 분석
- **Cppcheck 규칙 대상 100 % 만족.** 지적 0건이어야 한다.
- **예외 처리는 없다.** `--suppress`, `// cppcheck-suppress`, 억제 파일을 쓰지 않는다.
- 실행: `bash ci/scripts/cppcheck.sh` (`--enable=all --inconclusive --check-level=exhaustive`). 억제 문구(`cppcheck-suppress`, `--suppress` 등)나 `.cppcheck*` 파일이 있으면 실패한다. **분석이 정상 종료되지 않으면 통과가 아니라 실패**로 처리한다.
- 모든 소스(테스트 포함)를 분석하되, **판정 대상은 `src/`, `include/`에서 나온 지적**이다 (라이브러리 함수가 테스트에서만 호출될 때 `unusedFunction` 오탐을 막기 위함).

### 2.3 소스코드 메트릭 (Lizard)
- **순환복잡도(CCN) 10 이하, 함수 라인 수 80 이하**: `lizard -C 10 -L 80 -w src include`
- **구현이 끝났을 때 Claude Code 훅으로 검사한다.** Stop 훅 `.claude/hooks/check_lizard.py`가 응답이 끝날 때 git에서 변경·추가된 `src/`·`include/` 파일을 검사하고, 위반이면 응답 종료를 막고 위반 내용을 돌려보내 구현 단계에서 고치게 한다 (한 번 돌려보낸 뒤에도 위반이면 무한 반복을 막기 위해 경고만 남기고 CI가 최종 판정). 호스트에 Lizard가 없으면 `claudeclangbuild` 이미지에서 실행한다.
- 같은 검사를 CI에서도 한다 (`ci/scripts/lizard_gate.py`, 훅과 같은 코드).

### 2.4 주석
- 주석은 **Doxygen** 형식으로 쓴다.
- 모든 소스·헤더 파일의 `@file` 주석에 아래 **Human-in-the-Loop 항목**을 반드시 넣는다. 이 항목도 Doxygen 형식을 따른다.
  - 어느 **AI 모델**이, **언제**, **누가 요청**해서 작성했는가
  - **사용자의 리뷰가 완료된 코드**인가. 완료했다면 **언제, 누가** 했는가

```cpp
/**
 * @file    buffer.cpp
 * @brief   링 버퍼 구현
 * @design  DD-004
 *
 * @par AI 작성 이력
 *   - 모델:   Claude Sonnet 5.5 (claude-sonnet-5-5)
 *   - 일시:   2026-11-27
 *   - 요청자: <git user.name>
 * @par 사용자 리뷰
 *   - 상태:   미완료          // 미완료 | 완료
 *   - 일시:   -               // 완료 시 YYYY-MM-DD
 *   - 리뷰어: -               // 완료 시 사용자 이름
 */
```
- 다른 모델이나 다른 시점에 파일이 수정되면 `AI 작성 이력`에 항목을 **추가**한다 (지우지 않는다). 내용이 바뀐 파일은 `사용자 리뷰`를 다시 `미완료`로 돌린다.
- **AI는 `사용자 리뷰`를 스스로 `완료`로 바꾸지 않는다.** 사용자가 리뷰했다고 확인해 준 뒤에만, 사용자가 말한 이름과 일시로 기록한다.
- **주석률은 20 % 이상**이어야 한다. CLOC으로 측정하며, 주석률 = 주석 줄 ÷ (코드 줄 + 주석 줄)이다. 대상은 `src/`, `include/`이다.

## 3. Git 브랜치 및 PR 전략

### 3.1 브랜치: Gitflow
- `main`: 릴리스된 코드만. 직접 커밋하지 않는다.
- `develop`: 통합 브랜치. 이터레이션 결과가 모인다.
- `feature/<이터레이션>-<주제>`: `develop`에서 분기, 이터레이션 작업 단위. 완료 후 `develop`으로 PR.
- `release/<버전>`: `develop`에서 분기해 릴리스 준비, `main`과 `develop`에 병합 후 태그.
- `hotfix/<버전>`: `main`에서 분기해 긴급 수정, `main`과 `develop`에 병합.

### 3.2 PR과 CI
- PR은 이터레이션 종료 후 **사용자 확인을 받은 다음**에 만든다 (1.4절).
- PR은 **CI를 통과해야만** 완료(병합)한다. CI가 실패하면 고쳐서 다시 통과시킨다.
- CI 통과 조건은 **빌드 성공 + 2절 소스코드 품질 기준 전부**이다:
  1. 빌드 성공 (경고 없음)
  2. 단위 테스트 성공률 100 %, MC/DC 100 %, 분기 100 %
  3. 통합 테스트 성공률 100 %, 함수 커버리지 100 %
  4. 시스템 테스트 성공률 100 %, 요구사항 커버리지 100 % (`ci/scripts/system_test_gate.py`), 양방향 추적성 (`check_traceability.py --until test`)
  5. Cppcheck 지적 0건
  6. Lizard CCN ≤ 10, 함수 라인 ≤ 80
  7. 모든 소스 파일에 Doxygen HITL 주석 존재, CLOC 주석률 20 % 이상

## 4. 개발 환경

| 용도 | 도구 | 비고 |
|------|------|------|
| 언어/컴파일러 | **C++20, Clang 18 이상** | 이미지에 **Clang 23.1.6**(2026-11 기준 최신)을 고정했다. 바꾸려면 `--build-arg LLVM_VERSION=<메이저>`. MC/DC에는 18 이상 필요. |
| 빌드 | **CMake + Ninja** (추천) | `compile_commands.json`, CTest, GoogleTest, Cppcheck, Jenkins와 연동이 표준적이다. |
| 정적 분석 | **Cppcheck** | 2.2절 |
| 테스트 프레임워크 | **GoogleTest / GoogleMock** 1.14 | 이미지에 설치. `cmake/ClaudeTesting.cmake`의 `cc_add_test(<tdd\|unit\|integration> ...)`로 등록 |
| 커버리지 | **LLVM** (`llvm-profdata`, `llvm-cov`) | MC/DC까지 측정 |
| 순환복잡도/함수 라인 | **Lizard** | 2.3절 |
| 주석률 | **CLOC** | 2.4절 |
| 조합 테스트 | **PICT** | `/unit-test`, `/integration-test` |
| 포맷/린트 | `clang-format`, `clang-tidy` | `.clang-format`은 있음 |
| 추천 추가 도구 | **ccache**(빌드 속도), **Doxygen**(주석 검증, `-Wdocumentation`), **Python 3**(검사 스크립트) | |

### 4.1 Docker 이미지: ClaudeCLangBuild
- **개발 빌드와 CI 빌드 모두 같은 이미지를 쓴다.** 위 도구가 모두 들어 있다 (Ubuntu 24.04 기반). **구축 완료.**
- 이미지 이름은 **ClaudeCLangBuild**이다. 단, Docker 저장소 이름은 소문자만 허용하므로 실제 태그는 `claudeclangbuild`를 쓴다.
- 정의: `docker/Dockerfile` (PICT는 소스에서 빌드). 포함 도구 확인: `docker run --rm claudeclangbuild print-tools`
- 사용:
  ```sh
  docker build -t claudeclangbuild -f docker/Dockerfile .      # 이미지 (다시) 만들기
  bash docker/run.sh                                           # 컨테이너 셸 (현재 저장소를 /work 에 마운트)
  bash docker/run.sh cmake --build build                       # 한 번 실행
  bash docker/run.sh bash ci/scripts/run_all.sh                # CI 게이트 전체를 로컬에서
  ```

## 5. CI 환경 (Jenkins)
- **Jenkins 안정화(LTS) 2.580.3**을 이 PC의 Docker에서 실행한다. 포트는 **8080** (`http://localhost:8080`). **구축 완료.**
  - 기동/중지: `bash ci/jenkins/up.sh` / `bash ci/jenkins/up.sh down` (Jenkins 이미지는 `ci/jenkins/Dockerfile`, 플러그인은 `ci/jenkins/plugins.txt`, 설정은 `ci/jenkins/jenkins.yaml`(JCasC))
  - 로그인: 사용자 `admin`, 비밀번호는 저장소 밖 `~/.claudeclang/jenkins-admin-password` 파일 (git에 올라가지 않음)
  - 보안: 익명 접근 차단, 호스트 Docker 소켓을 공유하므로 **로컬 개발 PC 전용 구성**이다 (외부에 노출하지 않는다).
- **플러그인은 이미지에 설치해 두었다.** 결과는 플러그인에서 확인한다:
  - 테스트(TDD/단위/통합 JUnit): **JUnit** — `build/reports/<라벨>/junit.xml`
  - 정적 분석·메트릭: **Warnings Next Generation** — Cppcheck, Lizard(CCN/함수 라인), HITL 주석
  - 커버리지: **Coverage** — 라벨별(unit/integration/TDD) Cobertura. MC/DC는 Cobertura에 없으므로 보관된 `detail.txt`와 로그에서 확인한다.
  - 그 외: Pipeline, Git, GitHub Branch Source(멀티브랜치), Docker Pipeline, Configuration as Code, Job DSL
- 파이프라인은 저장소 루트 `Jenkinsfile`이며 모든 단계를 `claudeclangbuild` 이미지 안에서 실행한다. 게이트가 하나 실패해도 나머지를 끝까지 실행해 실패 항목을 한 번에 보여 주고, 최종 결과는 FAILURE가 된다. 게이트 스크립트는 `ci/scripts/`.
- 잡 `ClaudeClang`(GitHub 멀티브랜치)이 5분마다 `holybest/ClaudeClang`의 브랜치를 스캔한다. 브랜치가 GitHub에 푸시되어 있어야 빌드된다.
- 대상이 아직 없는 게이트(소스·테스트·요구사항이 없는 초기 상태)는 `[N/A] ... 대상 없음`으로 출력하며 통과한다. 대상이 생기면 자동으로 적용된다.
- Gitflow와 CI 통과 조건은 PR 병합 보호 규칙(GitHub의 브랜치 보호와 필수 상태 점검)으로 강제하는 것을 권장한다 — *미설정*

## 6. 프로세스 규칙 (A-SPICE)
- ID: `SWR-FUN|QUA|LIM|CON-nnn`(요구사항), `FSR-nnn`(기능 안전), `ARC-nnn`(컴포넌트), `IF-nnn`(인터페이스), `DD-nnn`(모듈), `UT-nnn`/`IT-nnn`(시험)
- 양방향 추적성: `docs/traceability/links.csv`(`parent_id,child_id`). 검사: `python -I .claude/skills/requirements-analysis/scripts/check_traceability.py --until <req|arch|design|code|test>`
- 품질 요구사항 기준: ISO/IEC 25010 (사용하는 판: **미정 — 확인 필요**)
- 상세 설계에서 인터페이스를 반드시 정의하는 모듈의 기준: 다른 모듈이 호출하는 공개 함수가 있거나, 컴포넌트 간 데이터를 주고받거나, 공개 함수가 3개를 넘거나 상태를 가진 모듈
- 커버리지 목표는 2.1절이 기준이다. 스킬은 이 값을 읽는다.

## 7. 코딩 규칙
- C++20, 경고는 `-Wall -Wextra -Wpedantic`로 켜고 새 경고를 만들지 않는다.
- 함수는 반환값(없으면 상태 코드)을 가지고 `return`은 마지막에 한 번만 둔다 (`/implementation`). 적용 범위는 `src/`, `include/`이며 테스트 코드는 제외한다.
- 소유권은 스마트 포인터(`std::unique_ptr` 우선)로 표현하고 raw `new`/`delete`는 쓰지 않는다.
- 커밋 전에 변경된 파일에 `clang-format`을 적용한다.
- 새 기능이나 버그 수정에는 테스트를 함께 추가한다.

## 8. 디렉터리 구조
- `CMakeLists.txt`, `cmake/ClaudeTesting.cmake` — 빌드 (있음). `src/CMakeLists.txt`와 `tests/<종류>/CMakeLists.txt`가 있으면 자동으로 추가된다.
- `src/`, `include/` — 소스, 공개 헤더 (예정)
- `tests/tdd/`, `tests/unit/`, `tests/integration/`, `tests/system/` — 테스트 (4종 분리, 예정)
- `docs/` — `requirements/`, `safety/`, `architecture/`, `design/`, `reviews/`, `traceability/`
- `docker/` — `Dockerfile`(ClaudeCLangBuild), `run.sh`, `print-tools.sh` (있음)
- `ci/scripts/` — CI 게이트 스크립트, `ci/jenkins/` — Jenkins 서버 구성, `Jenkinsfile` (있음)
- `build/`, `build-cov*/` — 빌드·커버리지 산출물 (git 무시)

## 9. Claude 구성 (`.claude/`)
- 스킬 (`.claude/skills/`):
  - 개발 도구: `/build`, `/test`, `/lint` — 모두 `claudeclangbuild` 이미지에서 CI와 같은 스크립트로 실행한다.
  - A-SPICE 단계: `requirements-analysis`, `architecture-design`, `detailed-design`, `implementation`, `unit-test`, `integration-test`, `review`
  - 외부 도입 2개 (수정하지 않고 사용, 프로젝트 규칙은 이 문서가 덧씌움): `test-driven-development`(obra/superpowers, MIT), `sw-system-test-case`
- 서브에이전트: `reviewer`(단계 게이트 리뷰), `cpp-reviewer`, `build-fixer`, `test-writer` — `.claude/agents/`
- 훅(Stop): `log_conversation.py`가 매 응답 후 `docs/conversation-log.md`에 프롬프트와 답변을 남긴다 (이 파일은 직접 고치지 않는다). `check_lizard.py`가 구현이 끝났을 때 변경된 소스의 CCN·함수 라인 수를 검사한다 (2.3절).
- 공유 설정: `.claude/settings.json` (개인 설정은 `.claude/settings.local.json`, git 무시)
