# 2단계 HWPX 어댑터 — 구현 계획 (render_lesson_hwpx.py)

**전제**: ADR-4 개정판(2026-08-01). kordoc 마크다운 경유는 실측으로 기각됐고,
lesson.json → OWPML(section0.xml) **직접 생성**으로 간다.
**DoD** (DESIGN §7 2단계): 표 포함 수업안이 한글에서 깨짐 없이 열림, docx 병행 유지.

## 설계 원칙

1. **치수의 단일 소스는 원본 렌더러의 pt 명세.** lesson_common.py의 학년 밴드 프로필
   (answer_box 초3–5 150pt / 중 130pt / 고 116pt)과 보정본 실측값(설계표 108pt,
   그리기표 74pt, 그림칸 150pt, 상단 여백 64.4pt)을 코드 상수로 승계한다. 1pt = 100 (hp:cellSz).
2. **기존 파일 무수정.** render_all.sh·render_documents.py·lesson_common.py는 건드리지
   않는다. 어댑터는 새 파일 `render_lesson_hwpx.py`(+ 필요시 `render_all_hwpx.sh`)로만 추가.
   입력 인터페이스는 render_documents.py와 동일한 lesson.json (`shared` + `documents[]`).
3. **오리지널 코드만 커밋.** HWPX 패키지 스켈레톤(mimetype·version.xml·settings.xml·
   header.xml)은 OWPML(KS X 6101) 최소 구성으로 직접 작성한다. `.claude/skills/hwpx/`
   툴체인(라이선스 미표기 서드파티)은 로컬 QA로만 쓰고 코드·템플릿을 복사하지 않는다.
4. **표준 라이브러리만.** zipfile + xml.etree(또는 문자열 템플릿)로 생성 — 스킬 배포 환경에
   추가 의존성을 만들지 않는다 (lxml·pywin2는 로컬 검증에만 쓰임).

## 블록 → OWPML 매핑 (초안 — Task 0에서 확정)

| lesson.json 블록 | OWPML 대응 | 비고 |
|---|---|---|
| h1/h2/h3, phase_header | `hp:p` + charPr 크기·굵기 위계 | phase_header는 분(分) 병기 |
| text, list, labeled | `hp:p` (목록은 문단 나열로 근사) | |
| callout (성취기준 등) | 1×1 `hp:tbl` + borderFill | **미해결 → 이번에 구현** |
| table / data_table | `hp:tbl` + 헤더 행 음영(borderFill) | 음영도 미해결 → 구현 |
| fill_table | `hp:tbl` + 빈 행 `hp:cellSz` height 고정 | 설계표 10800, 관찰표 7400 |
| answer_box | 1열 `hp:tbl` + 밴드 프로필 height | 그림칸 15000 |
| group | 쪽 나눔 회피: 잔여 공간 < 블록 높이 합이면 `pageBreak="1"` | |
| 큰 고정높이 표 | 표 앞 문단에 `hp:p pageBreak="1"` (treatAsChar 표는 행 분할 불가) | 보정 실측 교훈 |
| number_line | **미정** — 1×N 표 근사 vs 생략+안내 문구 | Task 0에서 결정 |
| 이모지 (📌·✋) | `※ [라벨]` 예방 치환 계승 (실측 미확인 상태 유지) | |
| faceted teacher/student | docx 렌더와 동일한 전개 순서 승계 | |

## 작업 순서 (커밋 단위)

- **Task 0 — 실사.** lesson_common.py의 블록 어휘·전개 순서 전수 목록화, 보정본
  `pilot/*/out/*.hwpx`의 section0.xml에서 실제 쓰인 XML 패턴 추출(참조용 — 복사 아님,
  kordoc 산출물 구조라 라이선스 문제 없음). number_line 대응 결정.
- **Task 1 — 스켈레톤 + 문단.** 빈 문서 + 헤딩/문단만으로 lesson_plan 생성 →
  구조 검증 + 한컴 실열림 통과.
- **Task 2 — 표 계열.** table/fill_table/answer_box + cellSz height →
  student_materials 통과, 답란 높이 실측 대조.
- **Task 3 — 콜아웃·음영·쪽 나눔.** borderFill 정의 + pageBreak 규칙 →
  lesson_plan·observation_template 전체 통과.
- **Task 4 — 전수 검증.** 파일럿 3종(lesson.json) × 문서 3종 = 9 hwpx 생성,
  로컬 툴체인 `validate → validate --layout → 한컴 COM 실열림·쪽수` 전수 실행.
  기준: 보정본 실측값과 치수 일치, 쪽수 편차 ±1 이내, U+FFFD 0건.
- **Task 5 — 문서화.** DESIGN §7 2단계 완료 기록, README에 HWPX 산출 안내,
  render_all_hwpx.sh(선택) 추가.

## 검증 프로토콜 (각 Task 공통)

1. `tests/smoke/korean_lesson.json` → 빠른 회귀 (구조 검증만)
2. 로컬 툴체인 (`.claude/skills/hwpx/scripts/`): `validate.py` → `validate.py --layout`
   (`body_paragraph_without_visible_indent` 경고는 무시 대상 — pilot-notes 규정)
3. 한컴 COM 실열림 + 쪽수 실측 (Task 2 이후 필수)
4. 최종: 한글에서 PDF 내보내기 → 보정본 PDF와 육안·pymupdf 대조 (Task 4)

## 리스크

- **borderFill은 header.xml 참조 체계** — 셀 속성만으로 안 되고 refList 등록이 필요.
  스켈레톤 설계 때 미리 자리를 잡는다 (Task 1에서 borderFill 2종 예약).
- **한컴 COM은 이 머신 전용 검증** — CI 불가. 결정론 검증(validate)과 분리 기록.
- **treatAsChar 표의 행 분할 불가**는 OWPML 사양 제약 — 쪽 나눔 규칙으로만 대응 가능.
