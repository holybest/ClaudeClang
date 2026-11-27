---
name: test
description: 프로젝트를 빌드한 뒤 TDD/단위/통합 테스트를 CTest 라벨별로 실행하고 실패를 분석한다. 개발과 CI가 같은 컨테이너와 스크립트를 쓴다. "테스트 돌려줘", "test", 변경 사항 검증이 필요할 때 사용한다.
---

# 테스트

테스트는 CTest **라벨**로 구분한다: `tdd`(구현 단계의 TDD 테스트), `unit`(공식 단위 테스트), `integration`(통합 테스트). 라벨별로 실행하고 **결과도 따로** 낸다 (CLAUDE.md 1.5절, 2.1절).

1. 먼저 `/build` 절차로 빌드한다. 빌드가 실패하면 테스트를 실행하지 않는다.
2. 라벨별로 실행한다. 인자가 없으면 세 라벨을 모두 실행한다:
   ```sh
   bash docker/run.sh bash ci/scripts/test.sh tdd
   bash docker/run.sh bash ci/scripts/test.sh unit
   bash docker/run.sh bash ci/scripts/test.sh integration
   ```
   - 결과는 `build/reports/<라벨>/junit.xml`로 남는다 (CI의 JUnit 플러그인이 읽는 것과 같다).
   - 해당 라벨의 테스트가 없으면 `[N/A] ... 대상 없음`이 출력된다. 통과로 오해하지 말고 "테스트가 없다"고 보고한다.
   - 특정 테스트만: `bash docker/run.sh ctest --test-dir build -R <패턴> --output-on-failure`
3. 테스트가 하나도 없으면 `test-writer` 서브에이전트로 추가할지 제안한다 (`/unit-test`, `/integration-test` 절차).
4. 실패한 테스트마다 테스트 이름, 실패한 단언(assertion), 관련 소스 위치(`파일:줄`)를 정리한다. **테스트를 통과로 꾸미거나, 실패한 테스트를 비활성화·건너뛰도록 고치지 않는다.** 성공률 기준은 100 %이다.
5. 시스템 테스트는 이 스킬의 범위가 아니다 (`/sw-system-test-case`, 게이트는 `python3 ci/scripts/system_test_gate.py`).
