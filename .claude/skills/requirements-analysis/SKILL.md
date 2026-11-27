---
name: requirements-analysis
description: A-SPICE(SWE.1) 기준으로 소프트웨어 요구사항을 분석·작성한다. 기능/비기능(품질·제한·제약) 분류, ISO 25010 품질 특성 적용, 양방향 추적성 수립이 필요할 때 사용한다. "요구사항 분석", "요구사항 작성", "SWR", "requirements" 요청 시 사용한다.
---

# 요구사항 분석 (A-SPICE SWE.1)

CLAUDE.md의 1.2절(단계·산출물 위치)과 6절(ID 규칙, 추적성 파일 경로)을 먼저 확인한다.

## 1. 요구사항 분류

모든 요구사항은 아래 중 정확히 하나에 속한다.

| 분류 | ID 접두사 | 저장 위치 |
|------|-----------|-----------|
| 기능 요구사항 | `SWR-FUN-nnn` | `docs/requirements/functional.md` |
| 비기능 – 품질 | `SWR-QUA-nnn` | `docs/requirements/non-functional.md` |
| 비기능 – 제한(limit) | `SWR-LIM-nnn` | `docs/requirements/non-functional.md` |
| 비기능 – 제약(constraint) | `SWR-CON-nnn` | `docs/requirements/non-functional.md` |
| 기능 안전 요구사항 | `FSR-nnn` | **`docs/safety/`의 별도 문서**. 위 문서에 섞지 않는다. |

- **제한**: 수치로 표현되는 한계. 예) 응답 시간 ≤ 10 ms, 메모리 ≤ 64 KB.
- **제약**: 해결책·환경에 대한 강제 조건. 예) C++20 사용, 동적 할당 금지, 특정 OS.
- 기능 안전 요구사항을 발견하면 `docs/safety/`에 작성하고, 일반 요구사항에서는 `FSR-nnn`을 **참조만** 한다.

## 2. 품질 요구사항: ISO 25010

`SWR-QUA`는 반드시 ISO/IEC 25010의 품질 특성·부특성 중 하나를 `품질 특성` 필드에 명시한다.
`references/iso25010.md`에 8개 특성과 부특성, 측정 예시가 있다. 이 목록에 없는 임의의 특성명은 쓰지 않는다.
각 품질 요구사항은 **측정 가능한 기준**(수치, 조건, 측정 방법)을 가져야 한다. "빠르게", "안정적으로" 같은 표현은 허용하지 않는다.

## 3. 요구사항 작성 형식

```markdown
### SWR-FUN-001 <짧은 제목>
- 설명: 시스템은 <조건>일 때 <동작>해야 한다(shall).
- 근거: <출처 – 이해관계자 요구, 상위 시스템 요구 ID 등>
- 우선순위: 필수 | 권장
- 검증 방법: 단위 시험 | 통합 시험 | 검사 | 분석
- 수락 기준: <판정 가능한 조건>
- 품질 특성: (SWR-QUA만) <ISO 25010 특성 / 부특성>
- 상태: 초안 | 검토됨 | 승인됨
```

요구사항 한 개는 한 가지 사항만 말하고, 모호하지 않고, 검증 가능하고, 다른 요구사항과 충돌하지 않아야 한다.

## 4. 양방향 추적성

추적성은 `docs/traceability/links.csv`(`parent_id,child_id`)에 기록한다.

- **상향**: 각 `SWR`은 상위 근거(시스템 요구, 이해관계자 요구)를 `근거`에 적는다.
- **하향**: 각 `SWR`은 이후 산출물인 아키텍처(`ARC`), 상세 설계(`DD`), 소스, 단위/통합 시험(`UT`/`IT`)과 연결된다.
  이 연결은 해당 산출물을 만드는 스킬이 `links.csv`에 추가한다. 요구사항 작성 시점에는 하향 연결이 비어 있어도 된다.
- 요구사항을 추가·변경·삭제하면 `links.csv`도 함께 갱신한다.

검사:
```sh
python -I .claude/skills/requirements-analysis/scripts/check_traceability.py
```
출력의 "하향 누락"/"상향 누락"/"알 수 없는 ID"를 모두 해소해야 한다. 아직 만들지 않은 단계는 `--until arch`, `--until design`, `--until test`로 범위를 제한한다.

## 5. 완료 조건

1. 모든 요구사항이 위 분류 중 하나이고, 품질 요구사항은 ISO 25010 특성이 있다.
2. 안전 요구사항이 별도 문서에 분리되어 있다.
3. `check_traceability.py --until req`가 오류 없이 끝난다.
4. `/review requirements`로 리뷰하고 결과를 `docs/reviews/`에 남긴다.
