#!/usr/bin/env python3
# Copyright 2026 Anthropic, PBC
# Copyright 2026 Learning Commons
# Copyright 2026 science-teacher-skills contributors
# SPDX-License-Identifier: Apache-2.0

"""Render every document in a material-source JSON to editable HWPX (한글) files.

ADR-4 (2026-08-01 개정): lesson.json → OWPML(section0.xml) 직접 생성. 마크다운을
경유하지 않는다 — 치수의 단일 소스는 lesson_common.py의 학년 밴드 프로필과
table_row_height/workspace_height 계산이며, docx 렌더와 같은 값이 1/100pt 단위로
셀 높이(hp:cellSz)에 기록된다.

패키지 구조·페이지 여백·서식 참조표(charPr/paraPr/borderFill)는 파일럿 6종에서
구조 검증 + 한컴 실열림 + PDF 대조를 통과한 보정본(pilot/*/out/*.hwpx)의 값을
기준으로 한다. 교사 대면 크롬(성취기준 라벨, 분 표기)은 한국어로 방출한다 —
docx 렌더러는 동결이라 영어 크롬을 유지하므로, 이 비대칭은 의도된 것이다.

Usage:
    python render_lesson_hwpx.py lesson.json --outdir out
    python render_lesson_hwpx.py lesson.json --only lesson_plan --outdir out
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lesson_common import (  # noqa: E402
    Theme, answer_profile, btype, build_header, coerce_headers, coerce_rows,
    expand_document, label_sep, label_text, md_tokens, meta_text,
    preamble_blocks, resolve_callout_kind, table_row_height, workspace_height,
)
from render_documents import build_doc  # noqa: E402

# ---------------------------------------------------------------------------
# 단위: hp:cellSz·hp:sz·페이지 치수는 1/100 pt. (보정본 실측: 설계표 10800=108pt)
U = 100                      # pt -> OWPML 단위
CONTENT_W = 44000            # 본문 폭 (보정본과 동일)
USABLE_PT = 710.0            # A4 인쇄 가능 높이 근사 (쪽 나눔 판단용)
CELL_MARGIN = 141
DEFAULT_ROW_H = 1500         # 텍스트 행 기본 높이 15pt (내용에 따라 늘어남)

# 교사 대면 크롬 한국어화 (정확 일치 시에만 치환)
CHROME_KO = {
    "Target standard": "성취기준",
    "Builds on": "선수 학습",
    "Students see": "학생에게 보이는 과제",
    "Materials": "준비물",
}

# 콜아웃 아이콘: KS X 1001 문자만 (이모지는 한글 글꼴에서 깨질 수 있어 예방 치환)
CALLOUT_ICON_KO = {"special": "★", "student-task": "※",
                   "teacher-note": "◆", "student-note": "◆"}

# charPr id 대응 (header.xml 정의 순서와 일치해야 함)
CH_BODY, CH_BOLD, CH_ITALIC, CH_BOLDITALIC = 0, 1, 2, 3
CH_SMALL, CH_TITLE, CH_H1, CH_H2, CH_H3 = 4, 5, 6, 7, 8
CH_GRAY_SMALL, CH_GRAY = 11, 12
# paraPr id 대응
PP_BODY, PP_TITLE, PP_SEC, PP_H3, PP_LIST, PP_CENTER, PP_CELL = 0, 1, 2, 3, 5, 8, 9
# borderFill id 대응
BF_NONE, BF_SOLID, BF_SHADE, BF_CALLOUT, BF_RULE, BF_LIGHT = 1, 2, 3, 4, 5, 6


def chrome_ko(label: str) -> str:
    return CHROME_KO.get(label.strip(), label)


# ---------------------------------------------------------------------------
# header.xml — 서식 참조표. 파일럿 보정본의 검증된 정의를 기반으로 borderFill
# 4종(음영·콜아웃·괘선·연한 상자)과 회색 charPr 2종을 추가한 것.

def _char_pr(cid: int, height: int, *, bold=False, italic=False, gothic=False,
             color="#000000") -> str:
    attrs = f'id="{cid}" height="{height}" textColor="{color}" shadeColor="none" ' \
            'useFontSpace="0" useKerning="0" symMark="NONE" borderFillIDRef="1"'
    if bold:
        attrs += ' bold="1"'
    if italic:
        attrs += ' italic="1"'
    f = "1" if gothic else "0"
    tail = "<hh:bold/>" if bold else ""
    return (f'<hh:charPr {attrs}>'
            f'<hh:fontRef hangul="{f}" latin="{f}" hanja="{f}" japanese="{f}" '
            f'other="{f}" symbol="{f}" user="{f}"/>'
            '<hh:ratio hangul="100" latin="100" hanja="100" japanese="100" '
            'other="100" symbol="100" user="100"/>'
            '<hh:spacing hangul="0" latin="0" hanja="0" japanese="0" other="0" '
            'symbol="0" user="0"/>'
            '<hh:relSz hangul="100" latin="100" hanja="100" japanese="100" '
            'other="100" symbol="100" user="100"/>'
            '<hh:offset hangul="0" latin="0" hanja="0" japanese="0" other="0" '
            f'symbol="0" user="0"/>{tail}</hh:charPr>')


def _border_fill(bid: int, *, sides="NONE", width="0.1 mm", color="#000000",
                 bottom_only=False, fill: str | None = None) -> str:
    def edge(side_type, w, c):
        return f'type="{side_type}" width="{w}" color="{c}"'
    if bottom_only:
        l = r = t = edge("NONE", "0.1 mm", "#000000")
        b = edge("SOLID", width, color)
    else:
        l = r = t = b = edge(sides, width, color)
    brush = (f'<hc:fillBrush><hc:winBrush faceColor="{fill}" hatchColor="#999999" '
             'alpha="0"/></hc:fillBrush>') if fill else ""
    return (f'<hh:borderFill id="{bid}" threeD="0" shadow="0" centerLine="NONE" '
            'breakCellSeparateLine="0">'
            '<hh:slash type="NONE" Crooked="0" isCounter="0"/>'
            '<hh:backSlash type="NONE" Crooked="0" isCounter="0"/>'
            f'<hh:leftBorder {l}/><hh:rightBorder {r}/>'
            f'<hh:topBorder {t}/><hh:bottomBorder {b}/>{brush}</hh:borderFill>')


def _para_pr(pid: int, *, align="LEFT", heading="NONE", level=0, indent=0,
             prev=0, nxt=0, spacing=160) -> str:
    head = (f'<hh:heading type="OUTLINE" idRef="0" level="{level}"/>'
            if heading == "OUTLINE" else '<hh:heading type="NONE" idRef="0" level="0"/>')
    return (f'<hh:paraPr id="{pid}" tabPrIDRef="0" condense="0" fontLineHeight="0" '
            'snapToGrid="0" suppressLineNumbers="0" checked="0" textDir="AUTO">'
            f'<hh:align horizontal="{align}" vertical="BASELINE"/>{head}'
            '<hh:breakSetting breakLatinWord="KEEP_WORD" breakNonLatinWord="BREAK_WORD" '
            'widowOrphan="0" keepWithNext="0" keepLines="0" pageBreakBefore="0" '
            'lineWrap="BREAK"/>'
            '<hh:autoSpacing eAsianEng="0" eAsianNum="0"/>'
            f'<hh:margin><hc:intent value="{indent}" unit="HWPUNIT"/>'
            '<hc:left value="0" unit="HWPUNIT"/><hc:right value="0" unit="HWPUNIT"/>'
            f'<hc:prev value="{prev}" unit="HWPUNIT"/>'
            f'<hc:next value="{nxt}" unit="HWPUNIT"/></hh:margin>'
            f'<hh:lineSpacing type="PERCENT" value="{spacing}"/>'
            '<hh:border borderFillIDRef="1" offsetLeft="0" offsetRight="0" '
            'offsetTop="0" offsetBottom="0" connect="0" ignoreMargin="0"/></hh:paraPr>')


def _fontface(lang: str, faces: list[tuple[str, str, int]]) -> str:
    fonts = "".join(
        f'<hh:font id="{i}" face="{face}" type="TTF" isEmbedded="0">'
        f'<hh:typeInfo familyType="{cat}" weight="{w}" proportion="4" contrast="0" '
        'strokeVariation="1" armStyle="1" letterform="1" midline="1" xHeight="1"/>'
        '</hh:font>'
        for i, (face, cat, w) in enumerate(faces))
    return f'<hh:fontface lang="{lang}" fontCnt="{len(faces)}">{fonts}</hh:fontface>'


def build_header_xml() -> str:
    faces_ko = [("함초롬바탕", "FCAT_GOTHIC", 6), ("함초롬돋움", "FCAT_GOTHIC", 6),
                ("HY견고딕", "FCAT_GOTHIC", 9)]
    faces_lat = [("Times New Roman", "FCAT_OLDSTYLE", 5), ("Consolas", "FCAT_MODERN", 5),
                 ("Arial Black", "FCAT_GOTHIC", 9)]
    one = [("함초롬바탕", "FCAT_GOTHIC", 6)]
    gul = [("굴림", "FCAT_GOTHIC", 6)]
    fontfaces = (_fontface("HANGUL", faces_ko) + _fontface("LATIN", faces_lat)
                 + _fontface("HANJA", one) + _fontface("JAPANESE", gul)
                 + _fontface("OTHER", gul) + _fontface("SYMBOL", one)
                 + _fontface("USER", gul))
    border_fills = (
        _border_fill(BF_NONE)
        + _border_fill(BF_SOLID, sides="SOLID", width="0.12 mm")
        + _border_fill(BF_SHADE, sides="SOLID", width="0.12 mm", fill="#F2F4F6")
        + _border_fill(BF_CALLOUT, sides="SOLID", width="0.12 mm", fill="#F6F8F9")
        + _border_fill(BF_RULE, bottom_only=True, width="0.12 mm", color="#C9CFD4")
        + _border_fill(BF_LIGHT, sides="SOLID", width="0.12 mm", color="#C9CFD4"))
    # 본문도 고딕(함초롬돋움) — 원본 디자인이 산세리프(Helvetica) 계열이다.
    char_prs = (
        _char_pr(0, 1000, gothic=True) + _char_pr(1, 1000, bold=True, gothic=True)
        + _char_pr(2, 1000, italic=True, gothic=True)
        + _char_pr(3, 1000, bold=True, italic=True, gothic=True)
        + _char_pr(4, 900, gothic=True) + _char_pr(5, 1800, bold=True, gothic=True)
        + _char_pr(6, 1400, bold=True, gothic=True)
        + _char_pr(7, 1200, bold=True, gothic=True)
        + _char_pr(8, 1100, bold=True, gothic=True)
        + _char_pr(9, 1000, gothic=True) + _char_pr(10, 1000, italic=True, gothic=True)
        + _char_pr(11, 900, gothic=True, color="#666666")
        + _char_pr(12, 1000, gothic=True, color="#666666"))
    # 왼쪽 정렬 — 양쪽 정렬(JUSTIFY)은 한글에서 자간을 불규칙하게 늘린다.
    # 본문 150% + 문단 뒤 7pt: 원본 docx(단행+8pt after)/html(1.55) 리듬의 절충.
    para_prs = (
        _para_pr(0, align="LEFT", spacing=150, nxt=700)
        + _para_pr(1, heading="OUTLINE", level=0, prev=800, nxt=200, spacing=180)
        + _para_pr(2, heading="OUTLINE", level=1, prev=600, nxt=150, spacing=170)
        + _para_pr(3, heading="OUTLINE", level=2, prev=400, nxt=100)
        + _para_pr(4, heading="OUTLINE", level=3, prev=300, nxt=100)
        + _para_pr(5, indent=400, spacing=140, nxt=200)
        + _para_pr(6, indent=600, spacing=150)
        + _para_pr(7, indent=600)
        + _para_pr(8, align="CENTER", spacing=140)
        + _para_pr(9, align="LEFT", spacing=140, nxt=200))   # 표 셀 본문 (촘촘)
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n'
        '<hh:head xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" '
        'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" '
        'xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core" version="1.4" secCnt="1">'
        '<hh:beginNum page="1" footnote="1" endnote="1" pic="1" tbl="1" equation="1"/>'
        '<hh:refList>'
        f'<hh:fontfaces itemCnt="7">{fontfaces}</hh:fontfaces>'
        f'<hh:borderFills itemCnt="6">{border_fills}</hh:borderFills>'
        f'<hh:charProperties itemCnt="13">{char_prs}</hh:charProperties>'
        '<hh:tabProperties itemCnt="0"/>'
        '<hh:numberings itemCnt="1"><hh:numbering id="1" start="0">'
        + "".join(f'<hh:paraHead start="1" level="{lv}" align="LEFT" useInstWidth="1" '
                  'autoIndent="1" widthAdjust="0" textOffsetType="PERCENT" '
                  'textOffset="50" numFormat="DIGIT" charPrIDRef="4294967295" '
                  'checkable="0"/>' for lv in range(1, 8))
        + '</hh:numbering></hh:numberings>'
        '<hh:bullets itemCnt="0"/>'
        f'<hh:paraProperties itemCnt="10">{para_prs}</hh:paraProperties>'
        '<hh:styles itemCnt="1"><hh:style id="0" type="PARA" name="바탕글" '
        'engName="Normal" paraPrIDRef="0" charPrIDRef="0" nextStyleIDRef="0" '
        'langIDRef="1042" lockForm="0"/></hh:styles>'
        '</hh:refList>'
        '<hh:compatibleDocument targetProgram="HWP2018">'
        '<hh:layoutCompatibility/></hh:compatibleDocument></hh:head>')


# ---------------------------------------------------------------------------
# section0.xml 방출기

SEC_PR = (
    '<hp:secPr textDirection="HORIZONTAL" spaceColumns="1134" tabStop="8000" '
    'outlineShapeIDRef="1" memoShapeIDRef="0" textVerticalWidthHead="0" '
    'masterPageCnt="0">'
    '<hp:grid lineGrid="0" charGrid="0" wonggojiFormat="0"/>'
    '<hp:startNum pageStartsOn="BOTH" page="0" pic="0" tbl="0" equation="0"/>'
    '<hp:visibility hideFirstHeader="0" hideFirstFooter="0" hideFirstMasterPage="0" '
    'border="SHOW_ALL" fill="SHOW_ALL" hideFirstPageNum="0" hideFirstEmptyLine="0" '
    'showLineNumber="0"/>'
    # A4 · 보정본 여백 (상단 121.6pt -> 64.4pt 실측 보정값)
    '<hp:pagePr landscape="WIDELY" width="59528" height="84188" gutterType="LEFT_ONLY">'
    '<hp:margin header="1417" footer="2835" gutter="0" left="5670" right="4252" '
    'top="4252" bottom="4252"/></hp:pagePr>'
    '<hp:footNotePr><hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" '
    'suffixChar=")" supscript="0"/>'
    '<hp:noteLine length="-1" type="SOLID" width="0.12 mm" color="#000000"/>'
    '<hp:noteSpacing betweenNotes="283" belowLine="567" aboveLine="850"/>'
    '<hp:numbering type="CONTINUOUS" newNum="1"/>'
    '<hp:placement place="EACH_COLUMN" beneathText="0"/></hp:footNotePr>'
    '<hp:endNotePr><hp:autoNumFormat type="DIGIT" userChar="" prefixChar="" '
    'suffixChar=")" supscript="0"/>'
    '<hp:noteLine length="14692344" type="SOLID" width="0.12 mm" color="#000000"/>'
    '<hp:noteSpacing betweenNotes="0" belowLine="567" aboveLine="850"/>'
    '<hp:numbering type="CONTINUOUS" newNum="1"/>'
    '<hp:placement place="END_OF_DOCUMENT" beneathText="0"/></hp:endNotePr></hp:secPr>'
    '<hp:ctrl><hp:colPr id="" type="NEWSPAPER" layout="LEFT" colCount="1" '
    'sameSz="1" sameGap="0"/></hp:ctrl>')


def _t(text: str) -> str:
    return f"<hp:t>{escape(str(text))}</hp:t>"


def _run(text: str, char_pr: int = CH_BODY) -> str:
    return f'<hp:run charPrIDRef="{char_pr}">{_t(text)}</hp:run>'


def _md_runs(text, base: int = CH_BODY) -> list[list[str]]:
    """미니 마크다운 -> hp:run 목록. 줄바꿈 토큰마다 문단을 나눈다(외부 리스트)."""
    style_map = {CH_BODY: (CH_BODY, CH_BOLD, CH_ITALIC, CH_BOLDITALIC)}
    normal, bold, italic, bolditalic = style_map.get(base, (base, base, base, base))
    paras: list[list[str]] = [[]]
    for txt, attrs in md_tokens(text):
        if attrs.get("break"):
            paras.append([])
            continue
        if not txt:
            continue
        if attrs.get("bold") and attrs.get("italic"):
            cid = bolditalic
        elif attrs.get("bold"):
            cid = bold
        elif attrs.get("italic"):
            cid = italic
        else:
            cid = normal
        paras[-1].append(f'<hp:run charPrIDRef="{cid}">{_t(txt)}</hp:run>')
    return [p for p in paras if p] or [[f'<hp:run charPrIDRef="{base}"><hp:t/></hp:run>']]


class SectionWriter:
    """문단·표를 순서대로 쌓으며 대략적 y 위치를 추적해 쪽 나눔을 결정한다.

    추적은 근사다 — 목적은 잔여 공간에 안 들어가는 큰 고정높이 표(글자처럼
    취급이라 행 분할 불가)가 페이지 하단에 큰 공백을 남기는 것을 막는 것뿐이다."""

    def __init__(self):
        self.parts: list[str] = []
        self.first = True          # 첫 문단이 secPr을 실어야 함
        self.y = 0.0               # 현재 페이지 사용량 (pt, 근사)
        self.tbl_id = 1000
        self.z = 0
        self.force_break = False   # page_break 블록이 다음 문단에 걸어 둠

    # -- 문단 --------------------------------------------------------------
    def para(self, runs: list[str], para_pr: int = PP_BODY, *, est_pt: float = 20.0,
             page_break: bool = False):
        brk = page_break or self.force_break
        self.force_break = False
        attrs = f'paraPrIDRef="{para_pr}" styleIDRef="0"'
        if brk and not self.first:
            attrs += ' pageBreak="1"'
            self.y = 0.0
        body = "".join(runs)
        if self.first:
            body = f'<hp:run charPrIDRef="{CH_TITLE}">{SEC_PR}</hp:run>' + body
            self.first = False
        self.parts.append(f"<hp:p {attrs}>{body}</hp:p>")
        self.y += est_pt
        if self.y > USABLE_PT:
            self.y = est_pt

    def text_para(self, text, base: int = CH_BODY, para_pr: int = PP_BODY):
        for runs in _md_runs(text, base):
            plain = re.sub(r"<[^>]+>", "", "".join(runs))
            lines = max(1, -(-len(plain) // 48))
            self.para(runs, para_pr, est_pt=16.0 * lines + 4)

    # -- 표 ----------------------------------------------------------------
    def _cell(self, col: int, row: int, w: int, h: int, paras: list[str],
              *, border=BF_SOLID, header=False) -> str:
        body = "".join(paras) or f'<hp:p paraPrIDRef="0" styleIDRef="0">' \
                                 f'<hp:run charPrIDRef="0"><hp:t/></hp:run></hp:p>'
        return (f'<hp:tc name="" header="{1 if header else 0}" hasMargin="0" '
                f'protect="0" editable="1" dirty="0" borderFillIDRef="{border}">'
                '<hp:subList id="" textDirection="HORIZONTAL" lineWrap="BREAK" '
                'vertAlign="TOP" linkListIDRef="0" linkListNextIDRef="0" '
                f'textWidth="0" textHeight="0" hasTextRef="0" hasNumRef="0">{body}'
                '</hp:subList>'
                f'<hp:cellAddr colAddr="{col}" rowAddr="{row}"/>'
                '<hp:cellSpan colSpan="1" rowSpan="1"/>'
                f'<hp:cellSz width="{w}" height="{h}"/>'
                f'<hp:cellMargin left="{CELL_MARGIN}" right="{CELL_MARGIN}" '
                f'top="{CELL_MARGIN}" bottom="{CELL_MARGIN}"/></hp:tc>')

    def tbl(self, rows: list[dict], *, table_border=BF_SOLID, widths=None):
        """rows: [{cells: [(paras, borderFill, char_est_pt)], height_u, header}]"""
        ncols = max(len(r["cells"]) for r in rows)
        if not widths:
            base = CONTENT_W // ncols
            widths = [base] * (ncols - 1) + [CONTENT_W - base * (ncols - 1)]
        total_h_u = sum(r["height_u"] for r in rows)
        total_pt = total_h_u / U
        # 잔여 공간에 안 들어가는 큰 고정높이 표 -> 표 문단에 쪽 나눔
        brk = total_pt >= 120 and self.y > 150 and (self.y + total_pt) > USABLE_PT
        trs = []
        for ri, r in enumerate(rows):
            cells = []
            for ci in range(ncols):
                paras, border = (r["cells"][ci] if ci < len(r["cells"])
                                 else ([], BF_SOLID))
                cells.append(self._cell(ci, ri, widths[ci], r["height_u"], paras,
                                        border=border, header=r.get("header", False)))
            trs.append(f"<hp:tr>{''.join(cells)}</hp:tr>")
        self.tbl_id += 1
        self.z += 1
        xml = (f'<hp:tbl id="{self.tbl_id}" zOrder="{self.z}" numberingType="TABLE" '
               f'pageBreak="CELL" repeatHeader="0" rowCnt="{len(rows)}" '
               f'colCnt="{ncols}" cellSpacing="0" borderFillIDRef="{table_border}" '
               'noShading="0">'
               f'<hp:sz width="{CONTENT_W}" widthRelTo="ABSOLUTE" '
               f'height="{total_h_u}" heightRelTo="ABSOLUTE" protect="0"/>'
               '<hp:pos treatAsChar="1" affectLSpacing="0" flowWithText="0" '
               'allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" '
               'horzRelTo="PARA" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" '
               'horzOffset="0"/>'
               '<hp:outMargin left="0" right="0" top="0" bottom="0"/>'
               f'<hp:inMargin left="510" right="510" top="{CELL_MARGIN}" '
               f'bottom="{CELL_MARGIN}"/>{"".join(trs)}</hp:tbl>')
        self.para([f'<hp:run charPrIDRef="{CH_BODY}">{xml}</hp:run>'],
                  est_pt=total_pt + 8, page_break=brk)

    def xml(self) -> str:
        return ("<?xml version='1.0' encoding='UTF-8'?>\n"
                '<hs:sec xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" '
                'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph">'
                + "".join(self.parts) + "</hs:sec>")


def _cell_paras(text, base=CH_BODY, para_pr=PP_CELL) -> list[str]:
    out = []
    for runs in _md_runs(text, base):
        out.append(f'<hp:p paraPrIDRef="{para_pr}" styleIDRef="0">{"".join(runs)}</hp:p>')
    return out


# ---------------------------------------------------------------------------
# 블록 방출기 (docx 렌더러와 1:1 대응)

def emit_paragraph(w, blk, theme):
    w.text_para(blk.get("text", ""))


def emit_instructions(w, blk, theme):
    w.text_para(blk.get("text", ""), base=CH_BODY)


def emit_labeled(w, blk, theme):
    lbl = chrome_ko(label_text(blk))
    runs = [_run(f"{lbl}{label_sep(lbl)} ", CH_BOLD)]
    body = _md_runs(blk.get("text", ""))
    runs += body[0]
    w.para(runs, est_pt=16.0 * max(1, len(str(blk.get('text', ''))) // 48) + 4)
    for extra in body[1:]:
        w.para(extra, est_pt=16.0)


def emit_heading(char_pr, para_pr):
    def _f(w, blk, theme):
        w.para([_run(str(blk.get("text", "")), char_pr)], para_pr, est_pt=26.0)
    return _f


def emit_phase_header(w, blk, theme):
    runs = [_run(str(blk.get("name", "")), CH_H2)]
    if blk.get("minutes") is not None:
        runs.append(_run(f"   {blk['minutes']}분", CH_GRAY))
    w.para(runs, PP_SEC, est_pt=24.0)


def emit_list(w, blk, theme, *, checklist=False):
    if blk.get("label"):
        w.para([_run(chrome_ko(label_text(blk)), CH_BOLD)], est_pt=18.0)
    ordered = bool(blk.get("ordered"))
    for i, item in enumerate(blk.get("items", []), 1):
        prefix = f"{i}. " if ordered else ("□ " if checklist else "• ")
        runs = _md_runs(item)
        first = [_run(prefix, CH_BODY)] + runs[0]
        w.para(first, PP_LIST, est_pt=15.0 * max(1, len(str(item)) // 48) + 2)
        for extra in runs[1:]:
            w.para(extra, PP_LIST, est_pt=15.0)


def emit_checklist(w, blk, theme):
    emit_list(w, blk, theme, checklist=True)


def emit_callout(w, blk, theme):
    kind = resolve_callout_kind(blk)
    icon = CALLOUT_ICON_KO.get(kind, "※")
    label = label_text(blk)
    label = re.sub(r"^(.*?)\s+—\s+Target standard$", r"성취기준 \1", label) \
        if label.endswith("Target standard") else chrome_ko(label)
    text = blk.get("text") or blk.get("body") or blk.get("content") or ""
    paras = []
    head = f"{icon} " + (label or "")
    paras += [f'<hp:p paraPrIDRef="{PP_CELL}" styleIDRef="0">'
              f'{_run(head.strip() + (" " if text else ""), CH_BOLD)}</hp:p>']
    if text:
        paras += _cell_paras(text)
    est = 24 + 16 * max(1, len(str(text)) // 46)
    w.tbl([{"cells": [(paras, BF_CALLOUT)], "height_u": int(est * U * 0.9)}],
          table_border=BF_CALLOUT)


def emit_cards(w, blk, theme):
    items = blk.get("items", [])
    if not items:
        return
    cells = []
    for c in items:
        c = c if isinstance(c, dict) else {"title": str(c), "text": ""}
        paras = _cell_paras(c.get("title", ""), CH_BOLD) + _cell_paras(c.get("text", ""))
        cells.append((paras, BF_SOLID))
    w.tbl([{"cells": cells, "height_u": 6000}])


def emit_fill_in(w, blk, theme):
    n = {"short": 12, "med": 28, "long": 60}.get(str(blk.get("size", "med")).lower(), 28)
    runs = []
    if blk.get("label"):
        runs.append(_run(chrome_ko(label_text(blk)) + ": ", CH_BOLD))
    runs.append(_run("_" * n, CH_BODY))
    w.para(runs, est_pt=18.0)


def emit_group(w, blk, theme):
    for b in blk.get("blocks", []):
        emit_block(w, b, theme)


def emit_columns(w, blk, theme):
    # HWPX 근사: 좌/우 컬럼을 순차 방출 (원본 docx는 2열 표)
    for side in ("left", "right"):
        for b in blk.get(side, []):
            emit_block(w, b, theme)


def emit_workspace(w, blk, theme, *, labeled=False):
    if labeled and blk.get("label"):
        w.para([_run(chrome_ko(label_text(blk)), CH_BOLD)], est_pt=18.0)
    h = workspace_height(blk, theme)
    if blk.get("ruled", theme.ruled_default):
        gap = float(theme.answer_gap)
        n = max(2, int(round(h / gap)))
        rows = [{"cells": [([], BF_RULE)], "height_u": int(gap * U)}
                for _ in range(n)]
        w.tbl(rows, table_border=BF_NONE)
    else:
        w.tbl([{"cells": [([], BF_LIGHT)], "height_u": int(h * U)}],
              table_border=BF_LIGHT)


def emit_page_break(w, blk, theme):
    w.force_break = True


def emit_table(w, blk, theme):
    headers = [chrome_ko(str(h).rstrip(": ")) for h in coerce_headers(blk.get("headers"))]
    rows = coerce_rows(blk.get("rows"))
    ncols = max(len(headers), max((len(r) for r in rows), default=1), 1)
    large = blk.get("display") == "large"
    out_rows = []
    if headers:
        cells = [(_cell_paras(h, CH_BOLD), BF_SHADE) for h in headers]
        cells += [([], BF_SHADE)] * (ncols - len(cells))
        out_rows.append({"cells": cells, "height_u": DEFAULT_ROW_H, "header": True})
    for r in rows:
        cells_txt = [str(r[i]) if i < len(r) else "" for i in range(ncols)]
        cells_txt = ["" if c.strip().strip("_") == "" and "_" in c else c
                     for c in cells_txt]
        full_blank = not any(c.strip() for c in cells_txt)
        blank = any(not c.strip() for c in cells_txt)
        h_u = DEFAULT_ROW_H
        if blank:
            h_u = max(h_u, int(table_row_height(blk, theme, full_blank=full_blank) * U))
        else:
            longest = max(len(c) for c in cells_txt)
            per_line = max(8, int(44 / ncols))
            h_u = max(h_u, int((16 * -(-longest // per_line) + 6) * U * 0.9))
        cells = []
        for i, v in enumerate(cells_txt):
            bold = (large and v.strip() != "") or (not headers and i == 0 and v.strip() != "")
            base = CH_H1 if large and v.strip() else (CH_BOLD if bold else CH_BODY)
            pp = PP_CENTER if large else PP_CELL
            cells.append((_cell_paras(v, base, pp) if v else [], BF_SOLID))
        out_rows.append({"cells": cells, "height_u": h_u})
    # 2열 라벨/값 표는 30/70 분할이 읽기 좋다 (보정본 어휘 표 관행)
    widths = None
    if ncols == 2 and rows and all(len(str(r[0] if r else "")) <= 12 for r in rows):
        widths = [CONTENT_W * 3 // 10, CONTENT_W - CONTENT_W * 3 // 10]
    w.tbl(out_rows, widths=widths)


def emit_fill_table(w, blk, theme):
    headers = coerce_headers(blk.get("headers"))
    try:
        cols = max(1, len(headers) or int(blk.get("cols") or 2))
    except (TypeError, ValueError):
        cols = 2
    cols = min(cols, 12)
    rows_val = blk.get("rows")
    if isinstance(rows_val, list):
        rows = []
        for r in coerce_rows(rows_val[:50]):
            cells = r[:cols]
            rows.append(cells + [""] * (cols - len(cells)))
    else:
        try:
            n = int(blk.get("blank_rows") or rows_val or 3)
        except (TypeError, ValueError):
            n = 3
        rows = [[""] * cols for _ in range(min(max(1, n), 50))]
    fwd = {"headers": headers, "rows": rows}
    for k in ("row_height_pt", "empty_row_height_pt"):
        if blk.get(k):
            fwd[k] = blk[k]
    emit_table(w, fwd, theme)


def emit_source_card(w, blk, theme):
    head = " · ".join(str(blk.get(k))
                      for k in ("title", "author", "date", "origin") if blk.get(k))
    emit_callout(w, {"kind": "student-task", "label": head,
                     "text": blk.get("excerpt") or blk.get("text") or ""}, theme)


def emit_number_line(w, blk, theme):
    # HWPX 근사: 눈금 그리기는 미지원 — 양 끝 값을 밝히고 그릴 공간을 준다.
    lo, hi = blk.get("min", 0), blk.get("max", 10)
    w.para([_run(f"수직선: {lo} ~ {hi} (직접 그려 보세요)", CH_BOLD)], est_pt=18.0)
    w.tbl([{"cells": [([], BF_LIGHT)], "height_u": int(60 * U)}],
          table_border=BF_LIGHT)


_EMITTERS = {
    "paragraph": emit_paragraph,
    "instructions": emit_instructions,
    "labeled": emit_labeled,
    "h1": emit_heading(CH_H1, PP_SEC),
    "h2": emit_heading(CH_H2, PP_SEC),
    "h3": emit_heading(CH_H3, PP_H3),
    "phase_header": emit_phase_header,
    "list": emit_list,
    "checklist": emit_checklist,
    "callout": emit_callout,
    "cards": emit_cards,
    "fill_in": emit_fill_in,
    "group": emit_group,
    "columns": emit_columns,
    "workspace": lambda w, b, t: emit_workspace(w, b, t, labeled=True),
    "page_break": emit_page_break,
    "table": emit_table,
    "fill_table": emit_fill_table,
    "source_card": emit_source_card,
    "number_line": emit_number_line,
}


def emit_block(w, blk: dict, theme: Theme):
    fn = _EMITTERS.get(btype(blk))
    if fn is None:
        # 미지원 블록: 조용히 삼키지 않는다 — 텍스트가 있으면 문단으로 강등.
        text = blk.get("text") or blk.get("label") or ""
        print(f"warning: unsupported block type '{btype(blk)}' rendered as text",
              file=sys.stderr)
        if text:
            w.text_para(text)
        return
    fn(w, blk, theme)


# ---------------------------------------------------------------------------

def _preview_text(doc: dict) -> str:
    bits = [doc.get("title", ""), meta_text(doc.get("meta"))]
    for s in doc.get("sections", []):
        bits.append(str(s.get("title", "")))
        for b in s.get("blocks", []):
            for key in ("text", "name", "label"):
                if isinstance(b.get(key), str):
                    bits.append(b[key])
    text = "\n".join(x for x in bits if x)
    text = re.sub(r"\*{1,2}([^*]+)\*{1,2}", r"\1", text)
    return text[:1500]


def render(data: dict, out_path: str) -> int:
    doc = expand_document(data, audience=data.get("audience", "teacher"))
    theme = Theme(doc.get("theme"))
    prof = answer_profile(doc)
    theme.answer_height, theme.answer_gap, theme.answer_row = prof[0], prof[1], prof[2]
    theme.ruled_default = prof[3]
    theme.student_doc = doc.get("audience") == "student"

    w = SectionWriter()
    head = build_header(doc)
    if head["eyebrow"]:
        w.para([_run(head["eyebrow"], CH_GRAY_SMALL)], est_pt=14.0)
    w.para([_run(head["title"], CH_TITLE)], PP_TITLE, est_pt=32.0)
    meta = head["meta"] or head["name_line"]
    if meta:
        meta = meta.replace("Materials:", "준비물:")
        w.para([_run(meta, CH_GRAY_SMALL)], est_pt=14.0)
    for blk in preamble_blocks(doc):
        emit_block(w, blk, theme)
    for section in doc.get("sections", []):
        heading = str(section.get("heading", "")).rstrip(": ")
        if heading:
            w.para([_run(heading, CH_H1)], PP_SEC, est_pt=26.0)
        for blk in section.get("blocks", []):
            emit_block(w, blk, theme)
    if doc.get("footer_note"):
        w.para([_run(str(doc["footer_note"]), CH_GRAY_SMALL)], est_pt=14.0)

    container = ('<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n'
                 '<ocf:container xmlns:ocf="urn:oasis:names:tc:opendocument:xmlns:'
                 'container" xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf">'
                 '<ocf:rootfiles><ocf:rootfile full-path="Contents/content.hpf" '
                 'media-type="application/hwpml-package+xml"/></ocf:rootfiles>'
                 '</ocf:container>')
    hpf = ('<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n'
           '<opf:package xmlns:opf="http://www.idpf.org/2007/opf/" '
           'xmlns:hpf="http://www.hancom.co.kr/schema/2011/hpf" '
           'xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head">'
           '<opf:metadata><opf:meta name="generator" '
           'content="science-teacher-skills render_lesson_hwpx"/></opf:metadata>'
           '<opf:manifest>'
           '<opf:item id="header" href="Contents/header.xml" media-type="application/xml"/>'
           '<opf:item id="section0" href="Contents/section0.xml" '
           'media-type="application/xml"/></opf:manifest>'
           '<opf:spine><opf:itemref idref="header" linear="no"/>'
           '<opf:itemref idref="section0" linear="yes"/></opf:spine></opf:package>')

    with zipfile.ZipFile(out_path, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "application/hwp+zip",
                   compress_type=zipfile.ZIP_STORED)
        for name, content in (("META-INF/container.xml", container),
                              ("Contents/content.hpf", hpf),
                              ("Contents/header.xml", build_header_xml()),
                              ("Contents/section0.xml", w.xml()),
                              ("Preview/PrvText.txt", _preview_text(doc))):
            z.writestr(name, content, compress_type=zipfile.ZIP_DEFLATED)
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("json_path")
    ap.add_argument("--outdir", default=".")
    ap.add_argument("--only", nargs="*", default=None,
                    help="document id(s) to render (default: all)")
    args = ap.parse_args()

    source = json.loads(Path(args.json_path).read_text(encoding="utf-8"))
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    docs = source.get("documents")
    if docs is None:
        docs = [dict(source, id=source.get("id", Path(args.json_path).stem))]
        source = {"shared": source.get("shared", {}), "theme": source.get("theme")}
    count = 0
    for entry in docs:
        if args.only and entry.get("id") not in args.only:
            continue
        merged = build_doc(source, entry)
        out = outdir / f"{entry.get('id', 'document')}.hwpx"
        render(merged, str(out))
        print(f"wrote {out}")
        count += 1
    if count == 0:
        print("error: no documents matched", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
