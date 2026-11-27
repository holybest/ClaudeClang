---
name: review
description: A-SPICE 요건에 따라 산출물별 체크리스트로 요구사항, 아키텍처, 상세 설계, 코드, 단위 테스트, 통합 테스트를 리뷰한다. 모든 산출물은 완료 전에 이 스킬로 리뷰해야 한다. "리뷰", "검토", "review" 요청 시 사용한다. 인자로 산출물 종류를 받는다 (requirements | architecture | detailed-design | code | unit-test | integration-test).
---

# 산출물 리뷰

모든 산출물은 이 스킬로 리뷰한 뒤에야 완료로 간주한다. 리뷰는 **산출물별 체크리스트**를 항목 하나하나 적용하는 방식으로 한다. 느낌으로 훑어보고 "문제없음"으로 끝내지 않는다.

## 절차

1. **대상과 체크리스트 선택**: 인자 또는 대화에서 산출물 종류를 정하고 해당 체크리스트를 읽는다.

   | 산출물 | 체크리스트 | 기준 프로세스 |
   |--------|------------|---------------|
   | 요구사항 | `checklists/requirements.md` | SWE.1 |
   | 아키텍처 | `checklists/architecture.md` | SWE.2 |
   | 상세 설계 | `checklists/detailed-design.md` | SWE.3 |
   | 코드 | `checklists/code.md` | SWE.3 |
   | 단위 테스트 | `checklists/unit-test.md` | SWE.4 |
   | 통합 테스트 | `checklists/integration-test.md` | SWE.5 |

   종류가 불분명하면 사용자에게 묻는다. 여러 산출물이면 각각 따로 리뷰한다.
2. **상위/하위 산출물 읽기**: 일관성과 추적성 항목을 판단하려면 상위 산출물(예: 설계 리뷰라면 요구사항·아키텍처)과 `docs/traceability/links.csv`가 필요하다. 읽지 않은 문서에 대해 판정하지 않는다.
3. **자동 검사 실행**: 해당하는 것을 먼저 돌린다.
   - 추적성: `python -I .claude/skills/requirements-analysis/scripts/check_traceability.py --until <단계>`
   - 코드: `/build`, `/lint`
   - 테스트: `/test`, 커버리지가 목표인 경우 `bash .claude/skills/unit-test/scripts/coverage.sh ...`
4. **체크리스트 항목별 판정**: 각 항목을 `Pass` / `Fail` / `N/A`로 판정하고 **근거(파일:줄, 문서 절, 실행 결과)**를 적는다. `N/A`는 사유를 적는다. 근거를 확인하지 못한 항목은 Pass로 두지 않고 `미확인`으로 둔다.
5. **지적 사항 정리**: Fail 항목마다 위치, 무엇이 왜 문제인지, 수정 방향, 심각도를 적는다.
   - **Major**: 요구사항 위반, 추적성 누락, 안전·정합성 문제, 규칙 위반 (완료 불가)
   - **Minor**: 가독성·표현·일관성 (이것도 부적합이며 다음 단계 전에 수정해야 한다)
6. **보고서 작성**: `docs/reviews/<산출물>-<YYYY-MM-DD>.md`에 `templates/review-report.md` 형식으로 저장한다.
7. **판정**:
   - `승인`: Fail 없음, 미확인 없음 (Minor 포함)
   - `반려`: Fail 또는 미확인이 하나라도 있음. 조건부 승인은 없다.
   - 승인되기 전에는 다음 개발 단계로 넘어갈 수 없다. 반려 시 모든 부적합을 조치하고 재리뷰한다.

## 리뷰 원칙

- **독립성**: 산출물을 작성한 같은 흐름에서 자기 결과를 승인하지 않는다. `reviewer` 서브에이전트(`.claude/agents/reviewer.md`)에게 산출물 경로와 종류만 넘겨 독립적으로 판정하게 한다. 코드는 `cpp-reviewer`를 병행해도 된다. 작성자의 결론이나 "문제없다"는 의견은 전달하지 않는다.
- **체크리스트를 통과시키기 위해 산출물이 아니라 체크리스트를 바꾸지 않는다.** 체크리스트 개선은 별도 변경으로 하고 사유를 남긴다.
- **재리뷰**: Fail을 수정한 뒤에는 수정한 항목과 영향받는 항목을 다시 판정한 새 보고서(같은 날이면 `-2`)를 남긴다. 이전 보고서는 지우지 않는다.
- 보고서에는 실제 확인한 것만 쓴다. 실행하지 않은 검사를 통과했다고 적지 않는다.

## 체크리스트 개발 방침

체크리스트는 A-SPICE 해당 프로세스의 기본 실천(Base Practice)과 산출물 특성(Work Product Characteristics)에서 도출한 것이며, 프로젝트 규칙(CLAUDE.md, 각 개발 스킬의 규칙)을 포함한다. 항목에는 고유 ID(`REQ-01` 등)가 있다. 프로젝트나 A-SPICE 버전의 요건이 바뀌면 해당 파일을 수정하고 변경 사유를 파일 하단 "변경 이력"에 남긴다.
