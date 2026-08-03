# 원본 그대로 둔 evals 항목

업스트림 `k12-teacher-skills`의 채점 루브릭 중 한국판 보정에서 **한 글자도 고치지 않은 38항목**의 전문이다. 현재 전체 69항목 가운데 나머지 31항목(변경 29 · 신설 2)은 [`evals-port-review.html`](evals-port-review.html)에서 원본과 나란히 볼 수 있다.

이 파일이 있는 이유는 대조 페이지와 짝을 이루기 위해서다. 그쪽이 *무엇을 왜 바꿨나*를 보인다면, 이 파일은 **바꾸지 않았다고 말한 것이 정말 원본 그대로인지** 독자가 확인할 수 있게 한다. 둘이 다 있어야 "고장난 것만 고쳤다"가 검증 가능한 진술이 된다.

대조 기준: `a76d683` (보정 직전) → 현재 작업 트리. `python docs/evals_port_review.py --unchanged`로 재생성한다.

> 아래 본문은 **업스트림 원문 그대로**이며 번역하지 않았다 — 한 글자도 고치지 않았다는 것이 이 문서의 요점이라 옮기는 순간 그 주장이 성립하지 않는다. 저작권 표기는 Anthropic, PBC / Learning Commons, Apache-2.0.

## 분포

두 루브릭 파일은 ID 공간이 서로 독립이다 — `P5`·`O2` 같은 ID가 양쪽에 따로 존재하므로 열을 갈라 적는다.

| 버킷 | 수업 설계 · 공통 (23) | 수준별 차별화 (15) |
| :--- | :--- | :--- |
| Pedagogy — 교육적 설계 | `P5` · `P6a` · `P7` · `P8` · `P9` · `P10` | `P3` · `P5` · `P7` · `P8` |
| Rigor — 인지적 요구 수준 | `R1` · `R2` · `R4` | `R1` · `R3` |
| Output / Formatting — 산출물 형식 | `O2` · `O3` · `O4` · `O5` · `O6` · `O7` · `O8` · `O9` · `O10` · `O11` · `O12` · `O13` · `O14` · `O15` | `O2` · `O3` · `O4` · `O6` · `O7` · `O8` · `O9` |
| Model Scaffolding — 모델의 대화 행동 | — | `M2` · `M3` |

분포가 한쪽으로 쏠려 있고, 그게 이 이식의 성격을 말해 준다. **산출물 형식(O)은 21항목이 그대로 왔다** — 학생이 쓸 공간이 충분한가, 교사용 내용이 학생 문서에 새지 않았나, 문서끼리 모순되지 않나 같은 것은 교육과정 체제와 무관하게 성립한다. 반면 **pedagogy(P 10)와 모델 대화 행동(M 2)은 유지된 비율이 낮다** — 목표 진술 프레임, 성취기준 인용 규칙, 무엇을 먼저 물어야 하는가는 체제에 직접 매여 있기 때문이다. 바꾼 쪽이 어디에 몰렸는지는 [`evals-port-review.html`](evals-port-review.html)에서 확인할 수 있다.

---

## 수업 설계 · 공통

`evals/ko12-lesson-planning/rubrics/shared.csv` — 전체 33항목 중 유지 23항목

### `P5` · Lesson phases present and sequenced correctly

**Bucket** — P — Pedagogy

**What pass requires** — The lesson has a recognizable instructional arc appropriate to the domain with time allocations on each phase. Pass = all required phases present with times. Fail = phases missing, merged, or unlabeled.

### `P6a` · Look-fors — minimum count

**Bucket** — P — Pedagogy

**What pass requires** — At least 3 look-fors are named for the main practice or work phase. Pass = 3 or more entries. Fail = fewer than 3.

### `P7` · Visual scaffolds with rationale

**Bucket** — P — Pedagogy

**What pass requires** — Visual or representational choices are pedagogically informed WITH stated rationale — e.g., a drawing-first option, an intentional choice not to pre-print a diagram, or guidance on when to introduce a visual model and why. Pass = at least one visual or representational choice with explicit reasoning. Fail = visuals appear without rationale, or no visual/representational thinking is evident in the plan.

### `P8` · Student engagement hook

**Bucket** — P — Pedagogy

**What pass requires** — At least one task is designed to generate genuine student curiosity or interest — an unexpected or novel context, an open-ended question, a real-world scenario students would care about, or productive-struggle design. A generic word problem or comprehension task does not count; there must be a deliberate hook. Not every task needs this quality — one is sufficient.

### `P9` · Timing is realistic

**Bucket** — P — Pedagogy

**What pass requires** — The work assigned in each phase is plausibly completable in the allotted minutes by students at this grade level. Count the tasks in each phase and estimate minutes per task. Pass = every phase's workload fits its time. Fail = any phase assigns clearly more work than its time allows (e.g., 12 problems in a 20-minute block that also includes discussion).

### `R1` · Grade-level demand is maintained

**Bucket** — R — Rigor

**What pass requires** — No scaffolding in the lesson reduces the cognitive demand below the standard's level. Supports provide access without simplifying the task. Pass = all student work targets the standard's complexity. Fail = problems are simplified to below-grade content, or the hardest part of the standard is avoided.

### `R2` · At least one task demands student reasoning

**Bucket** — R — Rigor

**What pass requires** — A student who only memorizes or follows steps cannot complete at least one task. Pass = one or more tasks require explanation, justification, comparison, or argumentation. Fail = every task is recall or procedural with a single right answer.

### `R4` · Student agency prompt on worksheet

**Bucket** — R — Rigor

**What pass requires** — The student-facing worksheet itself includes at least one prompt inviting student reasoning or choice: a self-assessment question, a reflection prompt, an open-ended extension, or a 'show/explain your thinking' prompt attached to a task (these count even when embedded in task items). Teacher-led discussion prompts in the lesson plan do NOT count. Judge the student materials only.

### `O2` · Student materials contain no teacher-only content

**Bucket** — O — Output / Formatting

**What pass requires** — Student-facing materials contain no teacher-only content: no look-fors, no misconception or points-of-difficulty notes, no assessment rationale, no answer keys, no instructions directed at the teacher ('the teacher places…', 'circulate and…'), no stage directions written TO the teacher ('Show…', 'Display…', 'Read aloud…', 'Distribute…'), and no third-person narration of student activity ('Students work in pairs…', 'Students blend the sounds…'). Scaffolding addressed TO STUDENTS in second person (hints, 'Remember:' reminders, sentence frames, worked examples) is student content and is fine — do NOT fail for it. Judge the student materials only; content in the lesson plan or observation sheet is irrelevant here.

### `O3` · Observation template rows are usable in the field

**Bucket** — O — Output / Formatting

**What pass requires** — Row labels are specific student behaviors traceable to SWBAT ('student will be able to') — not generic phase names — and each row has adequate writing space. Pass = behavior-specific labels and sufficient writing space throughout. Fail = rows labeled 'Phase 1 / Phase 2', or table is so compressed a teacher couldn't write in it.

### `O4` · Lesson plan is concise and scannable

**Bucket** — O — Output / Formatting

**What pass requires** — Teacher-facing plan uses clear headers and the instructional sequence is findable at a glance — a teacher can locate the next action within 10 seconds of scanning the page. Pass = action sequence is visually distinct from rationale. Fail = instructional steps are embedded in paragraphs of rationale so that the sequence isn't findable without reading closely.

### `O5` · Universal Design access features

**Bucket** — O — Output / Formatting

**What pass requires** — At least two Universal Design representation features are present in the base materials, such as: sentence stems or frames, clarification of symbols and vocabulary, multiple forms of representation (visual + symbolic + verbal), a culturally open task context, or choice in how students show their work. Name the features found in the explanation.

### `O6` · Teacher and student materials describe the same tasks

**Bucket** — O — Output / Formatting

**What pass requires** — The student materials' tasks ARE the same tasks the lesson plan describes — same contexts, same numbers and specifics, same count — and the observation sheet's look-fors are the ones the lesson plan names. Direction 1: every activity named in the plan has a corresponding student-facing version. Direction 2: nothing in the student materials is unaccounted for in the plan. List every mismatch found; pass only if BOTH directions are clean.

### `O7` · Teacher adaptation rationale notes

**Bucket** — O — Output / Formatting

**What pass requires** — The lesson plan includes one or two brief rationale notes identifying which elements must be PRESERVED to maintain alignment and rigor (non-negotiables such as curriculum sequence, grade-level demand, discourse structure) and why. Generic praise ('this lesson is well-structured') does not count.

### `O8` · Outputs are specific not generic

**Bucket** — O — Output / Formatting

**What pass requires** — Misconceptions, look-fors, and prerequisite references are specific to this standard's content — a reader could not transplant them unchanged to an unrelated topic. The standard text quoted in body text matches the header word-for-word wherever it appears. Fail = boilerplate misconceptions ('students may get confused'), generic look-fors, or a standard subtly reworded between header and body.

### `O9` · Narrative coherence across artifacts

**Bucket** — O — Output / Formatting

**What pass requires** — Contexts, names, numbers, grade level, and timing references agree across all artifacts. No artifact narrates a context, example, or task that the others do not have. Judge all artifacts together.

### `O10` · No contradictions across artifacts

**Bucket** — O — Output / Formatting

**What pass requires** — No conflicting counts, durations, units, instructions, or directions between any two artifacts. Quote any contradiction found in the explanation.

### `O11` · Lesson plan is internally consistent

**Bucket** — O — Output / Formatting

**What pass requires** — The plan never contradicts itself about which task or case is hardest; discussion and closing phases anchor on the case the rationale identifies as most important; and any task types the prose promises (e.g., 'students will work start-unknown problems') actually exist in the materials. Fail = the plan promises content that never appears, or different sections disagree about emphasis.

### `O12` · Closing phase introduces nothing new

**Bucket** — O — Output / Formatting

**What pass requires** — Every concept, case, or notation appearing in the synthesis/closing phase was investigated by students in an earlier phase. Nothing appears for the first time in the closing. Fail = the summary introduces a case, term, or representation students never worked with.

### `O13` · Information density

**Bucket** — O — Output / Formatting

**What pass requires** — Artifacts favor structure over prose: paragraphs stay within roughly 3 sentences; parallel content (per-group supports, per-phase variants, look-fors) appears in tables or bullet lists rather than stacked multi-sentence paragraphs; bullets are one-idea fragments rather than chained clauses. Fail = any wall-of-text paragraph or parallel variants written as back-to-back prose paragraphs.

### `O14` · Writing space matches demand

**Bucket** — O — Output / Formatting

**What pass requires** — Every student-facing prompt that demands written work (problems, exit ticket, reflection) is followed by visible blank writing space proportionate to the expected response and grade level — younger students get more room, multi-sentence answers get generous space, fill-in items get a line or two. Fail = any prompt with no adjacent writing space or space plainly too small for the expected response.

### `P10` · Standards economy

**Bucket** — P — Pedagogy

**What pass requires** — The target standard's full text appears exactly once (header or standards callout). Prerequisite and forward standards are referenced by code plus a short gist, never pasted in full. Fail = the full target standard repeated elsewhere, or prerequisite/forward standard text quoted verbatim.

### `O15` · Document set fits the lesson

**Bucket** — O — Output / Formatting

**What pass requires** — The package contains a lesson plan and student materials. Student materials may be absent only when the lesson is genuinely oral or teacher-led end to end AND the lesson plan says so plainly (this is rare — when in doubt, student materials should exist). Documents beyond the standard set (lesson plan, student materials, observation template) — a source packet, a data sheet — are used by a lesson phase. Fail = no student materials without an explicit oral-lesson rationale in the plan, or an extra document no phase uses. The observation template never fails this criterion.

---

## 수준별 차별화

`evals/ko12-lesson-differentiation/rubrics/differentiation.csv` — 전체 27항목 중 유지 15항목

### `P3` · Scaffolds support thinking

**Bucket** — P — Pedagogy

**What pass requires** — No scaffold in any tier provides the answer directly: no fill-in-the-blank with only one possible word, no embedded answer key, no step-by-step guide requiring zero student decisions, and no keyword or shortcut strategies (math: "'together' means add"; ELA: "the central idea is always in the first sentence"; a sentence starter that hands the student the claim). At least one problem or task in each tier requires a student decision that is not resolved by the scaffold provided.

### `P5` · Invisible-modifications rule

**Bucket** — P — Pedagogy

**What pass requires** — Every tier works toward the SAME objective in the SAME scenario or text context. Task wording and supports MAY vary between tiers — judge the goal, not the phrasing. Differences must be limited to phrasing, added supports, visual aids, sentence frames, or a reduced number of tasks. Fail ONLY if a tier changes the goal, the context, or the kind of work students produce (e.g., one tier writes about a different topic, or answers multiple-choice while the others compose). Quote any tier where the goal or context itself changed.

### `P7` · Scaffold fade pattern

**Bucket** — P — Pedagogy

**What pass requires** — Scaffolds are not uniformly present across all problems. Some problems have more support than others, creating a visible reduction in scaffold density within the tier or across the problem set (e.g., the last tasks in each tier carry less embedded support than the first).

### `P8` · Flexible grouping language

**Bucket** — P — Pedagogy

**What pass requires** — Teacher plan states tier assignments explicitly, justifies how students are assigned to tiers (what evidence places a student in a tier), and includes language indicating groups are revisable based on formative evidence from this lesson (e.g., exit-ticket-driven regrouping) — not static ability tracks.

### `R1` · Cognitive demand preserved across tiers

**Bucket** — R — Rigor

**What pass requires** — All three tiers require students to do more than compute or recall: at least one task in each tier asks students to explain, justify, compare, or apply their understanding. No tier is limited to rote procedural steps — name any tier that is.

### `R3` · Student agency prompt on each worksheet

**Bucket** — R — Rigor

**What pass requires** — Each tiered worksheet includes at least one open-ended or self-reflection prompt (e.g., "explain your thinking," "what strategy did you use?", "how confident are you?"). A 'show/explain how you know' prompt attached to a task counts. The prompt appears on all three tiers — name any tier missing it.

**Notes** — Keeps differentiation from becoming rote.

### `O2` · Formative checks included

**Bucket** — O — Output/Format

**What pass requires** — Teacher plan includes at least one mid-lesson check point more specific than "circulate and observe" — a check with a defined trigger, artifact, or decision — plus a tiered exit ticket whose sort buckets (Got it / Almost there / Needs re-teaching) carry explicit criteria distinguishing them.

### `O3` · Anchor activity included

**Bucket** — O — Output/Format

**What pass requires** — Teacher plan includes an explicitly labeled anchor activity (e.g., "Early finishers:" or "Anchor activity:") that asks students to produce something — an explanation, a creation, a connection, or a question — rather than complete additional practice problems identical to the main worksheet.

### `O4` · Teacher rationale notes

**Bucket** — O — Output/Format

**What pass requires** — Teacher plan includes at least two explicitly labeled rationale notes (e.g., "Why this works:", "Pedagogical note:") that each name a specific tier design choice and state a reason for it. Generic statements ("scaffolds help learners") do not count.

### `O6` · Teacher/student artifact alignment

**Bucket** — O — Output/Format

**What pass requires** — Two-direction cross-read. Direction 1: every task or activity the teacher plan describes for students has a corresponding student-facing version in at least one worksheet (anchor activities included — if the plan says early finishers build or write something, a printed task for it must exist somewhere). Direction 2: every discrete task on each worksheet appears in the teacher plan's description of that tier. List every mismatch with the document and task quoted; pass only if BOTH directions are clean.

**Notes** — Independent check of teacher/student mismatch — a common failure mode.

### `O7` · Closing next-steps section present

**Bucket** — O — Output/Format

**What pass requires** — Teacher plan closes with a labeled section (heading or inline label using terms such as 'Next Steps', 'Follow-up options', 'Iterations available', or equivalent) that provides substantive, lesson-specific guidance. The section must address at least three distinct outcomes or actions — e.g., what to do for each exit-ticket sort bucket, or what follow-up options are available for specific learner needs. Guidance must be specific to this lesson's content and student evidence; generic placeholders ('let me know if you want changes', 'adjust as needed') do not count. Pass if a teacher could act on the section without additional context.

### `M2` · Learner needs question

**Bucket** — M — Model Scaffolding

**What pass requires** — Before or alongside first generation, asks about specific learner needs (multi-lingual learner, individual education plan, etc) or explicitly states that universal design defaults are applied if no information is provided. Silence on learner needs is a fail.

### `M3` · Asks scope if needed

**Bucket** — M — Model Scaffolding

**What pass requires** — Asks for tier scope if unspecified; auto-passes when scope is already given in the prompt.

### `O8` · Information density

**Bucket** — O — Output / Formatting

**What pass requires** — The teacher plan presents parallel tier content (what each tier does, scaffolds, worksheet tasks) in a comparison table — never three stacked multi-sentence per-tier paragraph blocks. Paragraphs stay within roughly 3 sentences; longer material is bulleted or tabled. Asides such as misconception watch-fors and conferring moves appear as distinct callouts or notes, not sentences buried inside paragraphs. Fail = per-tier paragraph stacks, any wall-of-text paragraph, or watch-fors/conferring moves embedded mid-paragraph.

### `O9` · Writing space matches demand

**Bucket** — O — Output / Formatting

**What pass requires** — Every student task, exit ticket, and extension prompt on every worksheet is followed by visible blank writing space (or writable organizer rows) proportionate to the expected response: multi-sentence explanations get generous open space, fill-in rows get a line or two, and answer columns in organizers are at least as wide as their prompt columns. Fail = any prompt demanding written work with no adjacent space, organizer rows too short to write in, or an answer column squeezed narrower than its prompt column.
