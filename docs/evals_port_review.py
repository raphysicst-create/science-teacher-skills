#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 science-teacher-skills contributors
# SPDX-License-Identifier: Apache-2.0

"""evals 루브릭 한국판 보정 — 원본 대 보정 전수 대조 페이지 생성기.

업스트림 `k12-teacher-skills`의 채점 루브릭을 2022 개정 교육과정(과학 전용)으로
보정하면서 무엇을 왜 바꿨는지를 항목 단위로 남긴다. 변경 성격을 3분류(A/B/C)로
표시하는데, 특히 **B(우리 스펙 편을 든 것)**를 눈에 띄게 두는 것이 이 문서의 목적이다 —
"자를 스스로 고칠 수 있으면 그 자로 잰 게 무슨 의미냐"는 물음에 답하려면 그 분류가
숨겨져서는 안 된다.

사용:
    python docs/evals_port_review.py [BEFORE_REF] > docs/evals-port-review.html

BEFORE_REF 기본값은 보정 직전 커밋(a76d683). 현재본은 작업 트리에서 읽는다.
표준 라이브러리만 쓴다 (렌더러·검증기와 동일한 의존성 원칙).
"""
from __future__ import annotations

import csv
import html
import io
import subprocess
import sys

BEFORE_REF_DEFAULT = "a76d683"

# (현재 경로, 보정 전 경로, 화면 라벨)
FILES = [
    ("evals/ko12-lesson-planning/rubrics/science.csv",
     "evals/k12-lesson-planning/rubrics/science.csv", "수업 설계 · 과학 전용"),
    ("evals/ko12-lesson-planning/rubrics/shared.csv",
     "evals/k12-lesson-planning/rubrics/shared.csv", "수업 설계 · 공통"),
    ("evals/ko12-lesson-differentiation/rubrics/differentiation.csv",
     "evals/k12-lesson-differentiation/rubrics/differentiation.csv", "수준별 차별화"),
    ("evals/ko12-lesson-differentiation/rubrics/clarifying_question.csv",
     "evals/k12-lesson-differentiation/rubrics/clarifying_question.csv", "확인 질문 행동"),
]

CLSNAME = {"A": "측정 대상 부재", "B": "우리 스펙 편", "C": "계측기 수리"}

# 변경 항목 판정. 키는 (파일명, 항목 ID).
#   A — 한국 체제나 학습맵 데이터에 측정 대상이 없어 판정이 상수였던 것
#   B — 원본 기준과 이 프로젝트의 science.md가 충돌해 우리 쪽으로 해소한 것 (가장 취약)
#   C — 판정자가 찾는 문자열과 실제 렌더 문자열이 달라 매칭에 실패하던 것 (엄격성 불변)
CLASSIFICATION = {
    ("science.csv", "P-S1"): ("A", "NGSS 3차원은 한국 체제에 없다"),
    ("science.csv", "P-S2"): ("C", "용어만 — 앵커 현상·고등학교"),
    ("science.csv", "P-S3"): ("C", "단계명만 한국어로. 기준 자체는 그대로"),
    ("science.csv", "P-S4"): ("A", "횡단개념(CCC)이 한국 체제에 없다"),
    ("science.csv", "P-S5"): ("B", "science.md의 성취기준 유형 분기를 근거로 조건부화"),
    ("science.csv", "R-S1"): ("B", "학년군별 글쓰기 형식 게이팅을 science.md에서 가져옴"),
    ("science.csv", "R-S2"): ("C", "Gr6–12 → 중·고"),
    ("shared.csv", "P1"): ("A", "초등 레코드에 원문이 실려 있지 않다 (데이터 사실)"),
    ("shared.csv", "P2"): ("A", "학습맵에 선수 edge가 없는 성취기준이 흔하다"),
    ("shared.csv", "P3"): ("B", "Big Idea/SWBAT 틀을 3범주 채택에 맞춰 재조준"),
    ("shared.csv", "P4a"): ("B", "science.md의 상한 3개를 근거로 하한을 2로"),
    ("shared.csv", "P4b"): ("C", "열 이름을 렌더되는 한국어로"),
    ("shared.csv", "P6b"): ("B", "범주 귀속 요구를 science.md에서 추가"),
    ("shared.csv", "R3"): ("B", "정리 문항 규격을 science.md에서 가져옴"),
    ("shared.csv", "O3b"): ("C", "분류 칸 라벨 문자열"),
    ("shared.csv", "M3"): ("C", "예시 교체 — 주(state) 적응 삭제"),
    ("shared.csv", "M5"): ("A", "IM/OpenSciEd가 한국에 없다"),
    ("differentiation.csv", "P1"): ("C", "수준명 → 가·나·다 모둠"),
    ("differentiation.csv", "P2"): ("A", "학습맵 edge 부재"),
    ("differentiation.csv", "P4"): ("C", "수준명"),
    ("differentiation.csv", "P6"): ("C", "수학·국어 예시 → 과학 표현"),
    ("differentiation.csv", "P9"): ("A", "커리큘럼 누출 → 검정 교과서 중립"),
    ("differentiation.csv", "R2"): ("C", "수준명"),
    ("differentiation.csv", "O1"): ("C", "수준명"),
    ("differentiation.csv", "O5"): ("C", "수준명 + 이중언어 → 가정에서 쓰는 언어"),
    ("differentiation.csv", "M1"): ("A", "초등 원문 비verbatim"),
    ("differentiation.csv", "M4"): ("C", "WIDA → 다문화·개별화교육계획"),
    ("differentiation.csv", "O10"): ("C", "교사 용어 목록을 한국어로"),
    ("differentiation.csv", "P10"): ("A", "three-dimensional map → 범주별 학습 목표"),
    ("clarifying_question.csv", "M-CLARIFY-STATE"): ("A", "한국에 주(state)가 없다"),
    ("clarifying_question.csv", "M-CLARIFY-GRADE"): ("A", "대체 — 학년이 밴드 분기를 결정"),
    ("clarifying_question.csv", "M-CLARIFY-G12"): ("A", "신설 — ADR-2 초1–2 특례"),
}

# 완화가 아니라 오히려 엄격해진 변경 — 대조에서 숨기지 않는다.
STRICTER = {
    ("shared.csv", "P1"): "verbatim 주장 시 FAIL이 새로 생김 — 더 엄격",
    ("shared.csv", "P4a"): "상한 초과(4개 이상)가 새로 FAIL — 한쪽은 더 엄격",
}

e = html.escape


def parse(text: str) -> dict:
    rows = list(csv.reader(io.StringIO(text)))
    return {r[0]: {"id": r[0], "bucket": r[1], "criterion": r[2],
                   "requires": r[3], "notes": r[4], "cond": r[5]} for r in rows[1:]}


def collect(before_ref: str) -> list:
    out = []
    for cur_path, old_path, label in FILES:
        old = parse(subprocess.run(["git", "show", f"{before_ref}:{old_path}"],
                                   capture_output=True, text=True, encoding="utf-8",
                                   check=True).stdout)
        new = parse(io.open(cur_path, encoding="utf-8").read())
        items = []
        for key in list(old) + [k for k in new if k not in old]:
            a, b = old.get(key), new.get(key)
            if a and b:
                fields = ("criterion", "requires", "notes", "cond")
                status = "same" if all(a[f] == b[f] for f in fields) else "changed"
            else:
                status = "removed" if a else "added"
            name = cur_path.rsplit("/", 1)[-1]
            entry = {"id": key, "status": status, "before": a, "after": b}
            if status != "same":
                cls, why = CLASSIFICATION[(name, key)]
                entry["cls"], entry["why"] = cls, why
                entry["strict"] = STRICTER.get((name, key), "")
            items.append(entry)
        out.append({
            "file": cur_path.rsplit("/", 1)[-1], "label": label,
            "path_before": old_path, "path_after": cur_path,
            "n_after": len(new), "items": items,
            "changed": sum(1 for i in items if i["status"] == "changed"),
            "same": sum(1 for i in items if i["status"] == "same"),
            "added": sum(1 for i in items if i["status"] == "added"),
            "removed": sum(1 for i in items if i["status"] == "removed"),
        })
    return out


def pane(side: str, r, label: str) -> str:
    if not r:
        return ('<div class="pane %s empty"><span class="pane-h">%s</span>'
                '<p class="none">항목 없음</p></div>' % (side, label))
    cond = ('<div class="fld"><span class="k">Conditional</span><code>%s</code></div>'
            % e(r["cond"])) if r["cond"] else ""
    notes = ('<div class="fld"><span class="k">Notes</span><p class="nt">%s</p></div>'
             % e(r["notes"])) if r["notes"] else ""
    return ('<div class="pane %s"><span class="pane-h">%s</span><h4>%s</h4>'
            '<div class="fld"><span class="k">What pass requires</span><p>%s</p></div>'
            '%s%s</div>') % (side, label, e(r["criterion"]), e(r["requires"]), notes, cond)


def sections(data: list) -> str:
    secs = []
    for f in data:
        cards = []
        for it in (i for i in f["items"] if i["status"] != "same"):
            cls, status = it["cls"], it["status"]
            badge = {"changed": "변경", "added": "신설", "removed": "삭제"}[status]
            strict = ('<p class="strict">&uarr; %s</p>' % e(it["strict"])) if it["strict"] else ""
            cards.append(
                '<article class="card c-%s" data-cls="%s" data-st="%s">'
                '<header class="ch"><code class="id">%s</code>'
                '<span class="badge b-%s">%s</span>'
                '<span class="badge cls">%s &middot; %s</span>'
                '<p class="why">%s</p>%s</header>'
                '<div class="panes">%s%s</div></article>'
                % (cls, cls, status, e(it["id"]), status, badge, cls, CLSNAME[cls],
                   e(it["why"]), strict,
                   pane("before", it["before"], "원본 (업스트림)"),
                   pane("after", it["after"], "보정 (한국판)")))
        same = [i["id"] for i in f["items"] if i["status"] == "same"]
        samewrap = ""
        if same:
            chips = "".join('<code class="chip">%s</code>' % e(i) for i in same)
            samewrap = ('<div class="samewrap"><p class="samehd">원본 그대로 둔 %d항목</p>'
                        '<div class="chips">%s</div></div>' % (len(same), chips))
        extra = ""
        if f["added"]:
            extra += " &middot; 신설 <b>%d</b>" % f["added"]
        if f["removed"]:
            extra += " &middot; 삭제 <b>%d</b>" % f["removed"]
        secs.append(
            '<section class="filesec"><header class="fh"><h2>%s</h2>'
            '<p class="paths"><code class="pb">%s</code><span class="arw">&rarr;</span>'
            '<code class="pa">%s</code></p>'
            '<p class="fstat"><b>%d</b> 항목 &middot; 변경 <b>%d</b> &middot; 유지 <b>%d</b>%s</p>'
            '</header>%s%s</section>'
            % (e(f["label"]), e(f["path_before"]), e(f["path_after"]), f["n_after"],
               f["changed"], f["same"], extra, "".join(cards), samewrap))
    return "".join(secs)


CSS = """
:root{--paper:#F5F7F8;--surface:#fff;--sunk:#EDF1F3;--ink:#14181C;--ink2:#47525E;--ink3:#7C8894;
--line:#DDE4E9;--before:#5C6B7F;--beforebg:#EEF1F4;--after:#0E6F62;--afterbg:#E4F0EE;
--flag:#93491F;--flagbg:#F6EBE3;--radius:10px}
@media (prefers-color-scheme:dark){:root{--paper:#0F1316;--surface:#171C21;--sunk:#12171B;--ink:#E9EEF2;
--ink2:#A6B2BD;--ink3:#6C7883;--line:#28313A;--before:#93A3B5;--beforebg:#1A2027;--after:#4FBFA9;
--afterbg:#11241F;--flag:#D68F60;--flagbg:#2A1C13}}
:root[data-theme="dark"]{--paper:#0F1316;--surface:#171C21;--sunk:#12171B;--ink:#E9EEF2;--ink2:#A6B2BD;
--ink3:#6C7883;--line:#28313A;--before:#93A3B5;--beforebg:#1A2027;--after:#4FBFA9;--afterbg:#11241F;
--flag:#D68F60;--flagbg:#2A1C13}
:root[data-theme="light"]{--paper:#F5F7F8;--surface:#fff;--sunk:#EDF1F3;--ink:#14181C;--ink2:#47525E;
--ink3:#7C8894;--line:#DDE4E9;--before:#5C6B7F;--beforebg:#EEF1F4;--after:#0E6F62;--afterbg:#E4F0EE;
--flag:#93491F;--flagbg:#F6EBE3}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);
font-family:"Pretendard","Malgun Gothic","Apple SD Gothic Neo",system-ui,-apple-system,"Segoe UI",sans-serif;
line-height:1.65;-webkit-font-smoothing:antialiased}
code,.mono{font-family:ui-monospace,"Cascadia Mono",Consolas,"DejaVu Sans Mono",monospace}
.wrap{max-width:1180px;margin:0 auto;padding:clamp(28px,5vw,64px) clamp(16px,4vw,40px) 96px}
header.top{display:flex;flex-direction:column;gap:14px;padding-bottom:26px;border-bottom:2px solid var(--ink)}
.eyebrow{font-size:11.5px;letter-spacing:.16em;text-transform:uppercase;color:var(--ink3);
font-family:ui-monospace,Consolas,monospace;margin:0}
h1{margin:0;font-size:clamp(27px,4.4vw,40px);line-height:1.15;letter-spacing:-.022em;
text-wrap:balance;font-weight:700}
.lede{margin:0;max-width:64ch;color:var(--ink2);font-size:16px}
.commits{display:flex;flex-wrap:wrap;gap:8px;align-items:center;font-size:12.5px;color:var(--ink3);margin:0}
.commits code{background:var(--sunk);padding:2px 7px;border-radius:5px;border:1px solid var(--line);color:var(--ink2)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(112px,1fr));gap:1px;background:var(--line);
border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;margin:30px 0 0}
.stat{background:var(--surface);padding:15px 16px}
.stat b{display:block;font-size:27px;font-weight:700;letter-spacing:-.02em;
font-variant-numeric:tabular-nums;line-height:1.1}
.stat span{font-size:11.5px;color:var(--ink3);letter-spacing:.04em}
.stat.s-chg b{color:var(--after)}
.stat.s-same b{color:var(--ink3)}
.legend{margin:30px 0 0;padding:20px 22px;background:var(--surface);border:1px solid var(--line);
border-radius:var(--radius)}
.legend h3{margin:0 0 4px;font-size:14px;letter-spacing:-.01em}
.legend>p{margin:0 0 16px;font-size:13.5px;color:var(--ink2);max-width:70ch}
.lgrid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px}
.lg{padding:13px 15px;border-radius:8px;border:1px solid var(--line);background:var(--sunk)}
.lg .t{display:flex;align-items:baseline;gap:8px;margin-bottom:5px}
.lg .t b{font-size:13.5px}
.lg .t em{font-style:normal;font-size:19px;font-weight:700;font-variant-numeric:tabular-nums}
.lg p{margin:0;font-size:12.5px;color:var(--ink2);line-height:1.55}
.lg.A{border-left:3px solid var(--after)}
.lg.A .t em{color:var(--after)}
.lg.B{border-left:3px solid var(--flag);background:var(--flagbg)}
.lg.B .t em{color:var(--flag)}
.lg.C{border-left:3px solid var(--before)}
.lg.C .t em{color:var(--before)}
.filters{position:sticky;top:0;z-index:5;display:flex;flex-wrap:wrap;gap:7px;padding:13px 0;margin:32px 0 0;
background:var(--paper);border-bottom:1px solid var(--line)}
.filters button{font:inherit;font-size:13px;padding:6px 13px;border-radius:99px;border:1px solid var(--line);
background:var(--surface);color:var(--ink2);cursor:pointer}
.filters button:hover{border-color:var(--ink3);color:var(--ink)}
.filters button[aria-pressed="true"]{background:var(--ink);color:var(--paper);border-color:var(--ink)}
.filters button:focus-visible{outline:2px solid var(--after);outline-offset:2px}
.filesec{margin-top:46px}
.fh{padding-bottom:14px;border-bottom:1px solid var(--line);margin-bottom:22px}
.fh h2{margin:0 0 7px;font-size:20px;letter-spacing:-.018em}
.paths{margin:0 0 6px;display:flex;flex-wrap:wrap;align-items:center;gap:8px;font-size:12px}
.paths code{padding:2px 7px;border-radius:5px;border:1px solid var(--line)}
.pb{color:var(--before);background:var(--beforebg);text-decoration:line-through;text-decoration-thickness:1px}
.pa{color:var(--after);background:var(--afterbg)}
.arw{color:var(--ink3)}
.fstat{margin:0;font-size:12.5px;color:var(--ink3)}
.fstat b{color:var(--ink2);font-variant-numeric:tabular-nums}
.card{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);
margin-bottom:16px;overflow:hidden}
.card.c-B{border-color:color-mix(in srgb,var(--flag) 42%,var(--line))}
.ch{padding:14px 18px;border-bottom:1px solid var(--line);display:flex;flex-wrap:wrap;align-items:center;gap:8px}
.ch .id{font-size:13.5px;font-weight:700;color:var(--ink);background:var(--sunk);padding:3px 9px;
border-radius:5px;border:1px solid var(--line)}
.badge{font-size:11px;padding:3px 9px;border-radius:99px;letter-spacing:.03em;
font-family:ui-monospace,Consolas,monospace;border:1px solid transparent}
.b-changed,.b-added{background:var(--afterbg);color:var(--after);
border-color:color-mix(in srgb,var(--after) 30%,transparent)}
.b-removed{background:var(--beforebg);color:var(--before);border-color:var(--line)}
.badge.cls{background:var(--sunk);color:var(--ink2);border-color:var(--line)}
.c-B .badge.cls{background:var(--flagbg);color:var(--flag);
border-color:color-mix(in srgb,var(--flag) 32%,transparent)}
.why{flex:1 1 100%;margin:2px 0 0;font-size:12.5px;color:var(--ink3)}
.strict{flex:1 1 100%;margin:3px 0 0;font-size:12.5px;color:var(--flag);font-weight:600}
.panes{display:grid;grid-template-columns:1fr 1fr}
.pane{padding:16px 18px;min-width:0}
.pane.before{background:var(--sunk);border-right:1px solid var(--line)}
.pane-h{display:block;font-size:10.5px;letter-spacing:.14em;text-transform:uppercase;margin-bottom:9px;
font-family:ui-monospace,Consolas,monospace}
.before .pane-h{color:var(--before)}
.after .pane-h{color:var(--after)}
.pane h4{margin:0 0 11px;font-size:14.5px;line-height:1.4;letter-spacing:-.01em;text-wrap:balance}
.before h4{color:var(--ink2)}
.fld{margin-bottom:11px}
.fld .k{display:block;font-size:10.5px;letter-spacing:.08em;color:var(--ink3);margin-bottom:3px;
font-family:ui-monospace,Consolas,monospace}
.fld p{margin:0;font-size:13.5px;line-height:1.62;color:var(--ink2)}
.fld p.nt{font-size:12.5px;color:var(--ink3)}
.fld code{font-size:12px;background:var(--sunk);padding:2px 7px;border-radius:4px;border:1px solid var(--line)}
.pane.empty{display:flex;flex-direction:column}
.none{margin:0;font-size:13px;color:var(--ink3);font-style:italic}
.samewrap{margin-top:20px;padding:16px 18px;background:var(--sunk);border:1px dashed var(--line);
border-radius:var(--radius)}
.samehd{margin:0 0 10px;font-size:12.5px;color:var(--ink3)}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{font-size:11.5px;padding:3px 8px;border-radius:5px;background:var(--surface);
border:1px solid var(--line);color:var(--ink3)}
footer{margin-top:56px;padding-top:22px;border-top:1px solid var(--line);font-size:12.5px;
color:var(--ink3);max-width:74ch}
footer b{color:var(--ink2)}
footer p{margin:0 0 12px}
.hide{display:none!important}
@media (max-width:820px){.panes{grid-template-columns:1fr}
.pane.before{border-right:0;border-bottom:1px solid var(--line)}}
@media (prefers-reduced-motion:reduce){*{transition:none!important;animation:none!important}}
"""

JS = """
var btns = [].slice.call(document.querySelectorAll('.filters button'));
btns.forEach(function (b) {
  b.addEventListener('click', function () {
    btns.forEach(function (x) { x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
    var f = b.dataset.f;
    document.querySelectorAll('.card').forEach(function (c) {
      c.classList.toggle('hide', f !== 'all' && c.dataset.cls !== f);
    });
    document.querySelectorAll('.samewrap').forEach(function (s) {
      s.classList.toggle('hide', f !== 'all');
    });
    document.querySelectorAll('.filesec').forEach(function (s) {
      var any = [].slice.call(s.querySelectorAll('.card')).some(function (c) {
        return !c.classList.contains('hide');
      });
      s.classList.toggle('hide', !any);
    });
  });
});
"""

PAGE = """<title>evals 루브릭 — 원본 대 보정 대조</title>
<style>%s</style>
<div class="wrap">
<header class="top">
  <p class="eyebrow">science-teacher-skills &middot; evals</p>
  <h1>업스트림 루브릭을 한국 교육과정으로 재교정한 기록</h1>
  <p class="lede">Anthropic <code>k12-teacher-skills</code>의 채점 루브릭을 2022 개정 교육과정(과학 전용)에
  맞춰 보정했다. 아래는 항목 단위 전수 대조다 — 무엇을 왜 바꿨는지, 그리고
  <b>어떤 변경이 스스로에게 유리한 방향인지</b>까지 표시한다.</p>
  <p class="commits">대조 기준 <code>%s</code> <span class="arw">&rarr;</span> <code>%s</code>
  <span>&middot;</span> 이 루브릭은 LLM-judge용이며 결정론 검증은
  <code>tests/check_lesson.py</code>가 따로 담당한다</p>
</header>

<div class="stats">
  <div class="stat"><b>%d</b><span>현재 항목</span></div>
  <div class="stat s-chg"><b>%d</b><span>변경</span></div>
  <div class="stat s-same"><b>%d</b><span>원본 그대로</span></div>
  <div class="stat"><b>%d</b><span>신설</span></div>
  <div class="stat"><b>%d</b><span>삭제</span></div>
</div>

<section class="legend">
  <h3>변경 3분류</h3>
  <p>&ldquo;자를 내가 고칠 수 있으면 그 자로 잰 게 무슨 의미냐&rdquo;는 물음에 답하려면 변경의 성격을 갈라야 한다.
  아래 <b>B</b>가 그 물음이 실제로 겨누는 지점이다.</p>
  <div class="lgrid">
    <div class="lg A"><div class="t"><em>%d</em><b>A &middot; 측정 대상 부재</b></div>
      <p>한국 체제나 학습맵 데이터에 그 대상이 존재하지 않아, 판정 결과가 수업 품질과 무관하게
      상수였던 항목. 기준을 낮춘 것이 아니라 측정 불가를 해소했다.</p></div>
    <div class="lg B"><div class="t"><em>%d</em><b>B &middot; 우리 스펙 편을 든 것</b></div>
      <p>원본 기준과 이 프로젝트의 <code>science.md</code>가 충돌해 우리 쪽으로 해소한 항목.
      <b>가장 취약한 분류다</b> — 근거는 실질적이지만, 자기 스펙을 근거로 상류 기준을 굽힌 것이 맞다.</p></div>
    <div class="lg C"><div class="t"><em>%d</em><b>C &middot; 계측기 수리</b></div>
      <p>판정자가 찾는 문자열과 실제 렌더되는 문자열이 달라 매칭에 실패하던 항목
      (예: <code>Below tier</code> ↔ <code>가 모둠</code>). 엄격성은 불변.</p></div>
  </div>
</section>

<nav class="filters" aria-label="변경 분류 필터">
  <button data-f="all" aria-pressed="true">전체</button>
  <button data-f="A" aria-pressed="false">A &middot; 측정 대상 부재 %d</button>
  <button data-f="B" aria-pressed="false">B &middot; 우리 스펙 편 %d</button>
  <button data-f="C" aria-pressed="false">C &middot; 계측기 수리 %d</button>
</nav>

%s

<footer>
<p><b>이 대조가 증명하지 못하는 것.</b> 이 루브릭은 아직 <b>한 번도 실채점되지 않았다</b> —
점수 기록 0건. 현재 <code>evals/</code>는 측정이 아니라 명세다. 또한 하네스의
<code>claude plugin eval</code>은 <code>case.yaml</code> 또는 <code>prompt.md</code> +
<code>graders/*.md</code>를 기대하는데, 이 저장소는 업스트림 형식인 <code>rubrics/*.csv</code>라
실행기가 인식하지 못한다.</p>
<p>보정의 정당성을 외부에서 검증하려면 <code>--ablation with-without</code>으로 플러그인 없는
baseline과의 점수 델타를 봐야 한다. 루브릭을 자기 유리하게 느슨히 하면 baseline 점수도 함께 올라
델타가 사라지므로, 편법이 자기 손해가 되는 구조다.</p>
<p>이 페이지는 <code>docs/evals_port_review.py</code>가 생성한다. 판정(A/B/C)은 그 스크립트의
<code>CLASSIFICATION</code> 표에 있다 — 판정을 바꾸려면 거기를 고치고 다시 생성한다.</p>
</footer>
</div>
<script>%s</script>"""


def main() -> int:
    before_ref = sys.argv[1] if len(sys.argv) > 1 else BEFORE_REF_DEFAULT
    data = collect(before_ref)
    n = {"A": 0, "B": 0, "C": 0}
    for f in data:
        for i in f["items"]:
            if i["status"] != "same":
                n[i["cls"]] += 1
    total = sum(f["n_after"] for f in data)
    sys.stdout.write(PAGE % (
        CSS, before_ref, "현재 작업 트리", total,
        sum(f["changed"] for f in data), sum(f["same"] for f in data),
        sum(f["added"] for f in data), sum(f["removed"] for f in data),
        n["A"], n["B"], n["C"], n["A"], n["B"], n["C"],
        sections(data), JS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
