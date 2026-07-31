# ko12-teacher-skills 일괄 포팅 스펙 (Claude Code용)

과학 파일 2개(`curriculum-kr-mcp.md`, `science.md`)가 검증된 뒤 실행한다.
검증된 과학 파일이 나머지 과목의 **골든 레퍼런스**다 — 배치 작업은 창작이 아니라
과학판에서 확립된 치환 규칙의 기계적 적용이어야 한다.

## 0. 사전 조건

- [ ] `science.md` 실제 수업 1회 이상 생성 테스트 완료 (중학교 + 초등 각 1회 권장)
- [ ] `curriculum-kr-mcp.md` 호출 시퀀스가 실 MCP에서 작동 확인 (특히 `get_topic`의
      관찰 증거 → look-for 매핑, `get_prerequisites(depth:"all")`)
- [ ] 원본 대비 수정 결정 사항을 이 파일 하단 "확정 치환 규칙"에 기록

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

## 확정 치환 규칙 (과학 검증 후 기록)

- (검증하며 채울 것)
