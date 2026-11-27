---
name: unit-test
description: A-SPICE(SWE.4 단위 검증) 기준으로 단위 테스트를 설계·작성하고 LLVM 커버리지(MC/DC 포함) 목표를 달성한다. 경계값 분석, 동치 클래스, PICT 조합 기법과 Doxygen 테스트 주석을 적용한다. "단위 테스트", "커버리지", "MC/DC", "unit test" 요청 시 사용한다.
---

# 단위 테스트 (A-SPICE SWE.4)

입력은 구현된 소스와 상세 설계(`docs/design/`)이다. 테스트는 **설계 명세(기대 동작)에서** 도출하고, 코드를 보고 현재 동작을 그대로 기록하지 않는다.
테스트는 `tests/unit/`에 두고 `cmake/ClaudeTesting.cmake`의 `cc_add_test(unit <이름> SOURCES ... LINK ...)`로 등록한다(CTest 라벨 `unit`). GoogleTest/GoogleMock은 `claudeclangbuild` 이미지에 설치되어 있다. **구현 단계의 TDD 테스트(`tests/tdd/`)와 섞지 않는다.** TDD 테스트와 별개로, 설계 명세에서 도출한 공식 단위 테스트를 이 단계에서 만든다.

## 1. 커버리지 목표

- 목표는 CLAUDE.md 2.1절을 따른다: 단위 테스트는 **MC/DC 100 %, 분기 100 %, 성공률 100 %**. 측정은 `tests/unit/`(라벨 `unit`) 테스트만으로 하고 TDD 테스트는 합산하지 않는다. 목표가 바뀌었거나 정의되어 있지 않으면 작업 전에 사용자에게 묻는다.
- MC/DC 목표가 있으면 4절의 MC/DC 절차를 적용한다.
- 목표를 **100 % 달성할 때까지** 측정 → 미커버 분석 → 케이스 추가를 반복한다. 반복마다 수치를 보고한다.
- 도달 불가능한 코드가 원인이면 테스트를 억지로 만들지 말고, 방어 코드 제거(설계/구현 수정)나 정당한 제외 사유를 사용자에게 보고하고 승인을 받는다.

## 2. 테스트 케이스 설계 (순서대로)

1. **동치 클래스 분할**: 입력마다 유효/무효 클래스를 나누고 클래스별 대표값 하나를 정한다.
2. **경계값 분석**: 각 경계의 `min-1, min, min+1, max-1, max, max+1`과 0, 빈 입력, null을 포함한다.
3. **PICT 조합**: 입력 파라미터가 둘 이상이고 상호작용이 있으면 PICT로 조합 케이스를 만든다.
   - 모델 예시는 `templates/pict-model.example.txt`. 값은 2단계에서 정한 대표값·경계값으로 채운다.
   - 실행: `pict model.txt /o:2 > cases.tsv` (기본 2-way, 위험도가 높은 모듈은 `/o:3`). PICT가 없으면 https://github.com/microsoft/pict 에서 설치한다. 불가능한 조합은 제약(`IF … THEN …`)으로 제외하고 사유를 적는다.
   - 생성된 각 행을 매개변수화 테스트(`TEST_P`)의 입력으로 쓰고, 행마다 기대값을 설계 명세에서 정한다.
4. **오류·상태 전이**: 모든 반환 상태 코드와 상태 전이를 최소 한 번씩 다룬다.
5. 설계 문서의 각 공개 함수와 요구사항(`SWR`) 수락 기준이 테스트로 연결되어야 한다.

## 3. 작성 규칙

- **의미 없는 테스트 금지**: 커버리지 수치만 올리고 검증은 하지 않는 테스트(단언 없음, 항상 참인 단언, 반환값 무시)를 추가하지 않는다. 모든 테스트는 설계 명세의 기대 동작을 단언으로 검증해야 한다.
- **Stub/Mock은 필요한 경우에만**: 실제 하드웨어·네트워크·시간·난수 등 제어할 수 없는 의존성이나 다른 모듈의 인터페이스(`IF`)를 격리할 때만 쓴다. 대상 모듈 내부 함수를 mock하지 않고, 실제 협력 객체를 쓸 수 있으면 실제 객체를 쓴다. 테스트가 mock 호출 순서 검증으로만 이루어지면 과의존이다.
- **Doxygen 주석 필수**: 모든 테스트 함수에 목적, 입력값, 절차, 예상 출력값을 적는다. 형식은 `templates/test_example.cpp`를 따른다.
  `@test`, `@brief`(목적 + 적용 기법), `@trace`(`UT-nnn -> DD-nnn (SWR-…)`), `@par 입력값`, `@par 절차`, `@par 예상 출력값`.
- 테스트는 독립적이고 결정적이어야 한다 (순서·시간·외부 상태 의존 금지). 이름은 `<대상>_<동작>_<조건>` 형태로 의도를 드러낸다.

## 4. 커버리지 측정과 MC/DC

측정은 이 스킬의 스크립트를 쓴다. (LLVM의 clang, llvm-profdata, llvm-cov와 cmake, ninja가 필요하다.)

```sh
# 단위 게이트(CLAUDE.md 2.1): MC/DC 100 % + 분기 100 % — clang 18 이상, tests/unit 만 측정
bash .claude/skills/unit-test/scripts/coverage.sh --label '^unit$' --mcdc --mcdc-target 100 --branch 100

# CI 와 같은 판정(라벨별 래퍼, 결과는 build/reports/coverage/unit/ 에 보존)
bash ci/scripts/coverage.sh unit

# 지정한 항목만 판정한다: --line, --branch, --function, --mcdc-target (지정하지 않은 항목은 측정만)
```
스크립트는 `build-cov/`에 계측 빌드를 만들고, CTest를 실행해 프로파일을 합친 뒤 요약, 목표 대비 결과, 미커버 라인·분기 위치를 출력한다. 목표 미달이면 종료 코드 1이다.
도구가 없으면 스크립트가 설치 방법을 안내한다. `LLVM_BIN=<경로>`로 LLVM 위치를 지정할 수 있다.

**MC/DC 케이스 추가 절차** (MC/DC 목표가 수립된 경우)
1. `--mcdc`로 측정하고 `build-cov/cov/detail.txt`의 `MC/DC Decision Region` 표를 읽는다. 각 조건(condition)에 대해 "그 조건만 바꿔서 결정(decision) 결과가 바뀌는 쌍(independence pair)"이 있어야 한다. 표에서 `C1-Pair: not covered`처럼 표시된 조건이 부족한 것이다.
2. 부족한 조건마다, 다른 조건은 고정하고 그 조건만 뒤집어 결정 결과가 달라지는 입력 쌍을 설계 명세에서 도출한다.
3. 그 쌍을 케이스로 추가하고 다시 측정한다. 모든 조건이 커버될 때까지 반복한다.
4. 복잡한 결정식(조건 4개 초과 등)은 케이스 수가 폭증하므로, 테스트를 늘리기 전에 `/detailed-design` 수준에서 결정식을 단순화할 수 있는지 먼저 검토한다.

## 5. 절차 요약

1. CLAUDE.md의 커버리지 목표 확인 (없으면 질문)
2. 설계 명세에서 케이스 설계 (동치 클래스 → 경계값 → PICT)
3. 테스트 작성 + Doxygen 주석 → `/build`, `/test`
4. 커버리지 측정 → 미커버 분석 → 케이스 추가 → 목표 달성까지 반복
5. `links.csv`에 `DD-nnn,UT-nnn` 링크 추가, 시험이 직접 검증하는 요구사항이 있으면 `SWR-…,UT-nnn`도 추가
6. `python -I .claude/skills/requirements-analysis/scripts/check_traceability.py --until test`
7. `/review unit-test`로 리뷰하고 결과를 `docs/reviews/`에 남긴다.
