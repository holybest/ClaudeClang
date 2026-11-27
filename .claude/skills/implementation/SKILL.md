---
name: implementation
description: A-SPICE(SWE.3 구현) 기준으로 상세 설계를 C/C++ 코드로 구현한다. 모든 함수가 반환값을 가지고 return이 마지막에 한 번만 오는 규칙을 적용한다. "구현", "코드 작성", "implement" 요청 시 사용한다.
---

# 구현

입력은 검토된 상세 설계 `docs/design/`이다. 설계에 없는 모듈·함수를 임의로 만들지 않는다. 설계가 부족하면 구현을 멈추고 `/detailed-design`을 먼저 보완한다.

## 함수 규칙

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
2. 공개 헤더에는 인터페이스에 있는 것만 둔다. 내부 함수·상태는 `static`/익명 네임스페이스로 숨긴다.
3. 각 함수 위에 Doxygen 주석(`@brief`, `@param`, `@return`)과 구현하는 설계 ID(`@design DD-nnn`)를 적는다.
4. 구현 후 `/build`로 빌드하고 `/lint`로 포맷·정적 분석을 통과시킨다.
5. `links.csv`에 `DD-nnn,SRC-<파일 경로>[:<함수>]` 링크를 추가한다. (예: `DD-004,SRC-src/buffer/buffer.cpp:write`)
6. 단위 테스트는 `/unit-test`로 이어서 작성한다.

## 규칙 점검 (완료 전)

아래 검색에서 규칙 위반이 나오면 고친다. (`rg`가 없으면 `grep -rnE`로 대체)
```sh
rg -n '^\s*void\s+\w+\s*\(' src include        # void 함수 (선언부, 람다는 별도 확인)
rg -c '\breturn\b' src                          # 함수당 return 개수는 파일 단위로 읽어서 확인
```
이 검색은 보조 수단이다. 한 함수에 `return`이 둘 이상인지는 리뷰(`/review code`)에서 코드를 읽어 판단한다.

## 완료 조건

1. 빌드가 경고 없이 통과하고 `/lint`가 깨끗하다.
2. 모든 함수가 반환값을 가지고 마지막에 한 번만 return한다.
3. 소스가 설계의 모듈·인터페이스와 일치하고 `links.csv`에 `DD → SRC`가 있다.
4. `/review code`로 리뷰하고 결과를 `docs/reviews/`에 남긴다.
