# ko12-teacher-skills 1단계 과학 파일럿 — 구현 계획

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Anthropic `k12-teacher-skills` v0.6.0의 lesson-planning 스킬을 한국 2022 개정 교육과정 체제로 이식한 "과학 전용 프리뷰" 플러그인을 만들고, 실제 학습맵 MCP 연결 상태에서 중학교·초등 수업 각 1회 생성으로 초안 레퍼런스 2종(curriculum-kr-mcp.md, science.md)을 검증한다.

**Architecture:** 원본 플러그인 캐시(`C:\Users\22\.claude\plugins\cache\k12-teacher-skills\k12-teacher-skills\0.6.0\`)에서 파일을 복사해 골격을 만들고, 치환 3지점(DESIGN.md §3)만 바꾼다 — (A) KG 레퍼런스 → 학습맵 호출 시퀀스 파일, (B) science.md → 한국판(이미 초안 존재), (C) 렌더러는 무수정(HWPX는 3단계). SKILL.md는 최소 diff(ADR-6): 구조·단계는 유지하고 교사 대면 문구·도구명·가드레일만 바꾼다.

**Tech Stack:** Claude Code 플러그인(SKILL.md + references + scripts), Python 3.12 + python-docx 1.1.2(렌더), Git Bash(render_all.sh), MCP 서버 2종(npm: `korean-secondary-learning-map-mcp@0.1.0`, `korean-elementary-learning-map-mcp@0.5.1`), git.

## Global Constraints

- **Canonical 스펙은 `DESIGN.md`** — 구현과 충돌하면 어긋난 채 두지 않는다 (문서를 고치거나 구현을 고친다).
- **성취기준 원문은 verbatim** — 학습맵이 반환한 공식 원문을 바꿔 쓰지 않는다 (DESIGN §5-1).
- **산출 스키마·렌더러 동결** — `lesson.json` 스키마, `scripts/` 전체는 3단계 전까지 무수정 (DESIGN §5-5).
- **SKILL.md는 diff, 재작성 금지** — 단계 구조·순서·draft offer 메커니즘·밀도 규칙을 유지 (ADR-6).
- **교과서 출판사 중립** — 검정 교과서의 활동·지문·삽화·문항 재현 금지, 교사가 확언하지 않은 출판사명 언급 금지 (DESIGN §5-4).
- **라이선스** — Apache-2.0 유지, 모든 파생 파일에 SPDX 헤더(Anthropic, PBC + Learning Commons + ko12-teacher-skills contributors), NOTICE 유지 (DESIGN §8).
- **플러그인 이름은 `ko12-teacher-skills`, 스킬 이름은 `ko12-lesson-planning`** — 폴더명(`k12-teachers-skills`)은 바꾸지 않는다(이름은 plugin.json이 규정).
- 경로 표기: bash 명령은 `/c/Users/22/...`, PowerShell·에디터 도구는 `c:\Users\22\...`. 저장소 루트 = `c:\Users\22\Desktop\Y-claude\k12-teachers-skills`. 원본 캐시 = `C:\Users\22\.claude\plugins\cache\k12-teacher-skills\k12-teacher-skills\0.6.0`.
- 확인된 환경 사실: PowerShell `python` = 3.12(python-docx 1.1.2 있음), Git Bash `python3` = 3.14(WindowsApps, python-docx 없음 — render_all.sh가 자체 pip 설치를 시도함). Task 2의 스모크 테스트가 이 경로를 검증한다.

---

### Task 1: git 저장소 초기화 + 설계 문서 베이스라인 커밋

**Files:**
- Create: `.gitignore`
- Commit: `DESIGN.md`, `BATCH_SPEC.md`, `curriculum-kr-mcp.md`, `science.md`, `docs/superpowers/plans/2026-08-01-phase1-science-pilot.md`

**Interfaces:**
- Produces: git 저장소(브랜치 `main`), 이후 모든 태스크가 커밋 단위로 진행.

- [ ] **Step 1: git init + 기본 브랜치 확인**

```bash
cd /c/Users/22/Desktop/Y-claude/k12-teachers-skills
git init -b main
```

- [ ] **Step 2: .gitignore 작성**

```gitignore
__pycache__/
*.pyc
pilot/*/out/
tests/smoke/out/
```

- [ ] **Step 3: 베이스라인 커밋**

```bash
git add .gitignore DESIGN.md BATCH_SPEC.md curriculum-kr-mcp.md science.md docs/
git commit -m "docs: 1단계 파일럿 설계 문서 베이스라인

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

- [ ] **Step 4: `git log --oneline`으로 커밋 1개 확인**

---

### Task 2: 플러그인 골격 생성 — 원본 복사 + plugin.json + .mcp.json + 영어 원본 렌더 스모크 테스트

**Files:**
- Create: `plugin/.claude-plugin/plugin.json`, `plugin/.mcp.json`, `LICENSE`(루트), `NOTICE`(루트)
- Copy (원본 캐시 → 저장소, 무수정):
  - `skills/k12-lesson-planning/SKILL.md` → `plugin/skills/ko12-lesson-planning/SKILL.md` (Task 4에서 diff)
  - `skills/k12-lesson-planning/LICENSE` → `plugin/skills/ko12-lesson-planning/LICENSE`
  - `skills/k12-lesson-planning/references/example_lesson.json` → 동일 상대 경로
  - `skills/k12-lesson-planning/references/NOTICE` → 동일 상대 경로
  - `skills/k12-lesson-planning/scripts/` 전체(6개 파일: `lesson_common.py`, `render_all.sh`, `render_documents.py`, `render_lesson_docx.py`, `render_lesson_html.py`, `theme.css`) → 동일 상대 경로
- **복사하지 않는 파일 (의도적):** `references/learning-commons-kg.md`(→ curriculum-kr-mcp.md로 대체), `references/{math,ela,science,social_studies}.md`(미국 pedagogy — 과학은 한국판 초안이 대체, 나머지는 2단계에서 재작성), `k12-lesson-differentiation/` 스킬 전체(2차 포팅), 원본 `.mcp.json`(미국 에듀테크 9종 — 학습맵 2종으로 대체)

**Interfaces:**
- Produces: BATCH_SPEC §1 골격. `bash plugin/skills/ko12-lesson-planning/scripts/render_all.sh <json> <outdir>`가 이 머신에서 docx를 생성함을 보장.

- [ ] **Step 1: 디렉터리 생성 + 원본 복사**

```bash
cd /c/Users/22/Desktop/Y-claude/k12-teachers-skills
SRC="/c/Users/22/.claude/plugins/cache/k12-teacher-skills/k12-teacher-skills/0.6.0/skills/k12-lesson-planning"
mkdir -p plugin/.claude-plugin plugin/skills/ko12-lesson-planning/references plugin/skills/ko12-lesson-planning/scripts
cp "$SRC/SKILL.md" "$SRC/LICENSE" plugin/skills/ko12-lesson-planning/
cp "$SRC/references/example_lesson.json" "$SRC/references/NOTICE" plugin/skills/ko12-lesson-planning/references/
cp "$SRC/scripts/"* plugin/skills/ko12-lesson-planning/scripts/
cp "$SRC/LICENSE" LICENSE
cp "$SRC/references/NOTICE" NOTICE
```

- [ ] **Step 2: `plugin/.claude-plugin/plugin.json` 작성 (정확히 이 내용)**

```json
{
  "name": "ko12-teacher-skills",
  "version": "0.1.0-preview.1",
  "description": "한국 2022 개정 교육과정 기반 수업 설계 스킬 (과학 전용 프리뷰). Anthropic k12-teacher-skills의 한국 이식판 — 성취기준·선수관계·세부 주제는 한국 교육과정 학습맵 MCP(초등·중등)에서 가져온다.",
  "author": {
    "name": "ko12-teacher-skills contributors"
  }
}
```

- [ ] **Step 3: `plugin/.mcp.json` 작성 (정확히 이 내용 — npm 패키지명 확인 완료: secondary 0.1.0, elementary 0.5.1)**

```json
{
  "mcpServers": {
    "curriculum-kr-secondary": {
      "command": "npx",
      "args": ["-y", "korean-secondary-learning-map-mcp"]
    },
    "curriculum-kr-elementary": {
      "command": "npx",
      "args": ["-y", "korean-elementary-learning-map-mcp"]
    }
  }
}
```

- [ ] **Step 4: 영어 원본으로 렌더 스모크 테스트 (치환 전 기준선 — 스크립트가 이 머신에서 도는지)**

```bash
cd /c/Users/22/Desktop/Y-claude/k12-teachers-skills
mkdir -p tests/smoke/out
bash plugin/skills/ko12-lesson-planning/scripts/render_all.sh \
  plugin/skills/ko12-lesson-planning/references/example_lesson.json tests/smoke/out/en
ls tests/smoke/out/en
```

Expected: `documents[]`의 각 id마다 `.docx` + `.html`, 그리고 `lesson.json`. 오류 시 예상 원인은 Git Bash `python3`(3.14)에 python-docx가 없고 자체 pip 설치도 실패한 경우 — 그때의 해결책: `python3 -m pip install python-docx==1.1.2`를 먼저 수동 실행하고 재시도. 그래도 실패하면 `render_all.sh`를 고치지 말고(동결) PowerShell에서 `python plugin/skills/ko12-lesson-planning/scripts/render_documents.py <json> --format both --outdir <out>`을 직접 호출하는 우회를 확정 치환 규칙(Task 9)에 기록한다.

- [ ] **Step 5: 커밋**

```bash
git add plugin/ LICENSE NOTICE
git commit -m "feat: 플러그인 골격 — 원본 v0.6.0 복사 + 학습맵 MCP 번들

원본: anthropics/k12-teacher-skills v0.6.0 (Apache-2.0)
복사 제외: learning-commons-kg.md, 미국 과목 레퍼런스 4종, differentiation 스킬(2차), 미국 에듀테크 .mcp.json

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 3: 한글 콘텐츠 렌더 스모크 테스트 (렌더러 동결 상태에서 한글·표·grade 값 검증)

**Files:**
- Create: `tests/smoke/korean_lesson.json`, `tests/smoke/check_docx.py`

**Interfaces:**
- Consumes: Task 2의 렌더 파이프라인.
- Produces: "렌더러가 한글 텍스트·한글 표·`grade: "중1"` 값을 깨짐 없이 docx로 낸다"는 검증 결과. 실패 시 파일럿 전에 리스크가 드러난다.

- [ ] **Step 1: `tests/smoke/korean_lesson.json` 작성 (정확히 이 내용 — 스키마의 주요 블록 타입을 한글로 커버)**

```json
{
  "shared": {
    "grade": "중1",
    "subject": "과학",
    "duration": 45,
    "standard_code": "[9과01-01]",
    "standard_text": "(스모크 테스트용 임시 문장) 과학의 탐구 과정을 이해하고, 일상생활의 문제를 과학적으로 탐구할 수 있다.",
    "exit_ticket": {
      "teacher": "수합 후 이해함 / 거의 / 재지도 필요 3칸으로 분류한다.",
      "student": "오늘 관찰한 현상을 한 문장으로 설명해 보세요."
    }
  },
  "documents": [
    {
      "id": "lesson_plan",
      "audience": "teacher",
      "eyebrow": "과학 · 중1 · 45분",
      "title": "한글 렌더링 스모크 테스트 — 수업안",
      "sections": [
        {
          "heading": "한눈에 보기",
          "blocks": [
            { "type": "from_shared", "key": "standard" },
            { "type": "paragraph", "text": "현상 던지기(10분) → 탐구 활동(20분) → 논증 토의(10분) → 형성 확인(5분)." },
            { "type": "table", "headers": ["단계", "분", "핵심"], "rows": [["현상 던지기", "10", "설명하지 않고 제시"], ["탐구 활동", "20", "같게 할 것 / 다르게 할 것 확인"]] },
            { "type": "callout", "kind": "teacher-note", "label": "주의", "text": "학생이 증거를 다루기 전에 결론을 내려주지 않는다." }
          ]
        },
        {
          "heading": "정리 문항",
          "blocks": [ { "type": "from_shared", "key": "exit_ticket" } ]
        }
      ]
    },
    {
      "id": "student_materials",
      "audience": "student",
      "eyebrow": "과학 탐구",
      "title": "무엇이 보이나요?",
      "sections": [
        {
          "heading": "탐구하기",
          "blocks": [
            { "type": "callout", "kind": "student-task", "label": "과제 1", "text": "관찰한 것을 그림과 낱말로 기록해 보세요." },
            { "type": "fill_table", "headers": ["관찰한 것", "궁금한 점"], "blank_rows": 3 },
            { "type": "answer_box", "ruled": true },
            { "type": "from_shared", "key": "exit_ticket" }
          ]
        }
      ]
    }
  ]
}
```

- [ ] **Step 2: `tests/smoke/check_docx.py` 작성 (정확히 이 내용)**

```python
"""렌더된 docx의 한글 무결성 검사: U+FFFD 없음 + 핵심 한글 문자열 존재."""
import glob
import sys

from docx import Document


def all_text(path):
    doc = Document(path)
    parts = [p.text for p in doc.paragraphs]
    for tbl in doc.tables:
        for row in tbl.rows:
            for cell in row.cells:
                parts.append(cell.text)
    return "\n".join(parts)


def main(outdir):
    paths = sorted(glob.glob(f"{outdir}/*.docx"))
    assert paths, f"no docx in {outdir}"
    combined = ""
    for p in paths:
        text = all_text(p)
        assert "\ufffd" not in text, f"replacement character in {p}"
        combined += text
        print(f"ok: {p} ({len(text)} chars)")
    for needle in ["성취기준", "탐구", "무엇이 보이나요", "설명하지 않고 제시"]:
        assert needle in combined, f"missing: {needle}"
    print("korean smoke test passed")


if __name__ == "__main__":
    main(sys.argv[1])
```

- [ ] **Step 3: 렌더 실행 → 검사 실행**

```bash
cd /c/Users/22/Desktop/Y-claude/k12-teachers-skills
bash plugin/skills/ko12-lesson-planning/scripts/render_all.sh tests/smoke/korean_lesson.json tests/smoke/out/ko
python3 tests/smoke/check_docx.py tests/smoke/out/ko
```

Expected: `korean smoke test passed`. (python3에 python-docx가 없으면 PowerShell `python tests/smoke/check_docx.py tests/smoke/out/ko`로 실행.)

- [ ] **Step 4: 육안 확인 메모** — `tests/smoke/out/ko/lesson_plan.docx`를 열지 못하는 환경이므로, `answer_box`가 `grade: "중1"`(미국 밴드 문자열이 아님)에서 어떤 높이 기본값을 잡는지 html 쌍둥이(`student_materials.html`)에서 확인하고, 이상(0 높이·오류)이 있으면 BATCH_SPEC "확정 치환 규칙"에 "grade 값과 answer_box 밴드 감지" 항목으로 기록한다. 렌더러는 고치지 않는다(동결).

- [ ] **Step 5: 커밋**

```bash
git add tests/
git commit -m "test: 한글 콘텐츠 렌더 스모크 테스트

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 4: SKILL.md 한국화 diff (구조 유지, 문구·도구명·가드레일 치환)

**Files:**
- Modify: `plugin/skills/ko12-lesson-planning/SKILL.md`

**Interfaces:**
- Consumes: Task 2가 복사한 원본 SKILL.md (471줄).
- Produces: Step 0이 과학으로 라우팅하고 `references/curriculum-kr-mcp.md`·`references/science.md`를 가리키는 오케스트레이터. Task 7·8의 파일럿이 이 파일을 따른다.

원칙: 지시문 산문(영어)은 그대로 두고, 아래 **12개 지점만** 바꾼다. 각 지점의 새 텍스트는 아래에 그대로 쓴다 (따로 창작하지 않는다).

- [ ] **Step 1: frontmatter — name과 description 교체**

`name: k12-lesson-planning` → `name: ko12-lesson-planning`

description 전체를 다음으로 교체:

```yaml
description: >
  수업안·학생 자료·관찰 템플릿을 만든다. 학년·과목·주제·성취기준·차시 분량에 대해 교사에게
  무엇이든 묻기 전에 이 스킬을 먼저 로드할 것. 한국 초·중·고 교사가 새 수업을 만들 때 사용 —
  학년이나 주제가 아직 안 나왔어도 로드한다. 채점, 루브릭, 평가 피드백, 퀴즈, 단순 성취기준
  조회에는 로드하지 않는다 — 직접 답한다. 명시적 요청(수업안, 지도안, 교수학습과정안, 차시
  계획, 단원 계획)과 암묵적 신호("다음 주에 광합성 가르쳐야 해요", "중1 여러 가지 힘 수업
  준비해야 하는데") 모두에서 발동한다. 핵심 신호: 교사가 새 수업 자료 생성을 필요로 한다.
  수준별·단계별 자료를 포함한 새 수업도 하나의 설계 요청이다 — 이 스킬이 그 자료까지 수업
  패키지 안에서 만든다. 기존 수업의 차별화(별도 스킬 영역)나 지문 수준 조정에는 쓰지 않는다.
  ※ 이 버전은 과학 전용 프리뷰 — 수학·국어·사회는 준비 중.
```

- [ ] **Step 2: SPDX 주석 블록에 두 줄 추가** (기존 Anthropic·Learning Commons 줄 유지)

```
SPDX-FileCopyrightText: 2026 ko12-teacher-skills contributors

원본: anthropics/k12-teacher-skills v0.6.0 — skills/k12-lesson-planning/SKILL.md
```

- [ ] **Step 3: 제목·도입부** — `# K-12 Lesson Planning` → `# 한국 초·중등 수업 설계 (ko12-lesson-planning)`. 도입 문단의 `Works with or without the Learning Commons Knowledge Graph.` → `Works with or without the Korean curriculum learning-map MCPs (한국 교육과정 학습맵 — 초등·중등).`

- [ ] **Step 4: "Keeping the teacher posted"의 예시 문장 교체** — 괄호 안 영어 예시를 다음으로:

```
*"성취기준을 조회하고 선수 학습·세부 주제를 확인한 뒤, 수업안·학생 자료·관찰 템플릿을 만들게요."*
```

- [ ] **Step 5: Step 0.1 — 과목 신호 4줄과 레퍼런스 매핑 교체**

과목 신호 4줄을 다음으로:

```
   - **math** — 수와 연산, 분수·비율, 도형, 방정식·함수, 미적분, 확률과 통계, 성취기준 코드 `[2수…]`·`[9수…]`·`[10공수…]`
   - **korean** — 읽기, 쓰기, 문법, 문학, 화법, 듣기·말하기, 매체, 코드 `[2국…]`·`[9국…]`
   - **science** — 현상, 실험·탐구, 물리·화학·생명과학·지구과학, 통합과학, 과학탐구실험, 코드 `[4과…]`·`[9과…]`·`[10통과…]`
   - **social_studies** — 역사, 지리, 일반사회, 경제, 시민, 코드 `[4사…]`·`[9사…]`·`[9역…]`
```

레퍼런스 매핑(math → ... social studies → ... 4줄)을 다음으로:

```
   - science → `references/science.md`
   - math · korean · social_studies → **파일럿 범위 밖.** 이 프리뷰는 과학 전용이다. 교사에게
     알리고(예: *"지금 버전은 과학 수업 설계만 지원해요 — 수학·국어·사회는 준비 중입니다."*)
     과학 수업으로 도울 일이 있는지 묻는다. 과학이 아니면 이 스킬 밖에서 일반 지식으로 돕되,
     확인되지 않은 성취기준 코드는 인용하지 않는다.
```

바로 뒤 "Loading the matching reference file is mandatory." 문단은 유지 (과학에만 적용됨이 문맥상 자명).

- [ ] **Step 6: Step 0.2 Curriculum 항목 전체를 다음으로 교체**

```
2. **Textbook.** 한국은 국가 교육과정 단일 체제이지만 교과서는 검정제다 — 출판사마다 단원
   전개가 다르다. 교사가 출판사·교과서를 언급해도 그 교과서의 활동·지문·삽화·문항을 재현하지
   않는다 (아래 저작권 가드레일). 출판사 언급은 "단원의 어디쯤인지" 위치 감각으로만 쓴다.
```

- [ ] **Step 7: Step 0.3 Connector 항목의 도구명 교체**

```
3. **Connector.** Check whether the Korean curriculum learning-map MCP tools (e.g.
   `search_standards`, `get_standard` — servers `curriculum-kr-secondary` /
   `curriculum-kr-elementary`) are available in this conversation. This decides which path
   Step 2 takes. The skill is fully functional without them.
```

- [ ] **Step 8: Step 2 본문 교체** (제목 유지)

```
**If a learning-map MCP is connected:** follow the science section in
`references/curriculum-kr-mcp.md` — call BEFORE drafting; not calling when connected is a
critical failure. Extract only what each call specifies, then proceed directly to Step 3 — do
not summarize findings in chat.

**If not connected:** draft from best knowledge and add this footer to the lesson plan:
*"한국 교육과정 학습맵 미연결 상태에서 생성됨. 성취기준 표현과 오개념은 일반적 모범 사례 기준."*
Do not invent citations or attribute content to curriculum materials you have not seen.
```

- [ ] **Step 9: Copyright guardrail 섹션 본문 교체** (제목은 `## 저작권 가드레일`로)

```
항상 원저작 콘텐츠를 쓴다. 학습맵 데이터(성취기준·세부 주제·관찰 증거·평가 문항)는 구조와
범위, 소재 선택, 수업 흐름 설계에 정보를 줄 뿐이다 — 검정 교과서의 학생 대면 텍스트, 활동,
지문, 삽화, 문항을 재현하지 않는다.

교사가 출판사를 확언하지 않았다면, 어떤 출판사명도 산출물과 채팅 어디에도 쓰지 않는다 —
머리글, 각주, 근거 섹션, 진행 노트, 산출물 소개 메시지 전부. 교사가 밝힌 경우에도 언급은
위치 감각("2단원쯤")으로 제한한다.
```

- [ ] **Step 10: Step 4 draft offer의 질문·선택지 문자열 교체**

```
- Question: *교실에서 바로 쓸 전체 패키지(수업안 + 학생 자료 + 관찰 템플릿, 편집 가능한 워드
  문서)를 만들까요, 아니면 빠른 초안을 먼저 보시겠어요?*
- Options: **바로 만들어 주세요** · **초안 먼저 볼게요** — 수업의 뼈대를 채팅에서 한눈에
```

초안 후속 질문 두 선택지:

```
- **수정할게요** — 초안에서 고치고 싶은 부분 반영
- **자료 만들어 주세요** — 수업안·학생 자료·관찰 템플릿을 편집 가능한 워드 문서로
```

- [ ] **Step 11: Step 5 교사 대면 문자열 3곳 교체**

(a) plain-language 예시: `Say *"Here's your lesson plan — ..."*` 부분 →

```
Say *"수업안이 준비됐어요 — 학생 자료와 관찰 템플릿도 함께 왔습니다"*, not *"lesson.json을
렌더링했어요"*. The only format word in your prose is "워드 문서".
```

(b) "Spell out framework names" 문단 →

```
**Spell out framework names** in every teacher-facing document — 범주명을 축약하지 않는다:
*과·기*가 아니라 *과정·기능*, *지·이*가 아니라 *지식·이해*. 교사가 약어를 찾아봐야 하는
문서는 실패다.
```

(c) 5c의 만족도 질문·반복 옵션 예시 →

```
*"수업안, 학생 자료, 관찰 템플릿을 살펴봐 주세요 — 고치고 싶은 부분이 있나요?"*
```

```
*"(1) 느린 학습자용 스캐폴드 추가, (2) 수준별 학생 자료 3종(A·B·C) 분화, (3) 블록 차시(2차시
연강)로 확장, (4) 과정중심평가 기록지 추가 — 어느 쪽이 도움이 될까요?"*
```

- [ ] **Step 12: 건드리지 않았음을 확인** — 다음이 원본 그대로인지 diff로 확인: Step 1 전체, Step 3 전체, Step 5의 밀도 규칙·Everything matches·Document integrity·5a 스키마 블록·5b 렌더 명령·5d·5e, `shared` 스키마(`smps[]` 포함 — 선택 키라 무해, 동결 원칙 우선).

```bash
git diff --stat plugin/skills/ko12-lesson-planning/SKILL.md
git diff plugin/skills/ko12-lesson-planning/SKILL.md | head -200
```

- [ ] **Step 13: 커밋**

```bash
git add plugin/skills/ko12-lesson-planning/SKILL.md
git commit -m "feat: SKILL.md 한국화 diff — 라우팅·가드레일·교사 대면 문구 (ADR-6)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 5: 검증 대상 레퍼런스 2종을 플러그인 위치로 이동

**Files:**
- Move: `curriculum-kr-mcp.md` → `plugin/skills/ko12-lesson-planning/references/curriculum-kr-mcp.md`
- Move: `science.md` → `plugin/skills/ko12-lesson-planning/references/science.md`
- Modify: `DESIGN.md` §9 문서 지도의 두 파일 경로

**Interfaces:**
- Produces: SKILL.md Step 0·2가 가리키는 `references/` 경로에 실제 파일 존재. Task 6~8이 이 위치의 파일을 검증·수정한다.

- [ ] **Step 1: git mv + 경로 갱신**

```bash
cd /c/Users/22/Desktop/Y-claude/k12-teachers-skills
git mv curriculum-kr-mcp.md plugin/skills/ko12-lesson-planning/references/curriculum-kr-mcp.md
git mv science.md plugin/skills/ko12-lesson-planning/references/science.md
```

`DESIGN.md` §9 표의 `curriculum-kr-mcp.md`·`science.md` 행에 새 경로(`plugin/skills/ko12-lesson-planning/references/…`)를 표기.

- [ ] **Step 2: 참조 무결성 확인** — SKILL.md가 언급하는 references 파일명과 실제 파일 목록이 일치하는지:

```bash
grep -o 'references/[a-z_-]*\.\(md\|json\)' plugin/skills/ko12-lesson-planning/SKILL.md | sort -u
ls plugin/skills/ko12-lesson-planning/references/
```

Expected: 언급 = `curriculum-kr-mcp.md`, `science.md`, `example_lesson.json` — 전부 존재. `learning-commons-kg.md` 언급이 남아 있으면 Task 4 누락 — 돌아가 고친다.

- [ ] **Step 3: 커밋**

```bash
git commit -am "refactor: 레퍼런스 초안 2종을 플러그인 references/로 이동

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 6: curriculum-kr-mcp.md 호출 시퀀스를 실제 중등 MCP로 검증

이 세션에 `curriculum-kr-secondary` MCP가 연결되어 있다(도구 11종). 문서가 주장하는 각 호출을 실제로 실행해 필드·형식·동작을 대조하고, 어긋난 곳은 **문서를 고친다** (BATCH_SPEC 사전 조건 2).

**Files:**
- Modify: `plugin/skills/ko12-lesson-planning/references/curriculum-kr-mcp.md` (불일치 발견 시)
- Create: `docs/superpowers/pilot-notes.md` (검증 기록 — Task 9의 확정 치환 규칙 재료)

**Interfaces:**
- Consumes: 세션 연결된 `mcp__curriculum-kr-secondary__*` 도구.
- Produces: 실 데이터로 확인된 호출 시퀀스 + 파일럿 #1에서 쓸 성취기준·주제 데이터(pilot-notes.md에 기록).

- [ ] **Step 1: 성취기준 확정 경로** — `search_standards(keyword: "광합성", schoolLevel: "middle")` 실행. 반환 형식(요약 목록, `code` 필드)이 문서 기술과 맞는지 확인. 결과가 비면 키워드를 "힘", "물질의 상태"로 바꿔 재시도(문서의 3회 상한 규칙을 그대로 시연).
- [ ] **Step 2: `get_standard`** — Step 1에서 고른 코드로 호출. 확인: 공식 원문 필드 존재, 연결된 주제 ID 목록 존재. 코드 형식 수용성도 확인: `get_standard("[9과01-01]")`처럼 대괄호 포함 형태와 `9과01-01` 형태 중 무엇을 받는지 — 문서의 "코드 형식이 안 맞아 실패하면" 폴백 서술이 실제와 맞는지.
- [ ] **Step 3: 병렬 배치 3종** — 저장한 주제 ID로 한 번에: `get_prerequisites(topicId, depth: "all")`(위상 정렬 경로 + 직전 선수 주제·소속 성취기준 코드 추출 가능한지), `get_topic(topicId)`(**관찰 증거·평가 문항 필드가 실재하는지** — look-for 매핑의 근거), `get_transitions`(topicId와 code 중 무엇을 받는지, 고교 연계 1–2개 반환 형태).
- [ ] **Step 4: `search_standard_text`** — 성취기준 원문 표현 일부(예: Step 2 원문에서 뽑은 구절)로 호출해 전문 검색·스니펫 반환을 확인.
- [ ] **Step 5: 대조 결과 반영** — 문서 기술과 다른 모든 것(파라미터명, 필드명, 반환 구조, 코드 형식)을 `curriculum-kr-mcp.md`에서 수정. 수정 사항과 Step 1~4의 실측 요약(성취기준 코드·원문·주제 ID·관찰 증거 유무)을 `docs/superpowers/pilot-notes.md`에 기록. 초등 서버는 이 세션에 미연결이므로 "초등 라이브 검증은 Task 8의 stdio 프로브로 대체"라고 명기.
- [ ] **Step 6: 커밋**

```bash
git add plugin/skills/ko12-lesson-planning/references/curriculum-kr-mcp.md docs/superpowers/pilot-notes.md
git commit -m "fix: 호출 시퀀스를 실 중등 MCP 응답 형식에 맞게 보정

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 7: 파일럿 생성 #1 — 중학교 과학 수업 (실 MCP, 엔드투엔드)

포팅된 스킬을 교사 요청 시나리오로 끝까지 따른다. 시나리오: **"중학교 과학, Task 6에서 검증한 성취기준의 주제로 45분 1차시"** (실측 데이터 재사용 — 추가 검색 낭비 없음). SKILL.md Step 0→2→3→5를 문서에 적힌 대로 수행한다 — 문서에 없는 재량 판단이 필요해지는 지점이 곧 문서의 구멍이며, 전부 pilot-notes.md에 기록한다.

**Files:**
- Create: `pilot/middle-school/lesson.json` (+ 렌더 산출물은 `pilot/middle-school/out/` — gitignore됨)
- Modify: `docs/superpowers/pilot-notes.md`, 필요시 `references/science.md`·`references/curriculum-kr-mcp.md`

**Interfaces:**
- Consumes: Task 4의 SKILL.md, Task 5·6의 references, 실 중등 MCP 데이터.
- Produces: DoD 체크리스트가 채워진 중학교 수업 패키지(docx 3종 이상).

- [ ] **Step 1: Step 2 실행** — curriculum-kr-mcp.md 과학 절 순서대로 (Task 6 실측 데이터 재사용, 부족한 호출만 추가). 추출: 성취기준 원문 verbatim, 직전 선수 주제 1개, 세부 주제 최대 5개(관찰 증거·평가 문항 포함), 심화 연계 1–2개.
- [ ] **Step 2: Step 3 수업 구성** — science.md 중 1–3학년 밴드 구조(현상 던지기 → 탐구 활동 → 논증 토의 → 주장-증거-추론 설명 → 모형 수정 → 형성 확인)와 섹션 구조 1~7을 그대로 적용.
- [ ] **Step 3: `pilot/middle-school/lesson.json` 작성** — science.md의 "lesson.json 작성 — 과학 매핑" 절대로. 단계 분 합계 = 45 확인.
- [ ] **Step 4: 렌더 + 자동 검증**

```bash
cd /c/Users/22/Desktop/Y-claude/k12-teachers-skills
bash plugin/skills/ko12-lesson-planning/scripts/render_all.sh pilot/middle-school/lesson.json pilot/middle-school/out
python3 tests/smoke/check_docx.py pilot/middle-school/out
```

- [ ] **Step 5: DoD 체크리스트 실측** (pilot-notes.md에 결과 기록):
  - 성취기준 원문 verbatim: docx에서 추출한 성취기준 콜아웃 텍스트 == `get_standard` 원문 (문자열 비교, 정확히 1회 인용)
  - look-for 반영: 관찰 템플릿의 look-for 행이 `get_topic` 관찰 증거에서 왔는지 항목별 대조
  - 3범주 목표: 지식·이해 / 과정·기능 / 가치·태도 분리 진술 존재
  - 시간: phase_header 분 합계 == 45, 배부·회수 시간 명시(실험 수업인 경우)
- [ ] **Step 6: 문서 보정** — Step 1~5에서 드러난 science.md·curriculum-kr-mcp.md의 구멍(모호한 지시, 없는 필드 참조, 어색한 3범주 진술 틀)을 수정하고 pilot-notes.md에 사유 기록.
- [ ] **Step 7: 커밋**

```bash
git add pilot/middle-school/lesson.json docs/superpowers/pilot-notes.md plugin/
git commit -m "feat: 파일럿 #1 중학교 과학 수업 생성 + 레퍼런스 보정

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 8: 파일럿 생성 #2 — 초등 과학 수업 (stdio 프로브로 실 초등 MCP 데이터 확보)

초등 MCP는 이 세션에 연결돼 있지 않다. npm 패키지(`korean-elementary-learning-map-mcp@0.5.1`)를 stdio JSON-RPC로 직접 호출하는 프로브 스크립트로 실 데이터를 받아 "실 MCP 연결" DoD를 충족시킨다.

**Files:**
- Create: `C:\Users\22\AppData\Local\Temp\claude\c--Users-22-Desktop-Y-claude-k12-teachers-skills\83d61513-62fd-4a13-8d50-62b88b098283\scratchpad\mcp_probe.mjs` (스크래치패드 — 저장소에 넣지 않음)
- Create: `pilot/elementary/lesson.json`
- Modify: `docs/superpowers/pilot-notes.md`, 필요시 references 2종

**Interfaces:**
- Consumes: npx로 뜨는 초등 MCP 서버, Task 4·5의 스킬 파일.
- Produces: 초등 실 데이터 기반 수업 패키지 + 초등 서버 도구·필드 실측 기록.

- [ ] **Step 1: 프로브 스크립트 작성 (스크래치패드, 정확히 이 내용)**

```javascript
// mcp_probe.mjs — 초등 학습맵 MCP stdio 프로브
// 사용: node mcp_probe.mjs tools/list
//       node mcp_probe.mjs tools/call search_standards '{"keyword":"물의 상태 변화"}'
import { spawn } from "node:child_process";

const [method, toolName, argJson] = process.argv.slice(2);
const srv = spawn("npx", ["-y", "korean-elementary-learning-map-mcp"], {
  stdio: ["pipe", "pipe", "inherit"],
  shell: true,
});
let buf = "";
const send = (obj) => srv.stdin.write(JSON.stringify(obj) + "\n");
srv.stdout.on("data", (d) => {
  buf += d.toString();
  let i;
  while ((i = buf.indexOf("\n")) >= 0) {
    const line = buf.slice(0, i).trim();
    buf = buf.slice(i + 1);
    if (!line) continue;
    const msg = JSON.parse(line);
    if (msg.id === 2) {
      console.log(JSON.stringify(msg.result, null, 2));
      srv.kill();
      process.exit(0);
    }
  }
});
send({ jsonrpc: "2.0", id: 1, method: "initialize", params: {
  protocolVersion: "2024-11-05", capabilities: {},
  clientInfo: { name: "ko12-probe", version: "0" } } });
setTimeout(() => send({ jsonrpc: "2.0", method: "notifications/initialized" }), 400);
setTimeout(() => {
  const params = method === "tools/call"
    ? { name: toolName, arguments: JSON.parse(argJson || "{}") }
    : {};
  send({ jsonrpc: "2.0", id: 2, method, params });
}, 900);
setTimeout(() => { console.error("timeout"); srv.kill(); process.exit(1); }, 60000);
```

- [ ] **Step 2: 도구 목록 실측** — `node <scratchpad>/mcp_probe.mjs tools/list` 실행. 초등 서버의 실제 도구명·파라미터가 curriculum-kr-mcp.md의 가정(중등과 동일한 `search_standards`/`get_standard`/`get_topic`/`get_prerequisites`)과 맞는지 확인. 다르면 문서의 서버 라우팅 표·과학 절을 수정.
- [ ] **Step 3: 초등 데이터 확보** — 시나리오 "초등 4학년 과학, 물의 상태 변화, 40분": `tools/call search_standards` → 코드(`[4과…]`) 확인 → `get_standard` → `get_topic`·`get_prerequisites`를 프로브로 순차 호출, 결과를 pilot-notes.md에 기록.
- [ ] **Step 4: 수업 구성 + 렌더** — science.md 초 3–4 밴드(현상 던지기 → 탐구 활동 → 의미 나누기 → 모형/표현 → 정리 문항, 40분 합계)로 `pilot/elementary/lesson.json` 작성 →

```bash
bash plugin/skills/ko12-lesson-planning/scripts/render_all.sh pilot/elementary/lesson.json pilot/elementary/out
python3 tests/smoke/check_docx.py pilot/elementary/out
```

- [ ] **Step 5: DoD 체크리스트 실측** — Task 7 Step 5와 같은 4항목(합계 40분 기준) + 초 3–4 협상 불가 원칙 3개(직접 관찰 현상 / 탐구 먼저 / 기제 모형) 충족 여부를 pilot-notes.md에 기록.
- [ ] **Step 6: 커밋**

```bash
git add pilot/elementary/lesson.json docs/superpowers/pilot-notes.md plugin/
git commit -m "feat: 파일럿 #2 초등 과학 수업 생성 (stdio 프로브로 실 초등 MCP 검증)

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 9: 확정 치환 규칙 기록 + README 프리뷰 + 상태 갱신

**Files:**
- Modify: `BATCH_SPEC.md` ("확정 치환 규칙" 절), `DESIGN.md` (버전·상태), `docs/superpowers/pilot-notes.md`
- Create: `README.md`

**Interfaces:**
- Consumes: Task 6~8의 pilot-notes.md 기록 전부.
- Produces: 2단계 배치 작업이 그대로 따를 수 있는 확정 규칙 + 공개 가능한 저장소 상태 (DESIGN §7 "각 단계는 공개 가능한 상태로 끝난다").

- [ ] **Step 1: BATCH_SPEC.md "확정 치환 규칙" 절 채우기** — pilot-notes.md에서 옮겨 적는다. 최소 포함: (a) SKILL.md 12개 diff 지점 목록(Task 4 그대로 — 배치 시 재사용), (b) MCP 응답 필드 실측과 문서 보정 내역, (c) 파일럿 범위 밖 과목 처리 문구(2단계에서 제거 예정임을 명시), (d) 미국 과목 레퍼런스 4종을 복사하지 않은 결정, (e) grade 값·answer_box 밴드 감지 관찰 결과, (f) 렌더 실행 경로(Git Bash python3 자체 설치 성공 여부). 사전 조건 체크박스 3개도 완료 표시.
- [ ] **Step 2: DESIGN.md 갱신** — 버전 v0.1 → v0.2, "초안 — 과학 파일럿 검증 전" → "과학 파일럿 검증 완료(2026-08-01)". §9 문서 지도의 상태 열 갱신. ADR-1 재검토 조건에 파일럿 결과 한 줄(3범주 진술 자연스러움 — 사용자 판정은 Task 10) 기입.
- [ ] **Step 3: README.md 작성** — 구성(각 절 2~6줄, 전체 한 페이지):
  1. 제목 + 한 줄 정의(§1.1) + "과학 전용 프리뷰" 배지 문구
  2. 무엇을 만드나 — 수업안·학생 자료·관찰 템플릿(워드 문서), 성취기준 원문 verbatim 원칙
  3. 설치 — `claude plugin` 마켓플레이스 추가 또는 저장소 clone 후 플러그인 경로 지정; 학습맵 MCP 2종은 `.mcp.json`으로 자동 번들(npx)
  4. 사용 예 — "중1 여러 가지 힘 45분 수업 만들어 줘" 한 줄
  5. 데이터 출처 — 학습맵 2종 저장소 링크(raphysicst-create/korean-secondary-learning-map-mcp, taehyeonglim/korean-elementary-learning-map-mcp), 성취기준 원문은 교육부 고시(2022 개정) — NCIC 공개 문서 기반
  6. Attribution — 원본 anthropics/k12-teacher-skills v0.6.0(Apache-2.0, Anthropic PBC + Learning Commons), 본 저장소도 Apache-2.0, NOTICE 참조
  7. 로드맵 — DESIGN §7 표 요약(2단계 3과목 배치, 3단계 HWPX(kordoc), 4단계 differentiation 스킬)
- [ ] **Step 4: 커밋**

```bash
git add BATCH_SPEC.md DESIGN.md README.md docs/
git commit -m "docs: 확정 치환 규칙 기록 + 과학 전용 프리뷰 README

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>"
```

---

### Task 10: 사용자 검토 게이트 (구현 아님 — 보고와 판정 요청)

**Interfaces:**
- Consumes: `pilot/middle-school/out/`·`pilot/elementary/out/`의 docx, pilot-notes.md의 DoD 체크 결과.
- Produces: ADR-1 판정(3범주 목표 진술이 실제 수업 목표로 자연스러운가 — 현직 과학 교사인 사용자만 내릴 수 있는 판단)과 후속 결정 2건.

- [ ] **Step 1: 최종 보고** — 사용자에게 제시: (a) 생성된 docx 파일 경로 목록(중학교·초등 각 3종 이상), (b) DoD 체크리스트 4항목 실측 결과, (c) 문서 보정 내역 요약, (d) 남은 한계(초등 MCP는 프로브 검증 — Claude 세션 연결 검증은 사용자가 저장소를 플러그인으로 설치할 때 이뤄짐).
- [ ] **Step 2: 판정 요청 2건** — ① ADR-1: 3범주 목표 진술이 자연스러운가(아니면 DESIGN ADR-1 재검토 발동), ② GitHub 공개(신규 원격 저장소 push) 진행 여부 — 외부 공개 행위이므로 사용자 승인 필요.

---

## Self-Review 결과 (계획 확정 전 점검)

- **스펙 커버리지**: DESIGN §7 1단계 DoD(골격+`.mcp.json`+레퍼런스 2종+SKILL diff → Task 2·4·5 / 실 MCP 중·초 각 1회 생성 → Task 7·8 / 체크 4항목 → Task 7·8 Step 5 + Task 10) 및 BATCH_SPEC 사전 조건 3개(생성 테스트 → 7·8, 시퀀스 실작동 → 6, 확정 규칙 기록 → 9) 전부 태스크에 대응됨.
- **의도적 범위 제외**: differentiation 스킬(2차), HWPX/kordoc(3단계), example_lesson.json 한국어화(2단계), 수학·국어·사회(2단계) — DESIGN 로드맵과 일치.
- **알려진 리스크와 완화**: 한글 docx 렌더(Task 3에서 조기 검증) / Git Bash python3 3.14 경로(Task 2 Step 4 우회 포함) / 초등 MCP 미연결(Task 8 stdio 프로브) / grade 밴드 감지(Task 3 Step 4 관찰 후 기록, 렌더러 동결 유지).
