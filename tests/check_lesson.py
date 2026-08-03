"""수업 패키지 DoD 검사 (DESIGN.md §7 1단계 체크리스트).

사용: python tests/check_lesson.py <lesson.json> <outdir> [--official "성취기준 공식 원문"]

검사 항목:
  1. 렌더 무결성 — documents[] 전부 hwpx·html 쌍으로 나왔고 U+FFFD 없음
  2. 성취기준 verbatim — shared.standard_text가 --official과 문자 단위로 일치
  3. 인용 1회 — 렌더된 교사 문서 전체에서 성취기준 원문이 정확히 한 번
  4. 시간 — phase_header minutes 합계 == shared.duration
  5. 3범주 — 지식·이해 / 과정·기능 / 가치·태도가 수업안에 모두 진술됨

표준 라이브러리만 사용한다 (렌더러와 동일한 의존성 원칙).
"""
import argparse
import json
import os
import sys
import xml.etree.ElementTree as ET
import zipfile

CATEGORIES = ["지식·이해", "과정·기능", "가치·태도"]


def _para_text(p):
    """한 문단(hp:p)의 텍스트.

    텍스트 런(hp:t)은 서식 경계에서 쪼개지므로 문단 안에서 이어 붙인다 — 성취기준 원문
    같은 연속 문자열 검사가 런 분절에 깨지지 않게. 단, 표 셀 안의 문단은 자기 차례에
    따로 세므로 **중첩된 hp:p는 건너뛴다** (안 그러면 표를 품은 문단이 셀 텍스트를 전부
    다시 삼켜 인용 횟수가 두 배로 잡힌다).
    """
    out = []

    def walk(node):
        for child in node:
            if child.tag.endswith("}p"):
                continue
            if child.tag.endswith("}t"):
                out.append("".join(child.itertext()))
            else:
                walk(child)

    walk(p)
    return "".join(out)


def hwpx_text(path):
    """HWPX(zip)의 섹션 XML에서 문단 단위 텍스트 추출 (문서 순서 유지)."""
    parts = []
    with zipfile.ZipFile(path) as z:
        for name in sorted(n for n in z.namelist()
                           if n.startswith("Contents/section") and n.endswith(".xml")):
            root = ET.fromstring(z.read(name))
            for p in root.iter():
                if p.tag.endswith("}p"):
                    run = _para_text(p)
                    if run:
                        parts.append(run)
    return "\n".join(parts)


def walk_blocks(blocks):
    for b in blocks or []:
        if not isinstance(b, dict):
            continue
        yield b
        for key in ("blocks", "left", "right"):
            yield from walk_blocks(b.get(key))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lesson")
    ap.add_argument("outdir")
    ap.add_argument("--official", default=None,
                    help="학습맵 get_standard의 officialText (verbatim 대조용)")
    args = ap.parse_args()

    data = json.load(open(args.lesson, encoding="utf-8"))
    shared = data["shared"]
    failures = []
    texts = {}

    # 1. 렌더 무결성 (hwpx + html 쌍)
    for doc in data["documents"]:
        html_path = os.path.join(args.outdir, doc["id"] + ".html")
        if not (os.path.exists(html_path) and os.path.getsize(html_path) > 0):
            failures.append(f"[렌더] html 누락 또는 빈 파일: {html_path}")
        path = os.path.join(args.outdir, doc["id"] + ".hwpx")
        if not os.path.exists(path):
            failures.append(f"[렌더] 누락: {path}")
            continue
        text = hwpx_text(path)
        texts[doc["id"]] = text
        if "�" in text:
            failures.append(f"[렌더] 깨진 문자: {path}")
        print(f"  렌더 ok: {doc['id']}.hwpx ({len(text)}자)")

    # 2. 성취기준 verbatim
    st = shared["standard_text"]
    if args.official is not None:
        if st == args.official:
            print("  verbatim ok: 학습맵 officialText와 문자 단위 일치")
        else:
            failures.append(f"[verbatim] 불일치\n    lesson: {st!r}\n    official: {args.official!r}")

    # 3. 인용 1회 (교사 문서 기준)
    for doc in data["documents"]:
        if doc.get("audience") != "teacher" or doc["id"] not in texts:
            continue
        n = texts[doc["id"]].count(st)
        if doc["id"] == "lesson_plan" and n != 1:
            failures.append(f"[인용] lesson_plan에 성취기준 원문 {n}회 (1회여야 함)")
        elif doc["id"] != "lesson_plan" and n > 1:
            failures.append(f"[인용] {doc['id']}에 성취기준 원문 {n}회")
    print("  인용 ok: 수업안에 성취기준 원문 1회")

    # 4. 시간
    minutes = [b.get("minutes", 0) for d in data["documents"]
               for s in d["sections"] for b in walk_blocks(s["blocks"])
               if b.get("type") == "phase_header"]
    total, duration = sum(minutes), shared["duration"]
    if total != duration:
        failures.append(f"[시간] 단계 합계 {total}분 != duration {duration}분 ({minutes})")
    else:
        print(f"  시간 ok: {' + '.join(map(str, minutes))} = {total}분")

    # 5. 3범주
    plan = texts.get("lesson_plan", "")
    missing = [c for c in CATEGORIES if c not in plan]
    if missing:
        failures.append(f"[3범주] 수업안에 없음: {', '.join(missing)}")
    else:
        print("  3범주 ok: 지식·이해 / 과정·기능 / 가치·태도 모두 진술됨")

    if failures:
        print("\nFAIL")
        for f in failures:
            print(" -", f)
        sys.exit(1)
    print("\nDoD 체크리스트 통과")


if __name__ == "__main__":
    main()
