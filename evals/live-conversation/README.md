<!--
SPDX-FileCopyrightText: 2026 science-teacher-skills contributors
SPDX-License-Identifier: Apache-2.0
-->

# 라이브 대화 평가 — M 버킷 실측 체계

## 왜 따로 있나

산출물 루브릭(수업안 40항목, 차별화 27항목)은 보관된 문서를 채점한다. 그러나 스킬이
의무로 규정한 대화 행동 — 확인 질문의 **타이밍**, 마무리 3종(다양성 안내·다음 선택지·
만족 확인), 교사 언어, 학습맵 호출 시점 — 은 문서에 남지 않는다. 2026-08-06 실채점에서
M3가 전 패키지 "판정 불가"로 남았고, 2026-08-08-diff에서는 세션 기록이 우연히 남아 있어
M1~M4를 채점할 수 있었지만 그건 기회적 측정이었다. 이 디렉터리는 그 공백을 **재현
가능한 시나리오**로 메운다.

구성:

| 파일 | 내용 |
|---|---|
| [scenarios.md](scenarios.md) | 교사 역할 대본 6종 (S1 학년 미상 · S2 초1–2 특례 · S3 범위 미상 · S4 표준 마무리 · S5 학생 정보 제공 · S6 수정 턴) + 시나리오×항목 매트릭스 |
| [rubrics/live.csv](rubrics/live.csv) | 라이브 전용 채점 항목 L1~L7 |
| (기존) [../ko12-lesson-differentiation/rubrics/clarifying_question.csv](../ko12-lesson-differentiation/rubrics/clarifying_question.csv) | 조건부 확인 질문 2항목 — S1·S2가 조건을 만든다 |

## 실행 절차

1. **환경**: 플러그인이 설치된 Claude Code에서 시나리오마다 **새 세션**을 연다(S6만 S4에
   이어서). 학습맵 MCP 연결 여부를 세션 시작 시 확인해 기록한다 — L7 판정 조건이다.
2. **대본 실행**: scenarios.md의 첫 메시지를 그대로 붙여넣고, 이후에는 반응 규칙표의 답만
   한다. 모델이 물어야 할 것을 묻지 않아도 끊지 않고 끝까지 진행한다.
3. **기록 확보**: 세션 종료 후 대화 기록을 확보한다. Claude Code는 세션 전체(도구 호출
   포함)를 `~/.claude/projects/<프로젝트-슬러그>/<세션ID>.jsonl`에 남긴다 — 이 파일이
   판정 원본이다. L1(타이밍)·L7(학습맵 호출)은 도구 호출 순서까지 봐야 하므로 채팅 화면
   복사본으로는 부족하다.
4. **채점**: 판정자(사람 또는 판정 서브에이전트)에게 시나리오당 하나씩 넘긴다 —
   transcript 경로 + rubrics/live.csv + clarifying_question.csv + scenarios.md의 해당
   시나리오 절. 판정자는 9개 ID(L1~L7, M-CLARIFY-GRADE, M-CLARIFY-G12)를 전수 판정하고
   (해당 없음 = `"skip"`), FAIL 설명에는 대화 축자 인용을 싣는다.
5. **기록 형식**: `evals/runs/<날짜>-live/verdicts-live-s1.json` … `-s6.json`. 스키마는
   기존 실행과 동일하되 패키지 대신 시나리오를 적는다:

   ```json
   {
     "package": "live/s1-grade-unknown",
     "scenario": "S1",
     "rubrics": ["live-conversation/rubrics/live.csv",
                 "ko12-lesson-differentiation/rubrics/clarifying_question.csv"],
     "judge_model": "…",
     "run_date": "…",
     "inputs": "세션 jsonl 경로 + 학습맵 연결 여부",
     "verdicts": [ {"id": "L1", "pass": true, "explanation": "…"}, … ]
   }
   ```

6. **집계**: `python evals/runs/aggregate.py <날짜>-live` — rubrics 선언 순서대로 9항목 ×
   6시나리오 매트릭스가 나온다.

## 판정 유의

- **S3의 차별화 M3**(수준 범위 질문)는 별도 ID로 기록하지 않고 L1 판정 설명 안에 한 줄로
  남긴다 — 차별화 루브릭 전체를 선언하면 산출물 전용 26항목이 미판정으로 무결성 검사에
  걸리기 때문이다.
- 시나리오가 조건을 만들지 못한 항목(매트릭스의 skip 칸)은 반드시 `"skip"`으로 기록한다 —
  빈칸이 아니라. aggregate의 전수 판정 무결성 검사가 이를 요구한다.
- 자동화 주의: `claude -p` 헤드리스 1회 호출은 다중 턴 대본을 소화하지 못한다. 대본 실행은
  수동(또는 사람이 개입하는 반자동)이 기본이고, 그래서 시나리오를 6개로 절제했다 —
  1회전에 30~60분이면 끝난다.

## 배포 문서에 쓰는 문구

라이브 1회전을 돌기 전까지 배포 노트에는 이렇게 적는다:
"대화 행동(확인 질문 타이밍·마무리 3종·교사 언어)은 시나리오 기반 라이브 평가 체계가
준비되어 있으나(evals/live-conversation/) 아직 실측 전이다. 산출물 품질 수치는 이 항목을
포함하지 않는다."
