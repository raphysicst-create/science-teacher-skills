# ko12-teacher-skills 일괄 포팅 스펙 (Claude Code용)

과학 파일 2개(`curriculum-kr-mcp.md`, `science.md`)가 검증된 뒤 실행한다.
검증된 과학 파일이 나머지 과목의 **골든 레퍼런스**다 — 배치 작업은 창작이 아니라
과학판에서 확립된 치환 규칙의 기계적 적용이어야 한다.

## 0. 사전 조건

- [x] `science.md` 실제 수업 1회 이상 생성 테스트 완료 — 중학교 [9과12-01] · 초등 [4과10-02] 각 1회 (2026-08-01)
- [x] `curriculum-kr-mcp.md` 호출 시퀀스가 실 MCP에서 작동 확인 — 중등 6종 세션 연결 호출,
      초등 9종 stdio 프로브. `get_topic`의 관찰 증거 → look-for 매핑, `get_prerequisites(depth:"all")` 포함
- [x] 원본 대비 수정 결정 사항을 이 파일 하단 "확정 치환 규칙"에 기록

## 1. 저장소 골격

```
ko12-teacher-skills/
  plugin/
    .claude-plugin/plugin.json      # name: ko12-teacher-skills, author 수정
    .mcp.json                       # 아래 2절
    skills/
      ko12-lesson-planning/
        SKILL.md                    # 아래 3절
        references/
          curriculum-kr-mcp.md      # 검증본 (learning-commons-kg.md 대체)
          science.md                # 검증본
          math.md                   # 배치 대상
          korean.md                 # 배치 대상 (원본 ela.md 대응)
          social_studies.md         # 배치 대상
          example_lesson.json       # 한국어 예시로 재작성
        scripts/                    # 원본 그대로 (docx/html 렌더 유지)
      ko12-lesson-differentiation/  # 2차 배치 (planning 완료 후)
  NOTICE                            # Anthropic + Learning Commons 표기 유지
  LICENSE                           # Apache-2.0 유지
```

## 2. .mcp.json

```json
{
  "mcpServers": {
    "curriculum-kr-secondary": {
      "command": "npx", "args": ["-y", "korean-secondary-learning-map-mcp"]
    },
    "curriculum-kr-elementary": {
      "command": "npx", "args": ["-y", "korean-elementary-learning-map-mcp"]
    }
  }
}
```

kordoc은 3단계(HWPX 렌더링) 전까지 번들하지 않는다 — 렌더 스크립트에서 CLI 직접 호출
방식이 확정되면 번들 불필요할 수 있음.

## 3. SKILL.md 수정 (치환 diff, 재작성 아님)

- 언어: 교사 대면 문구 전부 한국어화. 단계 구조·순서·draft offer 메커니즘은 유지.
- Step 0 subject 라우팅: math/ela/science/social_studies → 수학/국어/과학/사회
  (국어 신호: 읽기·쓰기·문법·문학·화법; 사회 신호: 역사·지리·일반사회·경제).
- Step 0 connector 체크: `find_standard_statement` → `search_standards` 등 학습맵 도구명.
- Step 2: `learning-commons-kg.md` → `curriculum-kr-mcp.md`.
- Copyright guardrail: IM/OpenSciEd 문구 → "검정 교과서의 활동·지문·삽화·문항을 재현하지
  않는다. 교사가 출판사를 확언하지 않았으면 출판사명을 산출물·채팅 어디에도 쓰지 않는다."
- 미연결 푸터 문구: curriculum-kr-mcp.md 하단의 한국어 푸터로 통일.

## 4. 과목별 치환 규칙 (science.md에서 확립된 것)

모든 과목 공통:
1. State/jurisdiction 감지 → 삭제 (국가 단일 교육과정)
2. 미국 커리큘럼 분기(IM, OpenSciEd, …) → 삭제, 교과서 출판사 중립 원칙으로 대체
3. Grade band → 학년군: 초3–4 / 초5–6 / 중1–3 / 고(공통·선택). 초1–2 특례는 과목별 확인
   (국어·수학은 초1–2 존재, 사회·과학은 통합교과)
4. 시간 기본값: 초 40 / 중 45 / 고 50분
5. 3차원 목표 프레임 → 내용 체계 3범주 (지식·이해 / 과정·기능 / 가치·태도)
6. 커리큘럼 자료 KG 호출 → 생략 (curriculum-kr-mcp.md 6단계)
7. 오개념 → 훈련 지식 + 외부 오개념 MCP 연결 시 우선 (동 5단계)
8. lesson.json 매핑·스크립트 스키마 → 무수정 유지 (렌더러 호환성)

과목별 추가 판단 지점 (배치 실행 시 사람 확인 필요, 자동 결정 금지):
- **수학**: CCSS-M 관행(SMP) → 2022 수학과의 교과 역량/과정·기능 대응 확정.
  IM 문제 유형 분류(unknown positions 등) → 유지할지 한국 교과서 관행 문항 유형으로
  대체할지.
- **국어**: ela.md는 파닉스·독해 지문 선정 등 영어 고유 구조가 깊다. 4과목 중 치환이
  아니라 **부분 재저작**이 필요한 유일한 파일. 2022 국어과 6개 영역(듣기·말하기 /
  읽기 / 쓰기 / 문법 / 문학 / 매체) 구조로 골격 재편.
- **사회**: C3 inquiry arc → 유지 가능 (탐구 중심 사회과와 정합) 단 명칭·인용 제거.
  역사/지리/일반사회 하위 분기 추가 여부.

## 5. 실행 순서

1. 골격 생성 + SKILL.md diff 적용 + 과학 검증본 투입 → 커밋
2. math.md 치환 → 사람 확인 지점만 질문 → 커밋
3. social_studies.md 치환 → 커밋
4. korean.md 재저작 (가장 무거움, 마지막) → 커밋
5. example_lesson.json 한국어 재작성 (과학 소재 권장 — 검증된 레퍼런스와 정합) → 커밋
6. 초등·중등 MCP 실연결 상태에서 과목당 1회 생성 스모크 테스트
7. README.md 작성 (원본 attribution + 데이터 출처 명시) → npm/GitHub 공개

## 확정 치환 규칙 (과학 파일럿 검증 완료 — 2026-08-01)

배치 작업은 아래를 **기계적으로 적용**한다. 검증 근거는 `docs/superpowers/pilot-notes.md`.

### A. SKILL.md 치환 지점 (14곳 — 이 목록이 diff의 전부다)

과학 파일럿에서 확정. 2단계에서는 ①만 다시 손대고 나머지는 그대로 둔다.

1. frontmatter `name`(`ko12-lesson-planning`) + `description` 한국어 전체 — **2단계에서
   "과학 전용 프리뷰" 문구를 제거하고 4과목으로 되돌린다**
2. SPDX 주석에 contributors 줄 + 원본 출처 줄
3. 제목 + 도입부의 KG 언급 → 학습맵 MCP
4. "Keeping the teacher posted" 예시 문장
5. Step 0.1 과목 신호 4줄 (한국 코드 체계) + 레퍼런스 매핑 — **2단계에서 4과목 전부 활성화**
6. Step 0.2 Curriculum → **Textbook** (검정 교과서 중립)
7. Step 0.3 Connector 도구명 (`search_standards`, `get_standard`)
8. Step 2 본문 (`curriculum-kr-mcp.md` + 한국어 미연결 푸터)
9. Copyright guardrail → 저작권 가드레일 (출판사명 금지)
10. Step 4 draft offer 질문·선택지
11. Step 4 후속 선택지 2개
12. Step 5 plain-language 예시 + "워드 문서"
13. Step 5 framework 약어 금지 예시 (범주명)
14. 5b 구두 수업 안내 / 5c 인쇄물 제안·만족도 질문·반복 옵션

**건드리지 않은 것**(회귀 위험): Step 1 전체, Step 3 전체, Step 5의 밀도 규칙 · Everything
matches · Document integrity · 5a 스키마 · 5b 렌더 명령 · 5d · 5e. diff 규모 64+/59- (471줄 중).

### B. MCP 응답 형식 (문서가 가정하면 안 되는 것)

| 항목 | 중등 | 초등 |
|---|---|---|
| 도구 수 | 11 | 9 (`get_transitions` 없음) |
| 검색 파라미터 | `query`, `schoolLevel`, `gradeBand`("7-9"/"10"/"10-12"), `subject`, `domain` | `query`, `gradeBand`("1-2"/"3-4"/"5-6"), `subject`, `domain` |
| 검색 결과 요약 필드 | `summary` | **`focus`** (잘림) |
| `get_standard` | `subject` 파라미터 있음(공유 코드용) | 없음 |
| 원문 | `officialText` = verbatim (`sourceLocator`에 PDF 쪽·sha256) | `officialText` = **조립값**, `sourceTextIncluded: false` |
| 선수관계 | 희소 (공식 근거만, 213건) | 조밀 (1,894건) |

- `summary`(중등)는 `summaryKind: "mechanical-derivative"` — **인용 금지**. 원문은 `officialText`뿐.
- **초등 성취기준은 verbatim이라고 말하지 않는다.** 수업안에 출처 확인 문구를 단다.
- 선수 edge가 없으면 훈련 지식으로 쓰되 "추정" 표시 (치명적 실패 아님). 전이가 없으면 심화 연계 문장 생략.

### C. lesson.json 작성 규칙 (렌더러 무수정 전제)

- **`shared.grade`는 영문 학년을 먼저 쓴다** — `"Grade 8 · 중학교 2학년"`. 렌더러가 첫 번째
  숫자로 답란 크기를 정하므로 `"중학교 2학년"`만 쓰면 2학년으로 읽혀 답란이 초등 저학년 크기가 된다.
  이 값은 산출물에 출력되지 않는다 (교사가 보는 학년은 각 문서 `meta`에 한국어로 따로 쓴다).
- `phase_header` 분 합계 == `shared.duration`을 **반드시** 맞춘다.
- 성취기준 원문은 수업안에 정확히 1회 (`from_shared: standard`). 다른 곳은 코드로만 참조.
- 검증: `python tests/check_lesson.py <lesson.json> <outdir> --official "<officialText>"`

### D. 렌더러 영어 크롬 (1단계에서 수용, 3단계 재검토)

렌더러가 하드코딩한 영어 라벨이 한국어 문서에 그대로 나온다:
- 성취기준 콜아웃 제목 `— Target standard`
- 교사 문서의 학생 과제 리드인 `Students see:`

1단계는 렌더러 동결(DESIGN §5-5)이므로 수정하지 않았다. HWPX 어댑터를 만드는 **3단계에서
최소 i18n 패치를 함께 결정**한다 (두 문자열 상수화가 전부).

### E. 실행 환경

- Git Bash `python3`(3.14, WindowsApps)에서 `render_all.sh`의 자체 pip 설치 경로 정상 작동. 우회 불필요.
- 콘솔 한글 깨짐은 Git Bash cp949 출력 문제이며 docx 내용과 무관 (U+FFFD 검사로 확인).

### F. 과목별 추가 판단 지점 (2단계에서 사람 확인 — 자동 결정 금지)

§4의 3개 항목(수학·국어·사회) 그대로 유효. 여기에 파일럿에서 나온 항목 하나를 더한다:
- **성취기준 유형 분기**(설명·모형형 / 실험 설계형 / 자료 해석형)는 과학에서 확립했다. 수학·사회·국어에서
  이 분기가 어떤 형태로 대응하는지는 과목별 판단이 필요하다 (예: 국어의 수용/생산 활동 구분).
