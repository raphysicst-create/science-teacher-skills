# 1단계 과학 파일럿 — 검증 기록

Task 6~8의 실측 기록과 Task 9 "확정 치환 규칙"의 재료. 시간순 append.

## Task 3 — 한글 렌더 스모크 테스트 (2026-08-01)

**결과: 통과.** 한글 본문·표 셀·콜아웃·faceted exit_ticket(teacher/student) 모두 docx에서 깨짐 없음 (U+FFFD 없음).

발견 사항:

1. **렌더러 영어 크롬 (동결 유지, 수정 안 함).** 렌더러가 하드코딩한 라벨이 한국어 문서에 영어로 나온다:
   - 성취기준 콜아웃: `⭐ [코드] — Target standard` (lesson_common.py의 `standard` 조립)
   - 교사 문서의 학생 과제 리드인: `Students see:` (lesson_common.py:306)
   - 대응: 1단계에서는 수용하고 기록만. 렌더러 최소 i18n 패치 여부는 3단계(렌더러를 어차피 만지는 단계)에서 결정. Task 10에서 사용자에게 보고.

2. **학년 밴드 감지 우회법 (확정 치환 규칙 후보).** `grade_number()`는 `grade 4`·`4th grade`·eyebrow 선두 숫자 패턴만 파싱 → `"중1"`은 감지 실패, 기본 프로필(answer_box 120pt)로 강등. 그러나 `shared.grade`에 영문 학년을 병기하면 감지된다:
   - 초3~6: `"초4 (Grade 4)"` → 3–5 밴드 (150pt, 국어형 답란은 줄노트 기본)
   - 중1~3: `"중1 (Grade 7)"` → 6–8 밴드 (130pt)
   - 고: `"고1 (Grade 10)"` → 9–12 밴드 (116pt)
   - 렌더러 무수정. eyebrow·문서 본문에는 한국어 학년만 쓰면 교사 눈에는 병기가 안 보인다 (grade는 meta로만 쓰임 — 단, 렌더 확인 필요: Task 7에서 meta 줄 노출 여부 실측).

3. **계획 대비 편차.** check_docx.py의 needle "성취기준"은 JSON 콘텐츠에 없는 단어였다(성취기준 콜아웃 라벨은 렌더러가 영어로 조립 — 위 1번). needle을 standard_text 실제 구절("과학적으로 탐구할 수 있다")로 교체.

4. **렌더 실행 경로.** Git Bash `python3`(3.14, WindowsApps)에서 render_all.sh 자체 pip 설치 경로가 정상 작동. 우회 불필요.

## Task 4 — SKILL.md 한국화 diff (2026-08-01)

계획된 12지점 + 추가 2곳(5b 구두 수업 안내 예시, 5c 인쇄물 제안 예시 — "교사 대면 문구 전부
한국어화" 원칙의 동일 적용). diff 규모 64+/59- (471줄 중) — 구조·단계·밀도 규칙 전부 무수정.
잔여 영문 US 흔적은 SPDX 표기(유지 의무)뿐.

## Task 6 — 중등 MCP 실호출 검증 (2026-08-01)

도구 6종 전부 실호출 확인. 파일럿 #1 소재 확보: **[9과12-01]** (과학 > 식물과 에너지,
"광합성 과정을 이해하고, 환경 요인과 광합성의 관계를 탐구하는 실험을 설계할 수 있다.")
— 주제 3개(기본 + 탐구 설계와 자료 해석 / 증거 기반 설명과 적용 facet).

문서 보정 5건 (curriculum-kr-mcp.md):
1. `search_standards` 파라미터는 `keyword`가 아니라 **`query`** (+ `gradeBand`: "7-9"/"10"/"10-12").
2. 원문 필드는 **`officialText`**. `summary`는 기계 생성(`summaryKind: mechanical-derivative`) — 인용 금지 명시.
3. `get_prerequisites`: **선수 edge 없는 성취기준이 흔함**(`directEdges: []`) — "치명적 실패" 규정을
   "edge가 있는데 누락 = 실패 / 없으면 훈련 지식 + 추정 표시"로 보정 (DESIGN §5-2 정합).
4. `get_topic`: 필드 실명 `evidence[]`·`assessmentPrompts[]`·`facetKey`. 주제가 자동 분해 후보 단위라
   서술이 템플릿형 → "직접 사용"을 "시드로 재진술"로 보정.
5. `get_transitions`: 파라미터 `standardCode`/`topicId`, 반환 `asFrom`/`asTo`. 175건만 수록 — 빈 결과
   정상, 없으면 심화 연계 문장 생략 규정 추가.

[9과12-01] 실측: 선수 edge 0, 전이 0 — 파일럿 #1은 "추정 선수 표시" 경로와 "심화 연계 생략"
경로를 실제로 밟게 된다 (보정 규정의 실전 검증이 됨).

초등 서버는 세션 미연결 — Task 8의 stdio 프로브로 대체 검증.
