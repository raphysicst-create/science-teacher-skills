<!--
SPDX-FileCopyrightText: 2026 science-teacher-skills contributors
SPDX-License-Identifier: Apache-2.0
-->

# hwpx-quality-loop — HWPX 품질 재귀 개선 루프

HWPX(교사 전달물)가 HTML(내부 미리보기)과 같은 품질로 나오도록, **측정 → 수정 →
재렌더 → 재측정**을 수렴할 때까지 반복하는 루프. 2026-08-08에 1회차를 실행해
기준선 805건 결함을 0건으로 수렴시켰다(아래 이력). 앞으로 렌더러를 고치거나
교사 불만이 들어올 때마다 이 루프를 다시 돈다.

## 원칙

1. **측정 없이 수정 없다.** 모든 결함은 검사기 ID(S/F/C/P/G)로 명명되고,
   수정 커밋은 그 ID를 인용한다. "마음에 안 든다"는 피드백은 루프에 넣기 전에
   결함 ID로 번역한다(아래 피드백 변환표).
2. **검사기가 먼저 자란다.** 새 결함 유형이 발견되면 렌더러를 고치기 **전에**
   `tests/check_hwpx_quality.py`에 검사 항목을 추가한다 — 그래야 재발이 잡힌다.
   이것이 이 루프의 재귀성이다: 루프를 돌 때마다 검사기가 촘촘해진다.
3. **두 스킬 사본은 항상 동일하다.** 렌더 스크립트는 planning 쪽을 고치고
   differentiation으로 복사한 뒤 해시를 비교한다. diff가 있으면 그 자체가 결함.
4. **한 소스에서 전 문서 렌더.** 산출물을 손으로 고치지 않는다 — JSON을 고치고
   재렌더한다(DESIGN.md §5 불변 원칙).

## 루프 구조

```
        ┌─────────────────────────────────────────────────────┐
        │  0. 기준선: check_hwpx_quality.py --json baseline    │
        └────────────────────────┬────────────────────────────┘
                                 ▼
        ┌─────────────────────────────────────────────────────┐
   ┌──▶│  1. 결함 목록화 (검사기 ID + 교사 피드백 번역)        │
   │    └────────────────────────┬────────────────────────────┘
   │                             ▼
   │    ┌─────────────────────────────────────────────────────┐
   │    │  2. 검사기 확장 (새 유형이면 검사 항목 먼저 추가)     │
   │    └────────────────────────┬────────────────────────────┘
   │                             ▼
   │    ┌─────────────────────────────────────────────────────┐
   │    │  3. 렌더러 수정 (planning 사본) + diff 사본 동기화    │
   │    └────────────────────────┬────────────────────────────┘
   │                             ▼
   │    ┌─────────────────────────────────────────────────────┐
   │    │  4. 전 파일럿 재렌더 (render_all.sh — 게이트 내장)    │
   │    └────────────────────────┬────────────────────────────┘
   │                             ▼
   │    ┌─────────────────────────────────────────────────────┐
   │    │  5. 자동 검증: check_hwpx_quality + check_lesson      │
   │    │     + smoke + (로컬) validate.py                     │
   │    └────────────────────────┬────────────────────────────┘
   │                             ▼
   │    ┌─────────────────────────────────────────────────────┐
   │    │  6. 실측 검증(로컬 전용): 한컴 COM 실열림             │
   │    │     + 한글에서 육안 확인 → 교사 판정                  │
   │    └────────────────────────┬────────────────────────────┘
   │                             ▼
   │              수렴? ──아니오──┘ (새 결함 → 1로)
   │                │
   └── 아니오 ──────┤
                    ▼ 예
        ┌─────────────────────────────────────────────────────┐
        │  종료: 커밋 (검사기 + 렌더러 + 재렌더 산출물)          │
        └─────────────────────────────────────────────────────┘
```

**수렴 기준** (모두 충족 시 루프 종료):
- `tests/check_hwpx_quality.py` 전 파일럿 FAIL 0건
- `tests/check_lesson.py` DoD 통과 (파일럿 3종)
- `tests/smoke/check_hwpx.py` 통과
- 로컬 툴체인 `validate.py` 전 파일 VALID (가능한 환경에서)
- 한컴 COM 실열림 전 파일 PASS (가능한 환경에서)
- 교사(사용자)가 육안으로 새 결함을 제기하지 않음

## 실행 명령 (한 회차)

```bash
ROOT="<저장소 루트>"
PLAN="$ROOT/plugin/skills/ko12-lesson-planning"
DIFF="$ROOT/plugin/skills/ko12-lesson-differentiation"

# 4. 재렌더 (render_all.sh가 최소 게이트 G1–G6을 자동 실행)
cd "$ROOT/pilot/elementary"      && bash "$PLAN/scripts/render_all.sh" lesson.json out
cd "$ROOT/pilot/middle-school"   && bash "$PLAN/scripts/render_all.sh" lesson.json out
cd "$ROOT/pilot/urgent-middle-school" && bash "$PLAN/scripts/render_all.sh" lesson.json out
cd "$ROOT/pilot/elementary"      && bash "$DIFF/scripts/render_all.sh" differentiation.json out-differentiation
cd "$ROOT/pilot/middle-school"   && bash "$DIFF/scripts/render_all.sh" differentiation.json out-differentiation
cd "$ROOT" && bash "$PLAN/scripts/render_all.sh" tests/smoke/korean_lesson.json tests/smoke/out/ko

# 5. 자동 검증 (커밋된 층 — 어디서나 실행 가능, stdlib)
cd "$ROOT"
python tests/check_hwpx_quality.py \
  pilot/elementary/out pilot/elementary/out-differentiation \
  pilot/middle-school/out pilot/middle-school/out-differentiation \
  pilot/urgent-middle-school/out tests/smoke/out/ko
python tests/check_lesson.py pilot/elementary/lesson.json pilot/elementary/out
python tests/check_lesson.py pilot/middle-school/lesson.json pilot/middle-school/out
python tests/smoke/check_hwpx.py tests/smoke/out/ko

# 3b. 사본 동기화 검증 (수정한 회차에만)
for f in render_lesson_hwpx.py lesson_common.py render_lesson_html.py \
         render_documents.py theme.css check_hwpx_min.py; do
  cmp -s "$PLAN/scripts/$f" "$DIFF/scripts/$f" || echo "DRIFT: $f"
done

# 6. 실측 검증 (이 머신 전용 — lxml·pywin32·PyMuPDF·한글 설치 필요, CI 불가)
python .claude/skills/hwpx/scripts/validate.py --layout <파일.hwpx>
python .claude/skills/hwpx/scripts/finalize_hwpx.py --hancom <파일.hwpx>
# 5회차에 추가된 실측 계측기 3종:
python .claude/skills/hwpx/scripts/export_pdf.py     # 전 파일럿 → PDF 스냅샷 + 쪽수
python .claude/skills/hwpx/scripts/fill_check.py     # V5 계측판: 쪽 하단 공백 >⅓ 검출
python .claude/skills/hwpx/scripts/roundtrip_hwpx.py <파일...> --outdir <임시>  # cellSz 보존 실측
# est(쪽 나눔 추정) 드리프트 재보정이 필요하면: drift_probe.py (est vs PDF 실측 대조)
```

## 검사 항목 ID (tests/check_hwpx_quality.py)

| ID | 검사 | 잡는 결함 |
|---|---|---|
| S1–S3 | zip·mimetype / XML / manifest | 한글에서 안 열리는 파일 |
| S4 | U+FFFD | 인코딩 깨짐 |
| S5 | version.xml·settings.xml | OWPML 표준 패키지 구성 |
| F1 | 폰트 참조 무결성 | dangling fontRef (★※◆ 아이콘 폴백 위험) |
| F2 | charPr/paraPr/borderFill 참조 | 미정의 서식 참조 |
| F3 | 라틴 본문 폰트 | CO2·25℃가 고정폭(Consolas)으로 인쇄 |
| F4 | 목록 내어쓰기 | 두 줄 목록 항목이 글머리보다 왼쪽으로 튐 |
| F5 | 콜아웃 kind별 테두리색 | 성취기준/과제/교사노트가 구분 안 됨 |
| F6 | repeatHeader | 명렬표가 쪽 넘김에서 머리행 소실 |
| F7 | 표 폭 == 본문 폭 | 표·콜아웃 오른쪽 11% 여백 |
| F8 | 쪽번호 | 여러 장 학습지 순서 관리 불가 |
| F9 | 문서 끝 빈 문단 | 마지막 표 아래 커서 못 놓음 |
| C1 | 영어 크롬 | "Target standard" 등 잔존 |
| C2 | 마크다운 리터럴 | `**별표**` 그대로 인쇄 |
| C3 | 파이프 표 리터럴 | 마크다운 표가 텍스트로 인쇄 |
| P1/P2 | HTML↔HWPX 파리티 | 두 형식의 내용 어긋남(드리프트) |
| G1–G6 | (plugin 게이트 부분집합) | 렌더 직후 전달 차단선 |

## 교사 피드백 → 결함 ID 변환표

교사의 말은 그대로 루프에 들어가지 않는다 — 결함 ID로 번역해 1단계에 넣는다.
기존 ID에 안 맞으면 **새 검사 항목을 만들며 ID를 부여한다**(원칙 2).

| 교사 피드백 (예) | 번역 |
|---|---|
| "한글에서 안 열려요 / 깨져요" | S1–S4 + COM 실열림 재실행 |
| "표가 좁고 오른쪽이 비어요" | F7 |
| "글머리 기호 줄이 삐뚤어요" | F4 |
| "강조 상자가 다 똑같이 생겼어요" | F5 |
| "영어가 찍혀 나와요" | C1 (+ 새 문자열이면 검사 목록에 추가) |
| "별표가 그대로 보여요" | C2 |
| "표가 다음 장으로 넘어가며 제목 행이 사라져요" | F6 |
| "문제랑 답 칸이 다른 쪽에 있어요" | (신규 ID 부여 → 렌더러 emit_group 프로브 조정) |
| "미리보기(HTML)랑 한글 파일 내용이 달라요" | P1/P2 |
| "글꼴이 이상해요 / 영문만 달라 보여요" | F1/F3 |

## LLM-judge 확장 (evals/hwpx-format/)

자동 검사기가 못 보는 **시각 품질**(적정성 판단)은 `evals/hwpx-format/rubric.csv`
루브릭으로 LLM-judge 채점한다. 기존 evals 프레임(CSV 스키마·판정 JSON·
aggregate.py)을 그대로 쓴다. 판정 입력은 (a) 검사기 `--json` 리포트,
(b) HWPX 추출 텍스트, (c) 가능하면 한글 PDF 내보내기 스냅샷. 자동 검사가 fail 0을
만든 뒤에만 돌린다 — 계측기(자동)와 심사(판정)를 섞지 않는다.

## 캘리브레이션 경로와의 관계 (DESIGN.md ADR-4)

ADR-4의 "한글 직접 조판 기준 문서 → 실측 조판값(charPr/paraPr/borderFill)을
렌더러 상수에 굽기"는 이 루프의 **후속 회차**다: 교사가 한글에서 이상적으로 조판한
기준 문서 1부가 준비되면, 그 header.xml에서 상수를 추출해 `build_header_xml()`에
반영하고 루프를 한 바퀴 돌려 수렴을 확인한다. 이 루프의 검사기·게이트가 그 교체의
안전망이 된다.

## 회차 이력

| 회차 | 날짜 | 입력 | 결과 |
|---|---|---|---|
| 0 (기준선) | 2026-08-08 | 파일럿 14파일 (kordoc 6 + 신규 8) | **805건 FAIL** — F1 670, F6 35, S5 28, F5/F7/F8 각 14, F4 10, F3 8, F9 6, P1 6 |
| 1 | 2026-08-08 | 렌더러 20종 결함 수정 (본문 폭 49600, 폰트 참조, 내어쓰기, kind별 콜아웃, repeatHeader, 내용 기반 열폭, 쪽번호, version/settings, 한국어 크롬 발원지 이동, `_plain`, cards 가변 높이, number_line 눈금표, labeled_box, group 쪽나눔 프로브, columns 1×2 표, 문서 끝 문단) | **0건** — 17파일 PASS, DoD·smoke 통과, validate 19/19 VALID, 한컴 COM 실열림 19/19 PASS. kordoc 구형 6파일은 현 렌더러 재렌더로 대체(콜아웃 31개 증발·쓰기공간 문자열화 해소) |

| 2 | 2026-08-08 | 검사기 F10 신설(스타일 정의·참조·실사용) → 기준선 F10 38건(19파일 전부) | **0건** — 렌더러 hh:styles 7종(바탕글·문서 제목·제목 1/2/3·목록·부가 정보) 정의, 제목·목록·캡션 문단이 styleIDRef로 참조. DoD ×3·smoke·validate 19/19(경고 0)·COM 실열림 19/19 PASS |
| 3 | 2026-08-08 | 검사기 F11 신설(표 높이 선언 정합) + COM 라운드트립 실측(로컬 roundtrip_hwpx.py) | F11 0건(선언은 내부 정합 — 회귀 방지선으로 존치). **실측으로 후보 기각**: 974셀 라운드트립 드리프트 전부 0.0%, 고의 과소 선언(3pt) 프로브도 재저장 시 보존됨 → 한글은 cellSz를 "최소 높이 선언"으로 취급하고 재작성하지 않는다. 파일 수준 "hp:sz stale" 결함은 성립하지 않음. 실제 쪽수(COM PageCount) 전 파일 1~7쪽 정상 — 이 수치는 4회차 V4/V5 판정의 기초 자료 |
| 4 | 2026-08-08 | **evals/hwpx-format V1–V10 1차 실채점** — COM PDF 스냅샷(17파일 63쪽) + HTML 대조 + 자동 검사 리포트를 판정 입력으로, 패키지별 LLM-judge 5건(`evals/runs/2026-08-08/`) | **PASS 34 / FAIL 11 / skip 5 (75.6%)** — 자동 검사가 못 보는 시각 결함 4종 검출: V2 빈 답란 열이 라벨 열보다 좁음(2), V4 지시문-답란 쪽 분리(4), V5 큰 표 통째 밀림 대공백(4), V8 h1 구분선·그리기 상자 편측 존재(1) |
| 5 | 2026-08-08 | 4회차 fail 11건을 결함으로 번역 → 검사기 F12 신설(빈 답란 열폭, 기준선 9건) + 렌더러 근본 수정 | **확정 재채점 PASS 48 / FAIL 0 / skip 2 — 통과율 100%**(`evals/runs/2026-08-08-r5/`), 자동 층 0건 + 쪽 채움·고아 꼬리 실측 전 쪽 통과, DoD ×3·smoke·validate 19/19·COM 실열림 19/19. 수정: ① 데이터 표·괘선 답란을 어울림(treatAsChar=0)+셀 단위 쪽나눔으로 전환 — 한글이 행을 직접 나눠 V5 대공백 근본 해소, 머리행 반복(V9)이 실제로 동작 ② 제목·지시문-답란 동반을 est 추정이 아닌 keepWithNext(다음 문단과 붙임)로 — est 기반 강제 쪽나눔은 드리프트 실측(-706pt) 후 폐기 ③ 빈 답란 열 폭 우대(_col_widths) ④ h1 위 구분선 + HTML 무괘선 상자 정합(V8) ⑤ est 캘리브레이션(PDF 실측: USABLE 730pt, 머리부 97pt, CHARS_EST) ⑥ 4행 미만 표 분할 금지(고아 답줄 방지). 계측기 3종 신설(로컬): export_pdf, fill_check(쪽 하단 공백·고아 꼬리), drift_probe |

**일반화 시험 (2026-08-08, 5회차 종결 직후):** 루프가 파일럿 3종에 과적합되지
않았는지 확인하기 위해, 초등 과학 성취기준 102개에서 무작위 추첨한 [6과03-03]
(용해와 용액, 조사·공유형 — 기존 파일럿에 없던 수업 유형)으로 새 패키지
`pilot/random-elementary/`를 저작해 **첫 렌더본**을 전 층에 통과시켰다: 게이트·
DoD·검사기(S1~F12) 0건, validate 3/3, COM 실열림 3/3, 쪽 채움 실측 전 쪽,
V1–V10 실채점 **10/10 전 항목 PASS(skip 0)**. 이어서 같은 단원의 **차별화 4종**
(교사용 수업안 + 가/나/다 모둠 학습지, R1–R8 적용, `out-differentiation/`)도 첫
렌더본이 같은 전 층을 통과했다 — 검사기 0건, validate 4/4, COM 4/4, 쪽 채움 전 쪽,
실채점 **10/10 전 항목 PASS(skip 0, 조사표 쪽 넘김 머리행 반복 실측 포함)**.
집계는 `2026-08-08-r5`에 6·7번째 패키지로 포함(총 **68/68 = 100%**).

다음 회차 후보 (미해결):
- 캘리브레이션(위 절) — 기준 문서 대기 (est 상수는 5회차에 PDF 실측으로 1차 보정됨)
- 고아 절 제목: 나·다 모둠 p1 하단 '10분 사이에…' 제목이 내용 없이 홀로 남음 —
  5회차 판정자의 감점 아님 관찰. h1 keepWithNext가 어울림 표의 실제 위치를 못 보는
  잔여 사례로, V 루브릭에 항목을 신설할지부터 결정할 것(원칙 2)
