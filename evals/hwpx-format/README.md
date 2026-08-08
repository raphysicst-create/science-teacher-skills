<!--
SPDX-FileCopyrightText: 2026 science-teacher-skills contributors
SPDX-License-Identifier: Apache-2.0
-->

# hwpx-format — HWPX 시각 품질 루브릭

`docs/hwpx-quality-loop.md` 루프의 **판정 층**. 자동 검사기
(`tests/check_hwpx_quality.py`)가 fail 0을 만든 **뒤에만** 돌린다 — 계측기(자동)가
잡을 수 있는 것을 판정자에게 묻지 않는다.

## 루브릭

`rubrics/format.csv` — V1–V10, 전부 V(Visual) 버킷. 스키마는 다른 evals와 동일
(`ID, Bucket, Criterion, What pass requires, Notes, Conditional`, utf-8-sig).

자동 검사 ID(F4·F5·F6·F9 등)의 "시각 확인판" 항목들은 XML 속성이 아니라
**한글에서 실제로 그렇게 보이는지**를 판정한다 — 속성이 맞아도 한컴이 다르게
그리면 fail이고, 그 fail은 루프의 새 결함으로 등록된다.

## 판정 입력

1. `tests/check_hwpx_quality.py --json` 리포트 (자동 층의 결과)
2. 대상 HWPX에서 추출한 텍스트 (`tests/check_lesson.py`의 `hwpx_text` 사용)
3. **한글 PDF 내보내기 스냅샷** (가능한 환경에서) — V 버킷 판정의 근거.
   PDF 없이 텍스트만으로 판정 불가한 항목은 skip으로 기록한다 (fail 아님).

## 실행 방식

기존 evals와 동일: 판정자 시스템 프롬프트는 `evals/README.md`의 출력 계약을
따르고, 결과는 `evals/runs/<날짜>/verdicts-hwpx-format-<패키지>.json`으로 저장,
`aggregate.py`로 집계한다.
