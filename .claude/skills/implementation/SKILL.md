---
name: implementation
description: A-SPICE(SWE.3 구현) 기준으로 상세 설계를 C/C++ 코드로 구현한다. 모든 함수가 반환값을 가지고 return이 마지막에 한 번만 오는 규칙을 적용한다. "구현", "코드 작성", "implement" 요청 시 사용한다.
---

# 구현

입력은 검토된 상세 설계 `docs/design/`이다. 설계에 없는 모듈·함수를 임의로 만들지 않는다. 설계가 부족하면 구현을 멈추고 `/detailed-design`을 먼저 보완한다.

## 함수 규칙

**적용 범위: `src/`, `include/`의 제품 코드.** 테스트 코드(`tests/`)에는 적용하지 않는다 (GoogleTest의 `TEST` 본문과 GMock의 `MOCK_METHOD`는 반환형이 `void`이므로). 테스트 보조 함수는 값을 반환하는 것을 권장한다.

### 1. 모든 함수는 반환값을 가진다
- `void` 함수를 만들지 않는다. 반환할 값이 없으면 **정상 실행 여부를 알 수 있는 상태 코드**를 반환한다.
- 프로젝트 공용 상태 타입을 한 곳(`include/common/status.h` 등)에 정의해 쓴다.
  ```cpp
  enum class Status { Ok = 0, InvalidArgument, OutOfRange, NotInitialized, Failure };
  ```
  C에서는 `typedef enum { STATUS_OK = 0, ... } Status;`. 오류 종류가 의미 있으면 코드를 세분화한다.
- 계산 결과를 반환하는 함수는 값을 직접 반환하거나, 실패 가능성이 있으면 `Status` 반환 + 출력 인자로 결과를 준다.
- **반환 상태는 반드시 호출자가 검사한다.** 무시하려면 `[[nodiscard]]`를 사용해 컴파일러가 강제하게 한다.
- 언어상 반환값을 가질 수 없는 생성자/소멸자/연산자 오버로드 등은 예외로 두되, 초기화는 `Status init(...)`으로 분리하는 것을 우선 고려한다. 예외를 둔 곳은 코드 주석에 이유를 적는다.

### 2. return은 함수 마지막에 한 번만
- 함수 중간의 `return`, 조기 반환을 쓰지 않는다. 결과 변수를 선언하고 끝에서 한 번만 반환한다.
- 오류 처리는 조기 반환 대신 조건 중첩이나 상태 변수로 한다.

```cpp
[[nodiscard]] Status Buffer::write(const uint8_t* data, size_t len) {
    Status result = Status::Ok;

    if (data == nullptr || len == 0U) {
        result = Status::InvalidArgument;
    } else if (len > free_space()) {
        result = Status::OutOfRange;
    } else {
        copy_in(data, len);
    }

    return result;
}
```

## 구현 절차

1. 설계 문서의 모듈(`DD-nnn`)을 하나 고르고, 인터페이스(`IF-nnn`)가 있으면 그 헤더를 먼저 작성한다.
2. **TDD로 구현한다.** `test-driven-development` 스킬에 따라 실패하는 테스트를 `tests/tdd/`에 먼저 쓰고(`cc_add_test(tdd <이름> SOURCES ... LINK ...)`, 라벨 `tdd`), 통과하는 최소 구현을 쓰고, 리팩터링한다. TDD 테스트는 단위 테스트와 폴더·라벨·결과·커버리지를 모두 분리한다. 공식 단위 테스트(MC/DC·분기 100 %)는 `/unit-test`에서 `tests/unit/`에 따로 만든다.
3. 공개 헤더에는 인터페이스에 있는 것만 둔다. 내부 함수·상태는 `static`/익명 네임스페이스로 숨긴다.
4. **모든 소스·헤더 파일 맨 위에 `@file` Doxygen 블록과 Human-in-the-Loop 항목**(`@par AI 작성 이력`: 모델·일시·요청자, `@par 사용자 리뷰`: 상태·일시·리뷰어)을 넣는다. 형식은 CLAUDE.md 2.4절. 모델은 실제로 작성하는 모델의 이름과 ID, 일시는 오늘, 요청자는 `git config user.name`이다. **`사용자 리뷰`는 `미완료`로 두고, AI가 스스로 `완료`로 바꾸지 않는다.** 이미 있는 파일을 고치면 `AI 작성 이력`에 항목을 추가하고 리뷰 상태를 `미완료`로 되돌린다.
5. 각 함수 위에 Doxygen 주석(`@brief`, `@param`, `@return`)과 구현하는 설계 ID(`@design DD-nnn`)를 적는다. 주석률 20 % 이상이 CI 기준이므로 설계 의도를 충분히 적는다.
6. 구현 후 `/build`로 빌드하고 `/lint`로 포맷, 정적 분석, 메트릭(Cppcheck 0건, Lizard CCN ≤ 10·함수 라인 ≤ 80, 주석률, HITL 주석)을 통과시킨다. Stop 훅(`check_lizard.py`)도 응답 종료 때 같은 메트릭을 검사한다.
7. `links.csv`에 `DD-nnn,SRC-<파일 경로>[:<함수>]` 링크를 추가한다. (예: `DD-004,SRC-src/buffer/buffer.cpp:write`)
8. 단위 테스트는 `/unit-test`로 이어서 작성한다.

## 규칙 점검 (완료 전)

아래 검색에서 규칙 위반이 나오면 고친다. (`rg`가 없으면 `grep -rnE`로 대체)
```sh
rg -n '^\s*void\s+\w+\s*\(' src include        # void 함수 (선언부, 람다는 별도 확인)
rg -c '\breturn\b' src                          # 함수당 return 개수는 파일 단위로 읽어서 확인
```
이 검색은 보조 수단이다. 한 함수에 `return`이 둘 이상인지는 리뷰(`/review code`)에서 코드를 읽어 판단한다.

## 완료 조건

1. 빌드가 경고 없이 통과하고 `/lint`(clang-format, clang-tidy, Cppcheck 0건, Lizard, 주석률 20 % 이상, HITL 주석)가 깨끗하다. TDD 테스트가 `tests/tdd/`에 있고 통과한다.
2. 모든 함수가 반환값을 가지고 마지막에 한 번만 return한다.
3. 소스가 설계의 모듈·인터페이스와 일치하고 `links.csv`에 `DD → SRC`가 있다.
4. `/review code`로 리뷰하고 결과를 `docs/reviews/`에 남긴다.
