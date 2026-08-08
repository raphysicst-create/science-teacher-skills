#!/usr/bin/env python3
# Copyright 2026 science-teacher-skills contributors
# SPDX-License-Identifier: Apache-2.0

"""HWPX 품질 검사기 — 구조·서식·내용·HTML 파리티를 결정론적으로 검사한다.

hwpx-quality-loop(docs/hwpx-quality-loop.md)의 측정 장치다. 렌더러를 고치기 전에
이 검사기로 기준선을 재고, 고친 뒤에 다시 재서 수렴을 판단한다. 표준 라이브러리만
쓴다(저장소 원칙). 한컴 실열림 검증(COM)은 여기서 하지 않는다 — 로컬 툴체인
(.claude/skills/hwpx, gitignored)의 몫이다.

검사 항목 ID (루프 문서·수정 커밋이 이 ID로 결함을 참조한다):
  구조   S1 zip·mimetype  S2 XML well-formed  S3 manifest 정합  S4 U+FFFD 없음
         S5 version.xml/settings.xml 존재
  서식   F1 폰트 참조 무결성(dangling fontRef 없음)  F2 charPr/paraPr/borderFill 참조 무결성
         F3 라틴 본문 폰트가 고정폭이 아님  F4 목록 문단 내어쓰기(음수 intent + 양수 left)
         F5 콜아웃 kind별 테두리색 구분 정의  F6 헤더 행 있는 표의 repeatHeader
         F7 표 폭 == 본문 폭  F8 쪽번호 컨트롤 존재  F9 문서 끝 커서 자리(표로 끝나지 않음)
         F10 스타일 정의·사용(제목 스타일이 정의되고 문단이 실제로 참조)
         F11 표 높이 선언 정합(행 내 셀 높이 일치, 표 전체 높이 == 행 높이 합)
         F12 빈 답란 열 폭(라벨 열이 학생 답란 열보다 넓으면 안 됨 — V2의 정적판)
  내용   C1 영어 크롬 잔존 없음  C2 마크다운 리터럴(**) 없음  C3 파이프 표 리터럴 없음
  파리티 P1 HTML에 있는 내용이 HWPX에도 있음(누락=fail)
         P2 HWPX에만 있는 내용(정보성 warn)

Usage:
    python tests/check_hwpx_quality.py <outdir> [<outdir> ...] [--json report.json]
    # outdir 안의 모든 *.hwpx를 검사하고, 같은 이름의 .html이 있으면 파리티까지 본다.

Exit 0 = 전 항목 통과(warn 허용), 1 = fail 존재.
"""
from __future__ import annotations

import argparse
import html as html_mod
import json
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

MONOSPACE = {"consolas", "courier new", "courier", "d2coding", "nanumgothiccoding"}
ENGLISH_CHROME = ("Target standard", "Students see", "Builds on",
                  "Mathematical practices")
CALLOUT_KIND_COLORS = ("#5BB088", "#9FB8D8", "#E8C98A")  # special / task / note
ICONS = "⭐📌✋★※◆✅□•▲▼"


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _iter(root, name: str):
    # Element.iter()는 {*} 와일드카드를 지원하지 않는다 — 로컬네임으로 거른다.
    for el in root.iter():
        if isinstance(el.tag, str) and el.tag.rsplit("}", 1)[-1] == name:
            yield el


# ---------------------------------------------------------------------------
# 텍스트 추출·정규화 (파리티용)

_WS = re.compile(r"\s+")
_UNDERS = re.compile(r"[_＿]{2,}")


def norm_line(s: str) -> str:
    s = unicodedata.normalize("NFC", s)
    s = "".join(ch for ch in s if ch not in ICONS)
    s = _UNDERS.sub("_", s).replace("＿", "_")
    s = _WS.sub(" ", s).strip()
    return s


def squash(s: str) -> str:
    return re.sub(r"[\s_]+", "", s)


def hwpx_lines(zf: zipfile.ZipFile) -> list[str]:
    out = []
    for name in sorted(n for n in zf.namelist()
                       if re.fullmatch(r"Contents/section\d+\.xml", n)):
        root = ET.fromstring(zf.read(name))
        for p in _iter(root, "p"):
            texts = [t.text or "" for t in _iter(p, "t")]
            line = norm_line("".join(texts))
            if line:
                out.append(line)
    return out


def html_lines(path: Path) -> list[str]:
    h = path.read_text(encoding="utf-8")
    h = re.sub(r"<(style|script)[^>]*>.*?</\1>", "", h, flags=re.S)
    h = re.sub(r"<[^>]+>", "\n", h)
    h = html_mod.unescape(h)
    return [ln for ln in (norm_line(x) for x in h.split("\n")) if ln]


# ---------------------------------------------------------------------------
# 검사 본체

class Report:
    def __init__(self, path: Path):
        self.path = path
        self.fails: list[str] = []
        self.warns: list[str] = []

    def fail(self, cid: str, msg: str):
        self.fails.append(f"{cid}: {msg}")

    def warn(self, cid: str, msg: str):
        self.warns.append(f"{cid}: {msg}")


def check_structure(zf: zipfile.ZipFile, rep: Report):
    infos = zf.infolist()
    if not infos or infos[0].filename != "mimetype":
        rep.fail("S1", "mimetype이 zip 첫 엔트리가 아님")
    else:
        if infos[0].compress_type != zipfile.ZIP_STORED:
            rep.fail("S1", "mimetype이 STORED가 아님")
        if zf.read("mimetype") != b"application/hwp+zip":
            rep.fail("S1", "mimetype 내용 불일치")
    for info in infos:
        if info.filename.endswith(".xml") or info.filename.endswith(".hpf"):
            try:
                ET.fromstring(zf.read(info.filename))
            except ET.ParseError as e:
                rep.fail("S2", f"{info.filename} XML 파싱 실패: {e}")
    names = set(zf.namelist())
    if "Contents/content.hpf" in names:
        root = ET.fromstring(zf.read("Contents/content.hpf"))
        for item in _iter(root, "item"):
            href = item.get("href", "")
            if href and href not in names:
                rep.fail("S3", f"manifest href 부재: {href}")
    for required in ("version.xml", "settings.xml"):
        if required not in names:
            rep.fail("S5", f"{required} 없음")


def _parse_header(zf: zipfile.ZipFile):
    root = ET.fromstring(zf.read("Contents/header.xml"))
    fontfaces = {}   # lang -> [face, ...]
    for ff in _iter(root, "fontface"):
        faces = [f.get("face", "") for f in _iter(ff, "font")]
        fontfaces[ff.get("lang", "?")] = faces
    char_prs = {}    # id -> element
    for cp in _iter(root, "charPr"):
        char_prs[cp.get("id")] = cp
    para_prs = {}
    for pp in _iter(root, "paraPr"):
        para_prs[pp.get("id")] = pp
    border_fills = {}
    for bf in _iter(root, "borderFill"):
        border_fills[bf.get("id")] = bf
    styles = {}
    for st in _iter(root, "style"):
        styles[st.get("id")] = st
    return fontfaces, char_prs, para_prs, border_fills, styles


def check_format(zf: zipfile.ZipFile, rep: Report):
    fontfaces, char_prs, para_prs, border_fills, styles = _parse_header(zf)

    # F10a — 제목 스타일 정의: 한글 [서식-스타일]에서 제목을 일괄 편집하려면
    # 바탕글 외에 제목 계열 스타일이 정의되어 있어야 한다.
    style_names = {st.get("name") for st in styles.values()}
    missing_styles = {"바탕글", "제목 1", "제목 2"} - style_names
    if missing_styles:
        rep.fail("F10", f"스타일 미정의: {sorted(missing_styles)}")
    # F10b — 스타일이 가리키는 paraPr/charPr가 실제로 정의되어 있어야 한다.
    for sid, st in styles.items():
        if st.get("paraPrIDRef") not in para_prs:
            rep.fail("F10", f"스타일 {sid}: paraPr {st.get('paraPrIDRef')} 미정의")
        if st.get("charPrIDRef") not in char_prs:
            rep.fail("F10", f"스타일 {sid}: charPr {st.get('charPrIDRef')} 미정의")

    # F1 — dangling fontRef
    script_attr = {"hangul": "HANGUL", "latin": "LATIN", "hanja": "HANJA",
                   "japanese": "JAPANESE", "other": "OTHER", "symbol": "SYMBOL",
                   "user": "USER"}
    for cid, cp in char_prs.items():
        for fr in _iter(cp, "fontRef"):
            for attr, lang in script_attr.items():
                idx = fr.get(attr)
                faces = fontfaces.get(lang, [])
                if idx is not None and (not idx.isdigit() or int(idx) >= len(faces)):
                    rep.fail("F1", f"charPr {cid}: {lang} fontRef {idx} "
                                   f"(정의 {len(faces)}개) dangling")

    # F3 — 본문(charPr 0) 라틴 폰트
    cp0 = char_prs.get("0")
    if cp0 is not None:
        for fr in _iter(cp0, "fontRef"):
            idx = fr.get("latin")
            faces = fontfaces.get("LATIN", [])
            if idx and idx.isdigit() and int(idx) < len(faces):
                face = faces[int(idx)].lower()
                if face in MONOSPACE:
                    rep.fail("F3", f"본문 라틴 폰트가 고정폭({faces[int(idx)]})")

    # F5 — 콜아웃 kind 색 정의
    bf_xml = zf.read("Contents/header.xml").decode("utf-8", "replace")
    missing = [c for c in CALLOUT_KIND_COLORS if c not in bf_xml]
    if missing:
        rep.fail("F5", f"kind별 콜아웃 테두리색 미정의: {', '.join(missing)}")

    # 섹션 파싱
    sec_names = sorted(n for n in zf.namelist()
                       if re.fullmatch(r"Contents/section\d+\.xml", n))
    seen_pagenum = False
    for name in sec_names:
        root = ET.fromstring(zf.read(name))

        # F2 — 참조 무결성
        used = {"charPrIDRef": set(), "paraPrIDRef": set(), "borderFillIDRef": set()}
        for el in root.iter():
            for attr, bag in used.items():
                v = el.get(attr)
                if v is not None:
                    bag.add(v)
        for v in used["charPrIDRef"] - set(char_prs):
            rep.fail("F2", f"charPr {v} 미정의 참조")
        for v in used["paraPrIDRef"] - set(para_prs):
            rep.fail("F2", f"paraPr {v} 미정의 참조")
        for v in used["borderFillIDRef"] - set(border_fills):
            rep.fail("F2", f"borderFill {v} 미정의 참조")

        # F10c — 문단의 styleIDRef 참조 무결성 + F10d — 제목 스타일 실사용:
        # 스타일이 정의만 되고 모든 문단이 바탕글(0)이면 일괄 편집 이득이 없다.
        used_styles = {p.get("styleIDRef") for p in _iter(root, "p")
                       if p.get("styleIDRef") is not None}
        for v in sorted(used_styles - set(styles)):
            rep.fail("F10", f"styleIDRef {v} 미정의 참조")
        if used_styles <= {"0"}:
            rep.fail("F10", "모든 문단이 바탕글(0) — 제목 스타일을 참조하는 문단 없음")

        # F4 — 목록 문단 내어쓰기
        bad_list_pp = set()
        for p in _iter(root, "p"):
            first_t = next((t.text or "" for t in _iter(p, "t")), "")
            if re.match(r"^(•|□|\d{1,2}\.)\s", first_t):
                pid = p.get("paraPrIDRef")
                pp = para_prs.get(pid)
                if pp is None:
                    continue
                intent = left = 0
                for m in _iter(pp, "intent"):
                    intent = int(m.get("value", "0"))
                for m in _iter(pp, "left"):
                    left = int(m.get("value", "0"))
                if not (intent < 0 and left > 0):
                    bad_list_pp.add(pid)
        if bad_list_pp:
            rep.fail("F4", f"목록 paraPr {sorted(bad_list_pp)}에 내어쓰기 없음 "
                           "(intent<0, left>0 필요)")

        # F6 — repeatHeader
        for tbl in _iter(root, "tbl"):
            has_header_cell = any(tc.get("header") == "1" for tc in _iter(tbl, "tc"))
            if has_header_cell and tbl.get("repeatHeader") != "1":
                rep.fail("F6", "헤더 행 있는 표에 repeatHeader=1 아님")

        # F11 — 표 높이 선언 정합: 행 안의 셀 높이가 서로 같고, 표 전체 높이
        # (hp:sz)가 행 높이 합과 일치해야 한다. 어긋난 선언은 한글이 재조판하며
        # 무시하므로 쪽 나눔 추정(SectionWriter est)이 그만큼 틀어진다.
        # (렌더러는 표를 중첩하지 않는다 — 중첩 표가 생기면 이 검사를 확장할 것.)
        for ti, tbl in enumerate(_iter(root, "tbl"), 1):
            row_hs: dict[int, list[int]] = {}
            for tc in _iter(tbl, "tc"):
                addr = next(_iter(tc, "cellAddr"), None)
                csz = next(_iter(tc, "cellSz"), None)
                if addr is None or csz is None:
                    continue
                row_hs.setdefault(int(addr.get("rowAddr", "0")), []).append(
                    int(csz.get("height", "0")))
            bad = [r for r, hs in sorted(row_hs.items()) if len(set(hs)) > 1]
            if bad:
                rep.fail("F11", f"표 {ti}: 행 {bad} 안의 셀 높이 불일치")
            declared = next((int(c.get("height", "0")) for c in list(tbl)
                             if isinstance(c.tag, str) and _local(c.tag) == "sz"),
                            None)
            row_sum = sum(hs[0] for hs in row_hs.values() if hs)
            if declared is not None and row_hs and declared != row_sum:
                rep.fail("F11", f"표 {ti}: 전체 높이 {declared} != 행 높이 합 {row_sum}")

        # F12 — 빈 답란 열 폭: 내용 있는 라벨 열과 빈 답란 열이 섞인 표에서
        # 답란 열이 라벨 열보다 좁으면 학생이 쓸 자리가 모자란다(evals V2의 정적판).
        for ti, tbl in enumerate(_iter(root, "tbl"), 1):
            cols: dict[int, dict] = {}
            for tc in _iter(tbl, "tc"):
                if tc.get("header") == "1":
                    continue
                addr = next(_iter(tc, "cellAddr"), None)
                csz = next(_iter(tc, "cellSz"), None)
                if addr is None or csz is None:
                    continue
                ci = int(addr.get("colAddr", "0"))
                text = "".join(t.text or "" for t in _iter(tc, "t"))
                d = cols.setdefault(ci, {"w": int(csz.get("width", "0")),
                                         "blank": True})
                if text.strip().strip("_ "):
                    d["blank"] = False
            blank_w = [d["w"] for d in cols.values() if d["blank"]]
            fill_w = [d["w"] for d in cols.values() if not d["blank"]]
            if blank_w and fill_w and min(blank_w) + 300 < max(fill_w):
                rep.fail("F12", f"표 {ti}: 빈 답란 열 폭 {min(blank_w)} < "
                                f"라벨 열 폭 {max(fill_w)}")

        # F7 — 표 폭 == 본문 폭
        body_w = None
        for pg in _iter(root, "pagePr"):
            w = int(pg.get("width", "0"))
            for m in _iter(pg, "margin"):
                body_w = w - int(m.get("left", "0")) - int(m.get("right", "0"))
        if body_w:
            for tbl in _iter(root, "tbl"):
                sz = next((c for c in list(tbl)
                           if isinstance(c.tag, str) and _local(c.tag) == "sz"), None)
                if sz is not None:
                    tw = int(sz.get("width", "0"))
                    if abs(tw - body_w) > 300:
                        rep.fail("F7", f"표 폭 {tw} != 본문 폭 {body_w}")
                break  # 첫 표만 대표 검사 (전부 같은 상수를 쓴다)

        # F8 — 쪽번호
        if list(_iter(root, "pageNum")):
            seen_pagenum = True

        # F9 — 문서 끝
        top_paras = [p for p in list(root)
                     if isinstance(p.tag, str) and _local(p.tag) == "p"]
        if top_paras:
            last = top_paras[-1]
            has_tbl = bool(list(_iter(last, "tbl")))
            own_text = "".join(t.text or "" for t in _iter(last, "t"))
            if has_tbl and not own_text.strip():
                # 표만 있고 뒤 문단이 없으면 한글에서 표 아래에 커서를 못 놓는다
                rep.fail("F9", "문서가 표로 끝남 (마지막에 빈 문단 필요)")
    if not seen_pagenum:
        rep.fail("F8", "쪽번호(hp:pageNum) 컨트롤 없음")


def check_content(zf: zipfile.ZipFile, rep: Report):
    all_text = []
    for name in sorted(n for n in zf.namelist()
                       if re.fullmatch(r"Contents/section\d+\.xml", n)):
        root = ET.fromstring(zf.read(name))
        all_text += [t.text or "" for t in _iter(root, "t")]
    joined = "\n".join(all_text)
    if "�" in joined:
        rep.fail("S4", "U+FFFD(치환 문자) 존재")
    for chrome in ENGLISH_CHROME:
        if chrome in joined:
            rep.fail("C1", f"영어 크롬 잔존: {chrome!r}")
    if re.search(r"\*\*[^*\n]+\*\*", joined):
        rep.fail("C2", "마크다운 리터럴 ** 잔존")
    if re.search(r"\S \| \S.*\n.*\S \| \S", joined):
        rep.warn("C3", "파이프 표 리터럴 의심")


def check_parity(hwpx_path: Path, rep: Report):
    html_path = hwpx_path.with_suffix(".html")
    if not html_path.exists():
        rep.warn("P1", "짝 HTML 없음 — 파리티 생략")
        return
    with zipfile.ZipFile(hwpx_path) as zf:
        hw = hwpx_lines(zf)
    ht = html_lines(html_path)
    hw_squash = squash(" ".join(hw))
    ht_squash = squash(" ".join(ht))
    missing = [ln for ln in ht
               if len(squash(ln)) >= 6 and squash(ln) not in hw_squash]
    extra = [ln for ln in hw
             if len(squash(ln)) >= 6 and squash(ln) not in ht_squash]
    for ln in missing[:10]:
        rep.fail("P1", f"HTML에만 있음: {ln[:60]}")
    if len(missing) > 10:
        rep.fail("P1", f"... 외 {len(missing) - 10}건")
    for ln in extra[:5]:
        rep.warn("P2", f"HWPX에만 있음: {ln[:60]}")


def check_file(path: Path) -> Report:
    rep = Report(path)
    try:
        with zipfile.ZipFile(path) as zf:
            check_structure(zf, rep)
            check_format(zf, rep)
            check_content(zf, rep)
    except zipfile.BadZipFile:
        rep.fail("S1", "zip이 아님")
        return rep
    check_parity(path, rep)
    return rep


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("outdirs", nargs="+", help="*.hwpx가 있는 디렉터리(들)")
    ap.add_argument("--json", help="기계 판독 리포트를 이 경로에 쓴다")
    args = ap.parse_args()

    reports: list[Report] = []
    for d in args.outdirs:
        base = Path(d)
        files = sorted(base.glob("*.hwpx"))
        if not files:
            print(f"warning: {d}에 hwpx 없음", file=sys.stderr)
        for f in files:
            reports.append(check_file(f))

    total_fail = 0
    for rep in reports:
        status = "FAIL" if rep.fails else ("WARN" if rep.warns else "PASS")
        print(f"[{status}] {rep.path}")
        for m in rep.fails:
            print(f"    FAIL {m}")
        for m in rep.warns:
            print(f"    warn {m}")
        total_fail += len(rep.fails)

    if args.json:
        payload = [{"file": str(r.path), "fails": r.fails, "warns": r.warns}
                   for r in reports]
        Path(args.json).write_text(
            json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8")

    n_bad = sum(1 for r in reports if r.fails)
    print(f"\n{len(reports)}개 파일, FAIL {n_bad}개 파일 / {total_fail}건")
    return 1 if total_fail else 0


if __name__ == "__main__":
    sys.exit(main())
