---
name: ko12-lesson-planning
description: >
  수업안·학생 자료·관찰 템플릿을 만든다. 학년·과목·주제·성취기준·차시 분량에 대해 교사에게
  무엇이든 묻기 전에 이 스킬을 먼저 로드할 것. 한국 초·중·고 교사가 새 수업을 만들 때 사용 —
  학년이나 주제가 아직 안 나왔어도 로드한다. 채점, 루브릭, 평가 피드백, 퀴즈, 단순 성취기준
  조회에는 로드하지 않는다 — 직접 답한다. 명시적 요청(수업안, 지도안, 교수학습과정안, 차시
  계획, 단원 계획)과 암묵적 신호("다음 주에 광합성 가르쳐야 해요", "중1 여러 가지 힘 수업
  준비해야 하는데") 모두에서 발동한다. 핵심 신호: 교사가 새 수업 자료 생성을 필요로 한다.
  수준별·단계별 자료를 포함한 새 수업도 하나의 설계 요청이다 — 이 스킬이 그 자료까지 수업
  패키지 안에서 만든다. 기존 수업의 차별화(별도 스킬 영역)나 지문 수준 조정에는 쓰지 않는다.
  ※ 이 스킬은 과학 전용이다 — 다른 과목은 다루지 않는다.
license: Complete terms in LICENSE
---

<!--
SPDX-FileCopyrightText: 2026 Anthropic, PBC
SPDX-FileCopyrightText: 2026 Learning Commons
SPDX-FileCopyrightText: 2026 science-teacher-skills contributors
SPDX-License-Identifier: Apache-2.0

원본: anthropics/k12-teacher-skills v0.6.0 — skills/k12-lesson-planning/SKILL.md
-->

# 한국 초·중등 수업 설계 (ko12-lesson-planning)

Produces a teacher-ready, standards-aligned lesson plan + student-facing materials + teacher
observation template as editable 한글(HWPX) documents in a single output turn, rendered from one material-source JSON via
bundled scripts. The science pedagogy and output mapping live in
`references/science.md`. Works with or without the Korean curriculum learning-map MCPs
(한국 교육과정 학습맵 — 초등·중등).

"The teacher" throughout this skill is the user you are talking with — the same person, never
a third party. "Teacher-facing" names a document's audience: that user, as opposed to their
students.

---

## Keeping the teacher posted

Once the teacher's path is set (the draft offer answered), say in one or two sentences
what you're about to do (e.g. *"성취기준을 조회하고 선수 학습·세부 주제를 확인한 뒤,
수업안·학생 자료·관찰 템플릿을 만들게요."*).

When a task-list or to-do tool is available, also outline this skill's steps there so the
teacher can watch them check off; the only reason to skip this is that no such tool exists
in this conversation.

Teacher language only — name what the teacher is getting, never tool names, file names,
"JSON", or "rendering".

---

## Step 0 — Route (silent, before anything else)

1. **Subject.** Determine whether the requested lesson is science, from the prompt and any
   prior conversation:

   - **science** — 현상, 실험·탐구, 물리·화학·생명과학·지구과학, 통합과학, 과학탐구실험, 코드 `[4과…]`·`[9과…]`·`[10통과…]`

   Then read the reference file NOW:

   - science → `references/science.md`
   - 과학이 아닌 과목 → **범위 밖.** 이 스킬은 과학 전용이다. 교사에게
     알리고(예: *"이 도구는 과학 수업 설계 전용이에요."*)
     과학 수업으로 도울 일이 있는지 묻는다. 과학이 아니면 이 스킬 밖에서 일반 지식으로 돕되,
     확인되지 않은 성취기준 코드는 인용하지 않는다.

   **Loading the reference file is mandatory.** Drafting a lesson without first
   reading `references/science.md` is a critical failure. The reference file carries the
   complete subject-specific instructions: clarify priorities, curriculum branching,
   grade-band structures, section structure, non-negotiables, and the lesson.json mapping.
   Treat the loaded reference as your full skill instructions for this turn. If it is
   genuinely ambiguous whether the request is a science lesson, ask about it
   in Step 1.

2. **Textbook.** 한국은 국가 교육과정 단일 체제이지만 교과서는 검정제다 — 출판사마다 단원
   전개가 다르다. 교사가 출판사·교과서를 언급해도 그 교과서의 활동·지문·삽화·문항을 재현하지
   않는다 (아래 저작권 가드레일). 출판사 언급은 "단원의 어디쯤인지" 위치 감각으로만 쓴다.
3. **Connector.** Check whether the Korean curriculum learning-map MCP tools (e.g.
   `search_standards`, `get_standard` — servers `curriculum-kr-secondary` /
   `curriculum-kr-elementary`) are available in this conversation. This decides which path
   Step 2 takes. The skill is fully functional without them.

---

## Step 1 — Clarify

Read the subject file first — its clarify section defines the priorities and defaults. We
usually ask 0–2 clarifying questions — your judgment on what's relevant; the subject
file's priorities rank which missing answers matter most. Apply the defaults silently for
everything you don't ask about.

The **draft offer** (see *Step 4 — The draft offer* below) travels with this message's questions
as its own separate question — output logistics, not lesson content, so it doesn't count
toward the 0–2. When nothing needs clarifying, the offer is asked on its own.

---

## Step 2 — Ground in standards

**If a learning-map MCP is connected:** follow the science section in
`references/curriculum-kr-mcp.md` — call BEFORE drafting; not calling when connected is a
critical failure. Extract only what each call specifies, then proceed directly to Step 3 — do
not summarize findings in chat.

**If not connected:** draft from best knowledge and add this footer to the lesson plan:
*"한국 교육과정 학습맵 미연결 상태에서 생성됨. 성취기준 표현과 오개념은 일반적 모범 사례 기준."*
Do not invent citations or attribute content to curriculum materials you have not seen.

---

## Step 3 — Build the lesson

Follow the subject file's build section: curriculum branching, grade-band structure, section
structure, and non-negotiables. Respect the **Copyright guardrail** below — never reproduce
curriculum student-facing text verbatim.

---

## 저작권 가드레일

항상 원저작 콘텐츠를 쓴다. 학습맵 데이터(성취기준·세부 주제·관찰 증거·평가 문항)는 구조와
범위, 소재 선택, 수업 흐름 설계에 정보를 줄 뿐이다 — 검정 교과서의 학생 대면 텍스트, 활동,
지문, 삽화, 문항을 재현하지 않는다.

교사가 출판사를 확언하지 않았다면, 어떤 출판사명도 산출물과 채팅 어디에도 쓰지 않는다 —
머리글, 각주, 근거 섹션, 진행 노트, 산출물 소개 메시지 전부. 교사가 밝힌 경우에도 언급은
위치 감각("2단원쯤")으로 제한한다.

---

## Step 4 — The draft offer

The teacher gets the choice of a fast draft before the build. The offer is
asked the same way as the clarify questions — through the structured question tool when
one is available, in chat otherwise — as its own separate question, batched with Step 1's
questions when there are any and asked on its own when there aren't.

- Question: *교실에서 바로 쓸 전체 패키지(수업안 + 학생 자료 + 관찰 템플릿, 편집 가능한 한글
  문서)를 만들까요, 아니면 빠른 초안을 먼저 보시겠어요?*
- Options: **바로 만들어 주세요** · **초안 먼저 볼게요** — 수업의 뼈대를 채팅에서 한눈에

**The full packet is the default.** Declining, not answering, or anything like "proceed
with your defaults" runs Steps 2–3 and goes straight to Step 5; the draft happens only on
a clear yes.

**The draft (on a yes) is built on Steps 2–3, never instead of them.** Run Step 2 in
full — every KG call, exactly as written — and Step 3 before sketching anything. A draft
sketched without the Step 2 grounding is a critical failure, the same failure as skipping
the KG on the full build. Then present the lesson in chat — the draft is chat text only;
rendering happens at Step 5 once the teacher approves. Show:

- one line naming the grade, topic, and the standard the lesson is anchored to (code plus
  a gist of ten words or fewer);
- a summary of at most 3 sentences (what students do and why it works for this class);
- the sequence as one bullet per phase (name, minutes, one line of what happens);
- the student work at a glance — the actual tasks students will do, enough for the
  teacher to skim and judge coverage;
- what the lesson assumes students already know — the prerequisite skills or key
  vocabulary in play — so the teacher can catch a mismatch with where their class is;
- the exit ticket

The draft borrows its names from the documents it previews — phases, tasks, tiers,
and sections are called what the plan will call them.

Afterwards, ask what's next — a structured question, two options:

- **수정할게요** — 초안에서 고치고 싶은 부분 반영
- **자료 만들어 주세요** — 수업안·학생 자료·관찰 템플릿을 편집 가능한 한글 문서로

Apply change requests to the draft in chat and re-present it — changes are quick at this
stage. Step 5 runs in the turn the teacher gives the go-ahead ("Create the materials",
"proceed with your defaults", or similar).

---

## Step 5 — Output (one turn)

Runs immediately when the teacher chose the full packet, or in the turn the draft is
approved.

The artifacts are rendered by bundled scripts from **one material-source `lesson.json`**. The JSON
holds a `shared` block (content registered once) and a `documents[]` array (each document
authored as free-form `sections`). A section's `heading` renders as a large title directly
above its blocks; a block's `label` renders as a bold lead-in on the block itself. A label
that repeats its section's heading prints the same words twice in a row — labels carry what
the heading doesn't (the task's name belongs in one of them, not both). You
compose every page — the lesson plan, the student
materials, the observation template, and any others the lesson needs (e.g. a source packet)
— directly in `documents[]`. Anything that appears on more than one page is registered once
in `shared` under a key you choose and pulled into each document with
`{"type": "from_shared", "key": …}`, so the pages cannot drift apart.

Never write layout code, never re-type lesson content into another format, and never edit a
generated document directly — every change goes into `lesson.json` and is re-rendered
(re-rendering is instant). **Do not open, cat, head, or grep the renderer scripts** — their
behavior is fully specified by the commands and output paths in §5a–5d, and
`references/example_lesson.json` is the complete schema. Reading script source tells you
nothing this file doesn't already state.

**Plain language with the teacher.** The machinery above is invisible to the teacher: never
mention JSON, HTML, schemas, scripts, rendering, file names (`lesson.json`), or code in any
teacher-facing message — and never link or name the `.html` files the render command also
writes. Say *"수업안이 준비됐어요 — 학생 자료와 관찰 템플릿도 함께 왔습니다"*, not *"lesson.json을
렌더링했어요"*. The only format words in your prose are
"한글 문서" / "한글 파일". This
applies to every turn: presenting artifacts, the satisfaction ask, revision summaries, and
error messages (if generation fails, say the documents couldn't be created — not that a
script or JSON failed).

**Density rules — hard requirements for every document.** Every document is clear, brief,
and easy to skim. Include what a teacher needs to teach it; leave out what merely
demonstrates rigor. Headings use sentence case. Structure beats prose:

- A `paragraph` or `labeled` block is at most 3 sentences. Longer → split it, bullet it, or
  table it.
- Write like a colleague's note: plain, direct sentences built from commas and periods.
- Bullets are fragments — one idea each, ≤ ~15 words; never chain clauses with semicolons.
- Parallel variants (per-group supports, per-phase differentiation, tiered look-fors) go in
  ONE `table` block — rows = phases or features, columns = variants, ≤ ~25 words per cell —
  never back-to-back multi-sentence paragraphs.
- A callout marks the few moments a teacher must not miss — a warning ("do not resolve the
  debate yet"), a collect-before-moving-on, the one make-or-break move of a phase. A page
  where everything is boxed highlights nothing: a phase reads as plain script with at most
  one or two callouts. Teacher asides (watch-fors, confer prompts) are `labeled` or
  `instructions` blocks.
- Each instruction lives in exactly one place. A phase's opening prose and its blocks divide
  the work between them — the prose sets up, the blocks carry the content; neither repeats
  the other.
- Quote the standard verbatim exactly once (the target-standard callout, from `shared`).
  Everywhere else — prerequisite grounding, forward connections — reference by code plus a
  gist of ten words or fewer; never re-paste full standard text.
- A section that runs past about half a page of continuous prose must be restructured
  (table, bullets, or split into two sections) before rendering.

**Everything matches — hard requirements for every document.** A teacher trusts the package
because every part agrees with every other part:

- The materials list and the phases agree exactly: every listed item is used by a named
  phase, and every counted set matches its enumeration ("Picture cards, 18" lists 18 words).
- **Classroom-ready:** the lesson runs on what the teacher already holds. Every Materials
  item is a page this package ships, equipment the classroom has, or a sourced resource
  with its access path stated — exact title and source, a link when you could confirm one.
  Anything harder to get than that stays out of the lesson unless the teacher steered
  toward it. A printable the lesson depends on ships with the package — as lesson pages
  when the document set expresses it, or as its own file in the format that renders it
  best (5e).
- A task worded in two places (plan's "Students see" and the student page) uses identical
  wording in both.
- Student tasks match the skill the standard names, in both directions. Decoding, spelling,
  and writing skills happen on paper — students read and write real words on a student page.
  Listening and speaking skills get spoken, pointed, sorted, drawn, or circled responses.
  The lesson's scope statement binds every task that follows it.
- Scripts and worked examples are final say-aloud text: every step decided before it lands
  on the page, exactly what the teacher says.
- Exit-ticket sort buckets partition the answers: each example response fits exactly one
  bucket, and equivalent forms of one answer (17 + 24 = ? and 24 + 17 = ?) sit in the same
  bucket together.
- An answer space mirrors its ask: rows match the count requested, and every box sits under
  a prompt naming what goes in it.
- Number pairs inside a sentence are plain text ("2 → 10, 5 → 25"); a table is always its
  own block.

**Reading level and workload.** Student-facing text reads at the students' reading level —
which the teacher may state separately from the grade ("my 6th graders read at a 2nd–4th
grade level" means grade-6 content carried in sentences a 2nd–4th grade reader can read:
short sentences, everyday words, one instruction at a time). Size the student work to the
class period: a typical student finishes the worksheet in the minutes its phase allows.
Say "home language," not a specific language, and print translations only into a language
the teacher has named.

**Sentence supports** are plain text where students write: a starter to begin from
("One central idea is…") or a fill-in frame with blanks sized for the student's handwriting.
A support helps the student start, not answer — it never pre-fills what the task asks for.
Place each one on the specific task whose writing move is hardest —
never one bank copied across problems. K-2 students
and multilingual learners get a support on every task that asks for composed sentences.
Tasks that take only a number, a single word, or a drawing need none.

**Spell out framework names** in every teacher-facing document — 범주명을 축약하지 않는다:
*과·기*가 아니라 *과정·기능*, *지·이*가 아니라 *지식·이해*. 교사가 약어를 찾아봐야 하는
문서는 실패다.

**Document integrity.** Every document is finished prose a teacher hands out or works from:

- Every in-document reference points at something that exists in the package: "jot it in the
  table below" means that table is on the page; an exit ticket collected separately prints as
  its own piece; a reference table uses the same numbers as the problems it supports.
- Materials and the lesson match both ways: each listed item is used somewhere in the
  lesson, every item any section sends students to — phases and extensions alike — appears
  in Materials, and anything students read is printed in the package or named by its exact
  title. Offers and pointers to the chat conversation stay out
  of documents entirely.
- Lessons are light on materials: the default kit is what every classroom has (board,
  projector, paper) plus the pages this lesson ships. A separate printable or manipulative
  earns its place only when the activity genuinely needs it — and the same thinking work on
  the worksheet usually serves. When a printable earns it (cards, mats, a template), ship it
  with the package (5e picks the format); equipment a classroom owns is simply listed.
- Phase minutes include the transitions they cause (handing out, regrouping, collecting), at
  a pace real students of this grade manage, and the phases sum to exactly the stated
  period — transition time lives inside the phases, never as invisible buffer.
- Teacher notes read as finished sentences. A predicted error names one specific wrong answer
  a real student would produce.
- Verify every computation by working it — answer keys, worked examples, and any quantitative
  chain the lesson builds on (an energy pyramid's levels, a ratio table's entries, a coin
  total) produce the numbers the materials state.

### 5a. Write the complete `lesson.json` (same turn)

Write ONE `lesson.json` with two top-level keys: `shared` and `documents`.

**`shared` is a content registry.** It always carries the lesson identity — `grade`,
`subject`, `duration`, `standard_code`, `standard_text` (and `curriculum`,
`prerequisite_standard`, `smps[]` when applicable). Beyond that, register any content that
appears on more than one page under a key you choose: a problem as `p1`, a source as
`stamp_act_petition`, a data set as `prices_table`. A key's
value can be a string, a single block, a list of blocks, or a faceted object
`{teacher: …, student: …, stimulus: [blocks]}`. On a **student** page, only the `student`
facet (after any `stimulus` blocks) renders — a `student` of `null` means nothing prints
there, which is how oral or teacher-led tasks stay off the worksheet. On a **teacher** page,
both facets render: the teacher facet as plain script, then the student facet as one
"Students see" line, so the teacher reads their own script and the exact prompt
students will work from. A teacher facet written as a list of strings renders one move per
line — the glanceable form for any script with more than two moves — and since the student
text prints right beside it, the script points to it ("read the story in the box aloud")
rather than quoting it again. Apart from `standard` (which assembles `standard_code` +
`standard_text` into the target-standard callout), key names carry no special rendering — a
vocabulary list, a misconceptions table, an exit-ticket sort are blocks you compose yourself
(see `references/example_lesson.json` for the patterns).

**`documents[]` is where you compose each page.** Each entry is a full page:
`{id, audience: teacher|student, eyebrow, title, meta?, theme?, sections[{heading, blocks[]}]}`.
Include at minimum:

- `id: "lesson_plan"` (`audience: "teacher"`) — the subject file's section structure.
- `id: "observation_template"` (`audience: "teacher"`) — how-to-use, look-fors,
  misconceptions, a `fill_table` for student notes, and the exit-ticket sort.
- `id: "student_materials"` (`audience: "student"`) — **only when students hold a printed
  page.** A K-2 phonics or oral lesson may have none; a source-heavy lesson may have this AND
  a separate `id: "source_packet"`. The subject file's *Student page layout* gives the
  default skeleton; adapt it to the lesson. If the teacher asked for leveled/tiered student
  materials, label them Group A / B / C (A = below, B = at, C = above grade level) — level
  wording stays in the teacher-facing documents.

Inside any document, pull registered content with `{"type": "from_shared", "key": "…"}` —
the same key on two pages renders the same content (faceted by audience). Adding
`"label": "1"` to a `from_shared` block renders the pulled text as a numbered item on one
line. Within a single document, pull each key once (a reference table, an exit-ticket
protocol, a word list appears in one section only). Content that appears on only one page
can be written inline.

**Schema** — sufficient on its own; do not read any other file for the schema:

```
shared:
  grade, subject, duration, standard_code, standard_text          (required identity)
  curriculum?, prerequisite_standard?, smps[]?
  <any key you choose>: string
                      | block | block[]
                      | {teacher: …, student: … or null, stimulus?: block[]}
  (only `standard` is special — it assembles standard_code+standard_text)
documents[]: {id, audience: teacher|student, eyebrow, title, meta?, theme?,
              sections[]: {heading, color?, blocks[]}}
block types:
  {type: from_shared, key}
  {type: paragraph, text} | {type: labeled, label, text}
  {type: callout, kind: special|student-task|teacher-note|student-note, label, text}
  {type: h2|h3, text} | {type: list, label?, ordered?, items[]}
  {type: phase_header, name, minutes} | {type: cards, items[{title, text}]}
  {type: table|data_table, headers[]?, rows[[]]}
  {type: fill_table, headers[], blank_rows: int, row_height_pt?}
  {type: number_line, min, max, ticks?, marks[]?}
  {type: source_card, title, author?, date?, origin?, excerpt}
  {type: answer_box, height_pt?, ruled?} | {type: page_break}
  {type: group, blocks[]} | {type: columns, left[], right[]}
```

`references/example_lesson.json` is a filled-in worked example. Keep writing tight; no emoji
in JSON content. The density rules above are hard requirements for every text field.
Print-safety: never markdown pipe tables (use `table`/`data_table`); for number lines use
the `number_line` block, not a digit string. The renderer cannot draw images — anything the
teacher displays (a video, photo, projected image, chart) lives in the lesson plan: name it
in Materials and in the phase script that uses it. A student page carries only what is
printed on it.

**Which block when** — pick by what the content *is*, not how it should look:

| Block | Use it for |
|---|---|
| `callout` `kind: special` | The one anchoring fact per artifact — the target standard. Typically once. |
| `callout` `kind: student-task` | Any task students do: anchor task, exit ticket prompt, a practice problem shown in the plan. |
| `callout` `kind: teacher-note` | An aside the teacher reads but does not say aloud: "don't resolve yet", conferring moves, a watch-for. |
| `list` `ordered: true` | A numbered sequence — the problem set, procedure steps. Unordered otherwise. |
| `list` with `label` | A titled enumeration — several discrete items under one label. |
| `h2` | Sub-sections inside a section — the lesson-sequence phases use `phase_header`, which renders as h2 with minutes; the `minutes` across all phase headers should sum to `shared.duration`. |
| `h3` | A title above one block (a table, a list group, the look-fors). |
| `cards` | 2–4 parallel items of roughly equal length — exit-ticket sort buckets, tier summaries. Never for long or unbalanced items; use a `list` for those. |
| `table` (no `headers`) | Term/definition pairs, label/value reference rows. |
| `table` / `data_table` with `headers` | Real tabular data with column labels (misconceptions, scaffolds, the data set students analyze). `display: "large"` renders cells in big centered type — a word grid young students point to and read. |
| `fill_table` | An organizer students write into — observation log, comparison grid, evidence collector. `rows` as a count gives blank rows; `rows` as a list mixes filled and blank — `[["cap","cape"], [], []]` shows a worked first row, then write-in space, and `[["Shell", "", ""]]` gives a labeled row with blank cells students write in (say what goes in the blank — a ✓, yes/no, a word — in the instruction line above). |
| `number_line` | A drawn number line (`min`, `max`, `ticks`, optional `marks`). `ticks` omitted defaults to 10 evenly spaced segments; `ticks: 0` draws a bare line with only the `min`/`max` end labels and no tick marks, for students to partition themselves. |
| `source_card` | A primary or secondary source excerpt students read: title/author/date + the excerpt text. |
| `answer_box` | Writing space after a task. With no `height_pt` it sizes itself to the grade band (K-2 ~200pt, 3-5 ~150pt, 6-8 ~130pt, 9-12 ~115pt). K-5 boxes draw ruled handwriting lines; `ruled: true` draws lines at any grade — the surface for answers of composed sentences — and `ruled: false` gives open space for drawing or model-sketching. A task answered in a `fill_table` or on a `number_line` already has its surface. |
| `group` | Keeps a task's prompt, stimulus, supports, and answer box together so a page break never separates them. |

### 5b. Render every document — one command, same turn

Run this from the teacher's working folder (the one where you wrote `lesson.json`) and call
the script by **absolute path** — when this skill runs as an installed plugin, the skill
folder is nowhere near the working folder, so a relative `scripts/…` call fails. Do not `cd`
into the skill folder.

```bash
SKILL_DIR="<absolute path of the folder containing this SKILL.md>"
bash "$SKILL_DIR/scripts/render_all.sh" lesson.json "$OUTPUT_DIR"
```

This writes one editable `.hwpx` (the teacher deliverable — opens in 한글) per `documents[]`
entry, named by `id` (e.g. `$OUTPUT_DIR/lesson_plan.hwpx`, `student_materials.hwpx`,
`observation_template.hwpx`, `source_packet.hwpx`), plus `.html` and `lesson.json` working
files. Render straight into `$OUTPUT_DIR` and leave everything the script writes in place —
later revision turns re-render from the working files even though the teacher only sees the
한글 documents. Then list `$OUTPUT_DIR` and confirm every document has both its `.hwpx` and
`.html`; if either is missing or tiny, rerun the script. Present the 한글 documents to the
teacher together — attach the lesson plan last so it lands on top (chat surfaces stack
newest-first). If there is no `student_materials` document, say so plainly ("이 수업은 구두
활동 중심이라 학생 유인물이 없어요 — 학생들은 …로 활동합니다"). If the script errors, fix
`lesson.json` (it is almost always malformed JSON) and rerun. If file generation fails
entirely, say so clearly — do not silently fall back to a chat-only delivery.

### 5c. The satisfaction ask + iteration options (every output turn)

End the turn with EXACTLY ONE closing message that does three things, in this order:

1. **If Materials names equipment the classroom has that a paper version can stand in
   for** — coins, blocks, dice, a hundred chart — lead with a bolded offer to print it:
   *"**이 수업은 수 모형을 써요 — 부족할 때를 대비해 인쇄용 세트를 만들어 드릴까요?**"*
   Anything whose content this lesson wrote — word cards, a
   source excerpt, a sorting mat with this lesson's categories — already ships with
   the package.
2. Asks whether the teacher is satisfied with **every artifact produced** or wants changes —
   e.g. *"수업안, 학생 자료, 관찰 템플릿을 살펴봐 주세요 — 고치고 싶은 부분이 있나요?"*
   Do not skip the ask.
3. Offers 3–4 high-leverage, **specific** iteration options customized to the subject and
   topic. Do not write "let me know if you want changes" — that's a non-offer. For example,
   for a middle-school science inquiry lesson: *"(1) 느린 학습자용 스캐폴드 추가, (2) 수준별
   학생 자료 3종(A·B·C) 분화, (3) 블록 차시(2차시 연강)로 확장, (4) 과정중심평가 기록지
   추가 — 어느 쪽이 도움이 될까요?"*

### 5d. Revisions — one edit, every artifact stays in sync

Make **targeted edits to `lesson.json`**, then re-render every document (instant). Rules that
keep the artifacts consistent:

- If the change touches content registered in `shared` (a problem, a source, the exit ticket,
  vocabulary, look-fors, the phenomenon/context/numbers), edit it **in `shared`** — every
  document that pulls that key updates automatically.
- **Consistency sweep after any context/number/task change:** after editing `shared`, re-read
  every prose block in every `documents[]` entry and update every sentence that still mentions
  the old context, names, or numbers. When you are done, no document may reference the
  replaced content anywhere — stale prose is the most common consistency failure.
- A change aimed at one document (e.g. "more workspace on the worksheet", "add a column to the
  observation grid") goes in that document's `sections` — never by forking a `shared` key into
  two variants.
- Styling: `theme` fields (`primary`, `title_size`, `body_size`) apply to every artifact.
  Artifacts use minimal color so they print cleanly in black-and-white; do not set
  per-section or per-phase colors.

### 5e. Supplementary artifacts in their best format

The `lesson.json` pipeline is for the lesson's document set: pages a student or teacher
reads or writes on. An artifact whose value depends on its form — exact card
dimensions for cutting, poster-scale type — belongs outside it, as its own file in
whatever format produces the best version (e.g. a print-ready PDF). Your judgment
picks the format; source any shared content from `shared` so pages can't drift, and name
the file in Materials like any other page.
