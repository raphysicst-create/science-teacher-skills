<!--
SPDX-FileCopyrightText: 2026 Anthropic, PBC
SPDX-FileCopyrightText: 2026 Learning Commons
SPDX-FileCopyrightText: 2026 science-teachers-skills contributors
SPDX-License-Identifier: Apache-2.0

원본: k12-teacher-skills/plugin/skills/k12-lesson-planning/references/learning-commons-kg.md
Learning Commons Knowledge Graph 호출 시퀀스를 한국 2022 개정 교육과정 학습맵 MCP
(korean-secondary-learning-map-mcp · korean-elementary-learning-map-mcp) 호출로 치환.
-->

# 한국 교육과정 학습맵 MCP — 호출 시퀀스

`ko12-lesson-planning` Step 2에서 **학습맵 MCP 도구가 연결된 경우에만** 사용한다.
연결되지 않았다면 이 파일 전체를 건너뛴다 (SKILL.md Step 2에 폴백 있음).
연결됐는데 호출하지 않는 것은 치명적 실패(critical failure)다.

## 서버 라우팅 (모든 과목 공통)

두 개의 독립 MCP 서버가 있다. **서로 다른 그래프이며 교차 조회되지 않는다.**

| 학교급 | 서버 | 도구 접두 신호 |
| --- | --- | --- |
| 초등 (1–6학년) | `curriculum-kr-elementary` | 성취기준 코드 `[2xx…]` `[4xx…]` `[6xx…]` — `gradeBand: "1-2" \| "3-4" \| "5-6"` |
| 중·고 (보통교과) | `curriculum-kr-secondary` | 코드 `[9xx…]` (중), `[10xx…]` `[12xx…]` (고) — `schoolLevel: "middle" \| "high"`, `gradeBand: "7-9" \| "10" \| "10-12"` |

**두 서버의 차이 (실측):**
- 초등에는 `get_transitions`가 없다 (중→고 전이는 중등 전용). 초등은 9종, 중등은 11종.
- 초등 `search_standards` 결과의 요약 필드는 `summary`가 아니라 **`focus`**이며 문장이 잘려 있다.
  초등 `get_standard`에는 `subject` 파라미터가 없다.
- ⚠ **초등 성취기준 원문은 verbatim이 아니다.** 초등 레코드는 `sourceTextIncluded: false`이고
  `sourceBasis`에 "표준 본문은 저작권 정책상 재수록하지 않는다"고 명시돼 있다. `officialText`
  필드는 존재하지만 `focus + "할 수 있다"`로 조립된 값이다. 따라서 **초등 수업안에서는 성취기준을
  verbatim으로 인용했다고 말하지 않는다** — 콜아웃에 이 문장을 쓰되 수업안 푸터에 다음을 단다:
  *"초등 성취기준 문장은 학습맵의 요약 필드에서 재구성된 것입니다. 공식 고시문과 대조해 확인하세요."*
  중등은 `sourceLocator`(PDF 쪽·sha256)를 갖춘 verbatim이므로 이 제한이 없다.

라우팅 규칙:
- 교사가 말한 **학년**으로 서버를 정한다. 중학교 수업이면 secondary만 호출한다.
- 단, **선수학습 결손 진단** 맥락(중1 대상, "기초가 안 된", "초등 내용부터")이 명시되면
  elementary를 추가 호출해 초등 성취기준을 역추적한다.
- **초→중 브리지는 두 그래프 어디에도 없다.** 초등 결손 추적은 코드 연결이 아니라
  **키워드 병렬 검색**으로 한다: 같은 주제어로 두 서버의 `search_standards`를 각각 호출하고,
  학년군 순서로 모델이 직접 잇는다. 이 연결은 "추정 연계"임을 산출물에 표시한다.
- 중→고 심화 연계는 secondary의 `get_transitions`가 공식 근거(별책) 기반으로 제공한다 — 추정 아님.

## 성취기준 확정 (모든 과목 공통)

원본의 `find_standard_statement` 역할을 3개 도구가 분담한다:

- **코드가 주어진 경우** ("[9과01-01]", "9과01-01" 둘 다 수용): `get_standard(code, subject?)` 직행.
  코드 공유 과목(12스문·12심독 계열 11개)은 `subject` 파라미터로 구분해야 한다.
  코드 형식이 안 맞아 실패하면 → 키워드 검색으로 폴백; 반환된 실제 `code` 값으로 형식을 확인해 재시도.
- **코드가 없는 경우**: `search_standards(query, schoolLevel?, subject?, domain?, gradeBand?)` —
  요약 목록 반환. `gradeBand`는 `"7-9"`(중) / `"10"`(고 공통) / `"10-12"`(고 선택).
  성취기준 **원문 표현**으로 찾아야 할 때는 `search_standard_text(query, …)`(전문 검색, 매칭 스니펫)를 쓴다.
  가장 적합한 항목을 고르고 `get_standard`로 전체 레코드 + **공식 원문** + 연결 주제를 가져온다.
- **총 검색 시도 3회 상한.** 엉뚱한 학년군·과목 결과는 실패로 계산 — 남은 시도는 다른
  키워드(과목명, 영역명, 소재)로 쓴다. 3회 후에도 없으면 검색 중단, 훈련 지식의 최적
  성취기준으로 진행하고 부분-커버리지 푸터를 수업안에 단다.

확정된 성취기준에서 추출: **`officialText`**(공식 원문 — 수업안 성취기준 콜아웃에 verbatim 인용),
`code`, 그리고 연결된 **주제 ID 목록**(`linkedTopics[].id` — 이후 호출에 필요, 저장).
⚠ `summary` 필드는 기계 생성 요약(`summaryKind: "mechanical-derivative"`)이다 — 인용에 쓰지
않는다. 원문은 `officialText`뿐이다.

## 과학 (Science)

초안 작성 **전에** 호출한다. 연결됐는데 호출하지 않으면 치명적 실패다. 모든 호출을 마치고
아래 명시된 것만 추출한 뒤 곧장 Step 3으로 간다 — 학습맵 조회 결과는 채팅에 요약하지 않고,
초안의 성취기준 한 줄 읽어주기(read-back)로만 드러낸다.

호출 간 데이터 의존은 성취기준의 **주제 ID**(2–4단계에서 사용) 하나뿐이다. 따라서:
성취기준을 확정한 뒤, 2–4단계 호출을 **하나의 병렬 배치**로 실행한다.

**사용 도구:** `search_standards`, `search_standard_text`, `get_standard`, `search_topics`,
`get_topic`, `get_prerequisites`, `get_learning_roadmap`, `get_transitions`(secondary 전용),
`list_clusters`.

1. **성취기준**: 위 *성취기준 확정* 절차대로. `get_standard`가 반환한 **공식 원문**을
   수업안의 성취기준 콜아웃에 그대로 쓴다. 연결 주제 ID들을 저장한다.

2. **선수관계**: `get_prerequisites(topicId, depth: "all")` → 추출: 위상 정렬된 선수 경로
   (`pathOrder[]`)에서 **직전 선수 주제 1개**(그 주제가 속한 성취기준 코드 포함). 학습 목표
   섹션에 사용. 학습맵에 edge가 있는데 명시하지 않는 것은 치명적 실패다.
   ⚠ **edge가 없는 성취기준이 많다** (중고 선수관계는 공식 근거가 있는 것만 보수적으로 수록,
   `directEdges: []`로 반환). 그 경우 훈련 지식으로 직전 선수 내용을 쓰되 **"추정"임을 수업안에
   표시한다** — 학습맵 근거인 것처럼 쓰지 않는다.
   중학교 수업 + 결손 진단 맥락이면 elementary 서버에도 키워드 병렬 검색(위 라우팅 규칙).

3. **세부 학습 주제**: 저장한 주제 ID들에 `get_topic(topicId)` → 추출: 관찰 증거(`evidence[]`)와
   평가 문항(`assessmentPrompts[]`), 관점 키(`facetKey` — 예: 탐구 설계와 자료 해석 /
   증거 기반 설명과 적용). 주제는 성취기준을 관점별로 분해한 **자동 생성 후보 단위**라 서술이
   템플릿형이다 — 그대로 복사하지 말고 **시드로 쓴다**: `facetKey` 관점을 수업 목표 불릿과
   look-for 행의 뼈대로 삼고, `evidence`를 이번 수업의 활동·소재로 구체화한 "구체적 학생 행동"으로
   재진술한다. `assessmentPrompts`는 형성평가·정리 문항(exit ticket) 설계의 시드. 나머지는 버린다.

4. **심화 연계** (secondary·해당 시): `get_transitions(standardCode 또는 topicId)` → 추출:
   이 내용이 고교 어느 과목·성취기준으로 이어지는지 1–2개(`asFrom`/`asTo`). 수업안 "단원 맥락"
   섹션에서 "이 내용은 이후 ___로 심화된다" 한 문장으로만 사용. 고교 수업이면 역방향(중학교
   기반)으로 조회. ⚠ 전이는 공식 근거가 있는 175건만 수록 — 빈 배열이 정상인 성취기준이 많다.
   없으면 이 문장을 생략한다 (훈련 지식으로 지어내지 않는다).

5. **오개념**: **학습맵에 오개념 도구가 없다.** 훈련 지식에서 3개를 작성하되, 각 항목은
   반드시 해당 성취기준의 원문 표현과 3단계에서 얻은 세부 주제에 정합해야 한다.
   형식: *학생의 생각* / *지속되는 이유* / *교사의 대응*.
   (오개념 데이터 소스가 별도 MCP로 연결된 경우 — 도구명에 misconception이 포함 —
   그쪽을 우선 호출하고 훈련 지식은 폴백으로 강등한다.)

6. **커리큘럼 자료**: **한국판에는 IM/OpenSciEd 대응 자료 검색이 없다.** 이 단계는 생략한다.
   교과서 출판사별 전개는 학교마다 다르므로, 수업안은 성취기준·주제 데이터만으로 독립적으로
   설계하고 특정 출판사 교과서의 활동·삽화·지문을 재현하지 않는다.

**학습맵 미연결 시:** 최선의 지식으로 작성하고 푸터 추가:
*"한국 교육과정 학습맵 미연결 상태에서 생성됨. 성취기준 표현과 오개념은 일반적 모범 사례 기준."*

→ **학습맵 단계 완료. 곧장 Step 3으로.**
