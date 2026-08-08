# evals 실채점 집계 — 2026-08-06 — ko12-lesson-planning

루브릭 40항목 × 패키지 4종 = 160칸
무결성: OK — 전수 판정, 루브릭 외 ID 0

PASS 149 / FAIL 6 / skip 5 — 채점 칸 기준 통과율 149/155 = 96.1%

- elementary: 38/38 (100.0%), skip 2
- middle-school: 34/39 (87.2%), skip 1
- smoke-test: 39/39 (100.0%), skip 1
- urgent-middle-school: 38/39 (97.4%), skip 1

## FAIL 전건

- **P6b / middle-school** [CONFIRMED] — Look-fors — observable behavior, attributed to a category
  - 행동과 교사 대응은 있으나 범주 귀속이 2022 개정 3범주가 아니다. 5개 전부 (탐구 설계)·(자료 해석)·(증거 기반 설명) — 학습맵 topic facetKey다. 게다가 관찰 템플릿이 이를 '괄호 안은 이 행동이 성취기준의 어느 범주에 해당하는지입니다'라고 잘못 설명한다. 4패키지 대조 결과 이 패키지만의 이탈(초등·긴급·스모크는 전부 3범주 태그 사용).
- **O3 / middle-school** [JUDGE_VARIANCE] — Observation template rows are usable in the field
  - 판정자는 기록표 행에 행동 라벨이 없고(모둠/본 것/다음 수업에서 할 일 + 빈 8행 26pt) 관찰 포인트가 표 위 불릿으로만 있다는 이유로 fail 처리했다. 그러나 검증 결과 이 구조는 4패키지 공통(smoke-test 8행 28pt, elementary 10행 24pt, urgent 8행 28pt)이며 나머지 셋은 같은 구조로 pass를 받았다. 패키지 결함이 아니라 O3 기준의 미세부화에서 온 판정자 편차 — 루브릭 보정 대상.
- **O10 / middle-school** [CONFIRMED] — No contradictions across artifacts
  - 배부 시점 모순. 준비물은 '자료 표 — 학생 학습지에 인쇄되어 있음'이라고 하는데, 자료 해석 단계는 '설계표를 걷지 않은 채… 표를 배부한다'고 지시한다. 학습지는 이미 실험 설계 단계에 배부됐으므로(배부 2분이 15분 안에) 같은 표를 그 시점에 다시 배부할 수 없다. 부수로 '설계 학습지, 모둠당 1장'과 학생별 이름란·개별 회수도 어긋난다.
- **O11 / middle-school** [CONFIRMED] — Lesson plan is internally consistent
  - 논증 토의를 누가 여는지 수업안이 자기모순. 자료 해석 단계는 '절반이 되지 않는다는 점을 짚을 학생을 찾아 둔다 (논증 토의에서 먼저 발표시킨다)'인데, look-for 1번은 조작 변인을 좁힌 모둠을 '가장 먼저 발표시킨다 — 나머지 설계의 기준이 된다'이고 관찰 템플릿이 '가장 먼저 발표시킬 모둠 하나에 별표를 해 두었다가 논증 토의를 그 모둠으로 엽니다'로 같은 자리에 못박는다. 둘 다 첫 번째일 수 없고 강조점(설계 검토 vs 정량 해석)도 다르다.
- **P10 / middle-school** [CONFIRMED] — Standards economy
  - 목표 성취기준은 1회로 경제적이나, 선수 성취기준이 전문 인용됐다 — '[9과02-01] 세포는 생명 활동이 일어나는 기본 단위임을 이해하고, 세포의 구조와 기능의 관계를 추론하기'는 학습맵 진술 전문이다. 루브릭은 코드 + 짧은 요지만 허용하며, 바로 앞에 요지('세포와 엽록체')가 이미 있어 전문은 중복이다.
- **P-S2 / urgent-middle-school** [CONFIRMED] — Anchor phenomenon is observable and drives the lesson
  - 현상은 구체적이고 설명 대상으로 올바르게 제시되나 학생이 경험하지 않는다 — '앵커 현상 [제안]: 물풀 시험관 두 개… 칠판 그림과 말로 제시하며, 준비물이 필요 없다', '칠판에 시험관 두 개를 그린다'. 루브릭은 '학생이 직접 관찰할 수 있는 것'을 요구하며 'described rather than experienced'를 명시적 fail 조건으로 든다. 실연·영상·사진·실물 어느 것도 없다. 같은 성취기준의 다른 두 패키지는 모두 실물 관찰로 통과했다.

## 항목 × 패키지

| ID | 항목 | elementary | middle-school | smoke-test | urgent-middle-school |
|---|---|---|---|---|---|
| P1 | Standard named verbatim (중등) / official-text c | ○ | ○ | ○ | ○ |
| P2 | Prerequisite named — or honestly marked as inf | ○ | ○ | ○ | ○ |
| P3 | 지식·이해 target is an enduring understanding, not | ○ | ○ | ○ | ○ |
| P4a | Anticipated student thinking — count within th | ○ | ○ | ○ | ○ |
| P4b | Anticipated student thinking — each entry is c | ○ | ○ | ○ | ○ |
| P5 | Lesson phases present and sequenced correctly | ○ | ○ | ○ | ○ |
| P6a | Look-fors — minimum count | ○ | ○ | ○ | ○ |
| P6b | Look-fors — observable behavior, attributed to | ○ | **×** | ○ | ○ |
| P7 | Visual scaffolds with rationale | ○ | ○ | ○ | ○ |
| P8 | Student engagement hook | ○ | ○ | ○ | ○ |
| P9 | Timing is realistic | ○ | ○ | ○ | ○ |
| R1 | Grade-level demand is maintained | ○ | ○ | ○ | ○ |
| R2 | At least one task demands student reasoning | ○ | ○ | ○ | ○ |
| R3 | Exit ticket applies today's 지식·이해 through 과정·기 | ○ | ○ | ○ | ○ |
| R4 | Student agency prompt on worksheet | ○ | ○ | ○ | ○ |
| O2 | Student materials contain no teacher-only cont | ○ | ○ | ○ | ○ |
| O3 | Observation template rows are usable in the fi | ○ | **×** | ○ | ○ |
| O3b | Observation template exit-ticket section is pr | ○ | ○ | ○ | ○ |
| O4 | Lesson plan is concise and scannable | ○ | ○ | ○ | ○ |
| O5 | Universal Design access features | ○ | ○ | ○ | ○ |
| O6 | Teacher and student materials describe the sam | ○ | ○ | ○ | ○ |
| O7 | Teacher adaptation rationale notes | ○ | ○ | ○ | ○ |
| O8 | Outputs are specific not generic | ○ | ○ | ○ | ○ |
| O9 | Narrative coherence across artifacts | ○ | ○ | ○ | ○ |
| O10 | No contradictions across artifacts | ○ | **×** | ○ | ○ |
| O11 | Lesson plan is internally consistent | ○ | **×** | ○ | ○ |
| O12 | Closing phase introduces nothing new | ○ | ○ | ○ | ○ |
| M3 | Follow-up options offered | – | – | – | – |
| M5 | No textbook-publisher content or naming | ○ | ○ | ○ | ○ |
| O13 | Information density | ○ | ○ | ○ | ○ |
| O14 | Writing space matches demand | ○ | ○ | ○ | ○ |
| P10 | Standards economy | ○ | **×** | ○ | ○ |
| O15 | Document set fits the lesson | ○ | ○ | ○ | ○ |
| P-S1 | Three content-system categories are separate a | ○ | ○ | ○ | ○ |
| P-S2 | Anchor phenomenon is observable and drives the | ○ | ○ | ○ | **×** |
| P-S3 | Investigation precedes explanation | ○ | ○ | ○ | ○ |
| P-S4 | 가치·태도 is observable and required of students,  | ○ | ○ | ○ | ○ |
| P-S5 | Model revision is present and mechanistic — or | ○ | ○ | ○ | ○ |
| R-S1 | Evidence-based writing cites investigation evi | ○ | ○ | ○ | ○ |
| R-S2 | Quantitative reasoning required in student ana | – | ○ | ○ | ○ |

○ pass · × fail · – skip (조건 미충족 또는 판정 불가)
