# science-teacher-skills

**한국 2022 개정 교육과정 기반 과학 수업 설계 Claude 스킬 (v0.1.0-preview.1)**

Anthropic의 [k12-teacher-skills](https://github.com/anthropics/k12-teacher-skills)를 한국
초·중등 체제로 이식했습니다. 성취기준·선수관계·세부 학습 주제는 한국 교육과정 학습맵 MCP
2종에서 가져오고, 수업 자료는 편집 가능한 워드 문서로 나옵니다.

> 이 플러그인은 **과학 전용**입니다. 다른 과목은 다루지 않습니다.

## 무엇을 만드나

스킬 2종이 들어 있습니다.

**① 수업 설계** — "중2 광합성 45분 수업 만들어 줘"라고 하면 한 턴에 세 가지가 나옵니다.

| 문서 | 내용 |
|---|---|
| 수업안 | 성취기준 원문, 범주별 학습 목표(지식·이해 / 과정·기능 / 가치·태도), 단계별 전개와 분 배분, 예상되는 학생 생각, 설계 노트 |
| 학생 자료 | 학생이 직접 쓰는 학습지 — 과제, 자료 표, 답란 |
| 관찰 템플릿 | 순회하며 볼 것(look-for), 정리 문항 분류 기준, 기록표 |

**② 수준별 차별화** — "우리 반은 편차가 커요"처럼 기존 수업이 있을 때, 교사용 차별화
수업안 1종 + 학생용 수준별 학습지 3종(가·나·다 모둠)을 만듭니다. 세 수준은 **같은 현상,
같은 핵심 과제**를 다루고 지원만 달라집니다 — 기초 수준이라고 탐구를 빼지 않습니다.

각 패키지의 문서들은 하나의 소스에서 렌더되므로 서로 어긋날 수 없습니다. 성취기준은
학습맵이 준 **공식 원문 그대로** 인용하며, 바꿔 쓰지 않습니다.

## 설치

Claude Code에서 두 줄이면 됩니다.

```
/plugin marketplace add raphysicst-create/science-teacher-skills
/plugin install science-teacher-skills@science-teacher-skills
```

터미널에서 하려면 같은 인자로 `claude plugin marketplace add …` / `claude plugin install …`을
쓰면 됩니다. 설치 후 Claude Code를 재시작하면 스킬 2종(`ko12-lesson-planning`,
`ko12-lesson-differentiation`)과 학습맵 MCP 2종이 함께 올라옵니다.

저장소를 clone해서 쓰려면 clone한 폴더의 경로를 `marketplace add`에 그대로 넘깁니다.

학습맵 MCP 2종은 `plugin/.mcp.json`에 번들되어 있어 `npx`로 자동 실행됩니다 — 따로 설치할
것이 없습니다. 워드 문서 렌더에는 Python 3와 `python-docx`가 필요하며, 없으면 렌더 스크립트가
자동으로 설치합니다.

## 사용

```
중2 과학, 광합성 실험 설계 45분 수업 만들어 줘
```

```
이 수업을 우리 반 수준에 맞게 세 단계로 나눠 줘
```

학년·주제만 있으면 됩니다. 성취기준 코드(`[9과12-01]`)를 알고 있으면 그대로 써도 됩니다.
학습맵이 연결되지 않은 상태에서도 동작하며, 그 경우 수업안에 안내 문구가 붙습니다.

기본 산출은 워드(docx)이고, **한글(HWPX) 파일**을 요청하면 같은 소스에서 함께 렌더됩니다
(추가 의존성 없음 — 표준 라이브러리만으로 OWPML을 직접 생성).

## 데이터 출처

| 데이터 | 출처 |
|---|---|
| 중·고 성취기준·주제·선수관계·전이 | [korean-secondary-learning-map-mcp](https://github.com/raphysicst-create/korean-secondary-learning-map-mcp) |
| 초등 성취기준·주제·선수관계 | [korean-elementary-learning-map-mcp](https://github.com/taehyeonglim/korean-elementary-learning-map-mcp) |
| 성취기준 원문 | 교육부 고시 2022 개정 교육과정 (NCIC 공개 문서) |

초등 학습맵의 성취기준 문장은 저작권 정책상 원문을 재수록하지 않고 요약 필드에서 재구성된
값입니다. 초등 수업안에는 공식 고시문과 대조하라는 안내가 함께 인쇄됩니다. 중등은 원문
verbatim입니다.

이 플러그인은 검정 교과서의 활동·지문·삽화·문항을 재현하지 않습니다. 교사가 출판사를
확언하지 않으면 출판사명을 산출물이나 대화 어디에도 쓰지 않습니다.

## 원저작 표기

원본은 Anthropic, PBC와 Learning Commons의 `k12-teacher-skills` v0.6.0이며 Apache-2.0으로
배포됩니다. 이 저장소도 Apache-2.0을 따르며, 파생 파일에 SPDX 헤더와 원본 경로를 남겼습니다.
자세한 내용은 [LICENSE](LICENSE)와 [NOTICE](NOTICE)를 보세요.

원본에서 바꾼 것은 세 지점입니다 — 표준 조회(Learning Commons Knowledge Graph → 한국 학습맵
MCP), 과목 pedagogy(NGSS 3차원 → 2022 개정 내용 체계 3범주), 교사 대면 언어. 문서 렌더러와
산출 스키마는 무수정이라 원본 업스트림을 계속 추적할 수 있습니다.

## 로드맵

| 단계 | 내용 | 상태 |
|---|---|---|
| 1 | 과학 파일럿 — 골격, 학습맵 연결, 실 수업 생성 검증 | ✅ 완료 (2026-08-01) |
| 2 | HWPX 산출 — OWPML 직접 생성 어댑터, 한컴 실열림 전수 검증 | ✅ 완료 (2026-08-01) |
| 3 | 수업 차별화 스킬 포팅 (✅ 2026-08-01), 공개 배포 | 진행 중 |

설계 근거와 결정 기록은 [DESIGN.md](DESIGN.md)에 있습니다.
