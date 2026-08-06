#!/usr/bin/env python3
# SPDX-FileCopyrightText: 2026 science-teacher-skills contributors
# SPDX-License-Identifier: Apache-2.0
"""판정 JSON을 루브릭 순서대로 접어 집계표와 무결성 검사를 낸다.

사용: python evals/runs/aggregate.py 2026-08-06
표준 라이브러리만 쓴다. 저장소 어디서 실행해도 동작하도록 이 파일 위치를 기준으로 경로를 푼다.
"""
import csv
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
EVALS = os.path.dirname(HERE)
RUBRICS = [
    os.path.join(EVALS, "ko12-lesson-planning", "rubrics", "shared.csv"),
    os.path.join(EVALS, "ko12-lesson-planning", "rubrics", "science.csv"),
]
MARK = {True: "○", False: "×", "skip": "–"}


def rubric_order():
    order, meta = [], {}
    for path in RUBRICS:
        with open(path, encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                cid = row["ID"].strip()
                order.append(cid)
                meta[cid] = {
                    "criterion": row["Criterion"].strip(),
                    "conditional": row.get("Conditional", "").strip(),
                }
    return order, meta


def main():
    run = sys.argv[1] if len(sys.argv) > 1 else "2026-08-06"
    run_dir = os.path.join(HERE, run)
    files = sorted(f for f in os.listdir(run_dir) if f.startswith("verdicts-"))
    if not files:
        sys.exit(f"판정 파일 없음: {run_dir}")

    order, meta = rubric_order()
    runs = {}
    for fname in files:
        with open(os.path.join(run_dir, fname), encoding="utf-8") as f:
            data = json.load(f)
        runs[data["package"].split("/")[-1]] = {v["id"]: v for v in data["verdicts"]}
    pkgs = list(runs)

    problems = []
    for p, vs in runs.items():
        for cid in sorted(set(vs) - set(order)):
            problems.append(f"{p}: 루브릭에 없는 ID {cid}")
        for cid in sorted(set(order) - set(vs)):
            problems.append(f"{p}: 미판정 {cid}")

    out = [f"# evals 실채점 집계 — {run}", ""]
    out.append(f"루브릭 {len(order)}항목 × 패키지 {len(pkgs)}종 = {len(order) * len(pkgs)}칸")
    out.append("무결성: " + ("OK — 전수 판정, 루브릭 외 ID 0" if not problems else "; ".join(problems)))
    out.append("")

    tot, per = Counter(), {p: Counter() for p in pkgs}
    fails = []
    for cid in order:
        for p in pkgs:
            v = runs[p][cid]
            key = {True: "PASS", False: "FAIL"}.get(v["pass"], "skip")
            tot[key] += 1
            per[p][key] += 1
            if key == "FAIL":
                fails.append((cid, p, v.get("verified", "UNVERIFIED"), v["explanation"]))

    scored = tot["PASS"] + tot["FAIL"]
    out.append(f"PASS {tot['PASS']} / FAIL {tot['FAIL']} / skip {tot['skip']}"
               f" — 채점 칸 기준 통과율 {tot['PASS']}/{scored} = {100 * tot['PASS'] / scored:.1f}%")
    out.append("")
    for p in pkgs:
        c = per[p]
        s = c["PASS"] + c["FAIL"]
        out.append(f"- {p}: {c['PASS']}/{s} ({100 * c['PASS'] / s:.1f}%), skip {c['skip']}")
    out.append("")

    out.append("## FAIL 전건")
    out.append("")
    if not fails:
        out.append("없음")
    for cid, p, verified, ex in fails:
        out.append(f"- **{cid} / {p}** [{verified}] — {meta[cid]['criterion']}")
        out.append(f"  - {ex}")
    out.append("")

    out.append("## 항목 × 패키지")
    out.append("")
    out.append("| ID | 항목 | " + " | ".join(pkgs) + " |")
    out.append("|---|---|" + "---|" * len(pkgs))
    for cid in order:
        cells = []
        for p in pkgs:
            m = MARK.get(runs[p][cid]["pass"], "?")
            cells.append(f"**{m}**" if m == "×" else m)
        out.append(f"| {cid} | {meta[cid]['criterion'][:46]} | " + " | ".join(cells) + " |")
    out.append("")
    out.append("○ pass · × fail · – skip (조건 미충족 또는 판정 불가)")

    text = "\n".join(out) + "\n"
    with open(os.path.join(run_dir, "summary.md"), "w", encoding="utf-8") as f:
        f.write(text)
    sys.stdout.write(text)


if __name__ == "__main__":
    main()
