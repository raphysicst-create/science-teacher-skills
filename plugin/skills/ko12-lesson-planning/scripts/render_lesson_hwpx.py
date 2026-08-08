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
구조 검증 + 한컴 실열림 + PDF 대조를 통과한 보정본(pilot/*/out/*.hwpx)의 값에서
출발해, hwpx-quality-loop(tests/check_hwpx_quality.py 결함 ID 기준)로 보정했다:
본문 폭 일치(F7), 목록 내어쓰기(F4), 폰트 참조 무결성(F1·F3), 콜아웃 kind별
테두리색(F5), 표 머리행 반복(F6), 쪽번호(F8), version/settings(S5).
교사 대면 크롬(성취기준 라벨, 분 표기)은 lesson_common이 한국어로 방출한다 —
HWPX·HTML 둘 다 교사가 보는 산출물이기 때문이다.

Usage:
    python render_lesson_hwpx.py lesson.json --outdir out
    python render_lesson_hwpx.py lesson.json --only lesson_plan --outdir out
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

sys.path.insert(0, str(Path(__file__).resolve().parent))

from lesson_common import (  # noqa: E402
    Theme, answer_profile, btype, build_header, coerce_headers, coerce_marks,
    coerce_rows, expand_document, label_sep, label_text, md_tokens, meta_text,
    preamble_blocks, resolve_callout_kind, table_row_height, workspace_height,
)
from render_documents import build_doc  # noqa: E402

# ---------------------------------------------------------------------------
# 단위: hp:cellSz·hp:sz·페이지 치수는 1/100 pt. (보정본 실측: 설계표 10800=108pt)
U = 100                      # pt -> OWPML 단위
# 본문 폭 = 용지 59528 - 여백(좌 5670 + 우 4252) = 49606. 보정본의 44000은 본문
# 문단(496pt)보다 11% 좁아 표·콜아웃 오른쪽에 여백이 남았다(결함 F7) — 일치시킨다.
CONTENT_W = 49600
# 실측(한글 PDF, 5회차): 본문 첫 줄 y=64.4pt, 마지막 내용 줄 y≈794pt → 730pt.
USABLE_PT = 730.0            # A4 인쇄 가능 높이 (쪽 나눔 판단용, PDF 실측)
CELL_MARGIN = 141
DEFAULT_ROW_H = 1500         # 텍스트 행 기본 높이 15pt (내용에 따라 늘어남)
CHARS_FULL = CONTENT_W // (10 * U)   # 본문 폭 기준 줄당 글자수 근사 (10pt 한글)
# est(쪽 나눔 판단)용 줄당 글자수: 띄어쓰기·어절 단위 줄바꿈 때문에 실제 줄은
# 이론값(49자)보다 일찍 꺾인다 — PDF 실측에서 est가 쪽당 약 -100pt 뒤처진 원인.
CHARS_EST = CONTENT_W // (12 * U)

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
PP_H1 = 10   # h1 전용: 위 구분선(HTML .h1 border-top 대응 — 결함 V8)
PP_KEEP = 11  # 본문 + 다음 문단과 붙임 — 지시-답란 동반 배치(결함 V4)
# 스타일 id 대응 (한글 [서식-스타일]에서 제목·목록을 일괄 편집할 수 있게 — 결함 F10)
ST_BODY, ST_TITLE, ST_H1, ST_H2, ST_H3, ST_LIST, ST_CAPTION = 0, 1, 2, 3, 4, 5, 6
# borderFill id 대응
BF_NONE, BF_SOLID, BF_SHADE, BF_CALLOUT, BF_RULE, BF_LIGHT = 1, 2, 3, 4, 5, 6
# 콜아웃 kind별 테두리색(HTML theme.css와 동일) + 카드 배경 — 결함 F5 해소
BF_CO_SPECIAL, BF_CO_TASK, BF_CO_NOTE, BF_CARD = 7, 8, 9, 10
BF_H1_RULE = 11   # h1 문단 위 구분선 (HTML .h1 border-top과 동일)
CALLOUT_BF = {"special": BF_CO_SPECIAL, "student-task": BF_CO_TASK,
              "teacher-note": BF_CO_NOTE, "student-note": BF_CO_NOTE}


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
    # hanja 이하 5종 fontface는 id 0 하나만 정의된다 — id 1 참조는 dangling(결함 F1).
    return (f'<hh:charPr {attrs}>'
            f'<hh:fontRef hangul="{f}" latin="{f}" hanja="0" japanese="0" '
            f'other="0" symbol="0" user="0"/>'
            '<hh:ratio hangul="100" latin="100" hanja="100" japanese="100" '
            'other="100" symbol="100" user="100"/>'
            '<hh:spacing hangul="0" latin="0" hanja="0" japanese="0" other="0" '
            'symbol="0" user="0"/>'
            '<hh:relSz hangul="100" latin="100" hanja="100" japanese="100" '
            'other="100" symbol="100" user="100"/>'
            '<hh:offset hangul="0" latin="0" hanja="0" japanese="0" other="0" '
            f'symbol="0" user="0"/>{tail}</hh:charPr>')


def _border_fill(bid: int, *, sides="NONE", width="0.1 mm", color="#000000",
                 bottom_only=False, top_only=False,
                 fill: str | None = None) -> str:
    def edge(side_type, w, c):
        return f'type="{side_type}" width="{w}" color="{c}"'
    if bottom_only:
        l = r = t = edge("NONE", "0.1 mm", "#000000")
        b = edge("SOLID", width, color)
    elif top_only:
        l = r = b = edge("NONE", "0.1 mm", "#000000")
        t = edge("SOLID", width, color)
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
             left=0, prev=0, nxt=0, spacing=160, border_bf=1,
             border_top_off=0, keep=False) -> str:
    # heading은 항상 NONE — OUTLINE + idRef=0은 존재하지 않는 numbering을 가리켜
    # (dangling) 한글이 개요 번호를 붙이면 "1. 1. 현상 던지기" 이중 번호가 된다.
    del heading, level
    head = '<hh:heading type="NONE" idRef="0" level="0"/>'
    # keep: 다음 문단과 붙임 — 제목·지시문이 쪽 맨 아래 고립되지 않게 한글
    # 조판기가 직접 지킨다(결함 V4). y 추정 기반 강제 쪽나눔은 추정 오차가
    # 그대로 빈 쪽으로 새어 나와 쓰지 않는다.
    return (f'<hh:paraPr id="{pid}" tabPrIDRef="0" condense="0" fontLineHeight="0" '
            'snapToGrid="0" suppressLineNumbers="0" checked="0" textDir="AUTO">'
            f'<hh:align horizontal="{align}" vertical="BASELINE"/>{head}'
            '<hh:breakSetting breakLatinWord="KEEP_WORD" breakNonLatinWord="BREAK_WORD" '
            f'widowOrphan="0" keepWithNext="{1 if keep else 0}" keepLines="0" '
            'pageBreakBefore="0" lineWrap="BREAK"/>'
            '<hh:autoSpacing eAsianEng="0" eAsianNum="0"/>'
            f'<hh:margin><hc:intent value="{indent}" unit="HWPUNIT"/>'
            f'<hc:left value="{left}" unit="HWPUNIT"/><hc:right value="0" unit="HWPUNIT"/>'
            f'<hc:prev value="{prev}" unit="HWPUNIT"/>'
            f'<hc:next value="{nxt}" unit="HWPUNIT"/></hh:margin>'
            f'<hh:lineSpacing type="PERCENT" value="{spacing}"/>'
            f'<hh:border borderFillIDRef="{border_bf}" offsetLeft="0" offsetRight="0" '
            f'offsetTop="{border_top_off}" offsetBottom="0" connect="0" '
            'ignoreMargin="0"/></hh:paraPr>')


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
    # 라틴 id1은 본문이 참조한다 — Consolas(고정폭)였던 것을 함초롬돋움으로 교체(결함 F3):
    # CO2·25℃·mL 같은 영문·숫자가 코딩 글꼴로 인쇄되던 문제.
    faces_lat = [("Times New Roman", "FCAT_OLDSTYLE", 5), ("함초롬돋움", "FCAT_GOTHIC", 6),
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
        + _border_fill(BF_LIGHT, sides="SOLID", width="0.12 mm", color="#C9CFD4")
        # 콜아웃 kind별 테두리색 — theme.css의 .co.special/.co.task/.co.tnote와 동일
        + _border_fill(BF_CO_SPECIAL, sides="SOLID", width="0.25 mm", color="#5BB088",
                       fill="#F6F8F9")
        + _border_fill(BF_CO_TASK, sides="SOLID", width="0.25 mm", color="#9FB8D8",
                       fill="#F6F8F9")
        + _border_fill(BF_CO_NOTE, sides="SOLID", width="0.25 mm", color="#E8C98A",
                       fill="#F6F8F9")
        + _border_fill(BF_CARD, sides="SOLID", width="0.12 mm", color="#C9CFD4",
                       fill="#FAFBFB")
        # h1 위 구분선 — HTML .h1의 border-top: 1pt solid var(--rule) 대응(V8)
        + _border_fill(BF_H1_RULE, top_only=True, width="0.3 mm", color="#D0D4D8"))
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
        + _para_pr(1, prev=800, nxt=200, spacing=180, keep=True)
        + _para_pr(2, prev=600, nxt=150, spacing=170, keep=True)
        + _para_pr(3, prev=400, nxt=100, keep=True)
        + _para_pr(4, prev=300, nxt=100)
        # 목록: 내어쓰기 — 글머리("• ")가 왼쪽 여백에 걸리고 둘째 줄부터 본문이
        # 글머리 뒤에 정렬된다(결함 F4: 양수 intent는 첫 줄만 밀어 역효과였다).
        + _para_pr(5, indent=-1500, left=1500, spacing=140, nxt=200)
        + _para_pr(6, indent=600, spacing=150)
        + _para_pr(7, indent=600)
        + _para_pr(8, align="CENTER", spacing=140)
        + _para_pr(9, align="LEFT", spacing=140, nxt=200)   # 표 셀 본문 (촘촘)
        # h1 전용: 위 구분선 + 넉넉한 앞 간격 — HTML .h1(border-top, padding-top)
        + _para_pr(PP_H1, prev=800, nxt=150, spacing=170, border_bf=BF_H1_RULE,
                   border_top_off=4, keep=True)
        # 본문 + 다음 문단과 붙임 — group/암묵 그룹의 마지막 전 블록들이 쓴다
        + _para_pr(PP_KEEP, align="LEFT", spacing=150, nxt=700, keep=True))
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n'
        '<hh:head xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" '
        'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph" '
        'xmlns:hc="http://www.hancom.co.kr/hwpml/2011/core" version="1.4" secCnt="1">'
        '<hh:beginNum page="1" footnote="1" endnote="1" pic="1" tbl="1" equation="1"/>'
        '<hh:refList>'
        f'<hh:fontfaces itemCnt="7">{fontfaces}</hh:fontfaces>'
        f'<hh:borderFills itemCnt="11">{border_fills}</hh:borderFills>'
        f'<hh:charProperties itemCnt="13">{char_prs}</hh:charProperties>'
        '<hh:tabProperties itemCnt="0"/>'
        '<hh:numberings itemCnt="1"><hh:numbering id="1" start="0">'
        + "".join(f'<hh:paraHead start="1" level="{lv}" align="LEFT" useInstWidth="1" '
                  'autoIndent="1" widthAdjust="0" textOffsetType="PERCENT" '
                  'textOffset="50" numFormat="DIGIT" charPrIDRef="4294967295" '
                  'checkable="0"/>' for lv in range(1, 8))
        + '</hh:numbering></hh:numberings>'
        '<hh:bullets itemCnt="0"/>'
        f'<hh:paraProperties itemCnt="12">{para_prs}</hh:paraProperties>'
        # 스타일 정의(결함 F10): 제목·목록·캡션 문단이 이름 있는 스타일을 참조해
        # 교사가 한글 [서식-스타일]에서 문서 전체를 일괄 편집할 수 있다.
        '<hh:styles itemCnt="7">'
        '<hh:style id="0" type="PARA" name="바탕글" engName="Normal" '
        'paraPrIDRef="0" charPrIDRef="0" nextStyleIDRef="0" langIDRef="1042" lockForm="0"/>'
        f'<hh:style id="{ST_TITLE}" type="PARA" name="문서 제목" engName="Title" '
        f'paraPrIDRef="1" charPrIDRef="{CH_TITLE}" nextStyleIDRef="0" '
        'langIDRef="1042" lockForm="0"/>'
        f'<hh:style id="{ST_H1}" type="PARA" name="제목 1" engName="Heading 1" '
        f'paraPrIDRef="{PP_H1}" charPrIDRef="{CH_H1}" nextStyleIDRef="0" '
        'langIDRef="1042" lockForm="0"/>'
        f'<hh:style id="{ST_H2}" type="PARA" name="제목 2" engName="Heading 2" '
        f'paraPrIDRef="2" charPrIDRef="{CH_H2}" nextStyleIDRef="0" '
        'langIDRef="1042" lockForm="0"/>'
        f'<hh:style id="{ST_H3}" type="PARA" name="제목 3" engName="Heading 3" '
        f'paraPrIDRef="3" charPrIDRef="{CH_H3}" nextStyleIDRef="0" '
        'langIDRef="1042" lockForm="0"/>'
        f'<hh:style id="{ST_LIST}" type="PARA" name="목록" engName="List" '
        f'paraPrIDRef="{PP_LIST}" charPrIDRef="0" nextStyleIDRef="{ST_LIST}" '
        'langIDRef="1042" lockForm="0"/>'
        f'<hh:style id="{ST_CAPTION}" type="PARA" name="부가 정보" engName="Caption" '
        f'paraPrIDRef="0" charPrIDRef="{CH_GRAY_SMALL}" nextStyleIDRef="0" '
        'langIDRef="1042" lockForm="0"/>'
        '</hh:styles>'
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
    'sameSz="1" sameGap="0"/></hp:ctrl>'
    # 쪽번호 "- 1 -" 하단 중앙 — 여러 장짜리 학습지의 순서 보장(결함 F8)
    '<hp:ctrl><hp:pageNum pos="BOTTOM_CENTER" formatType="DIGIT" sideChar="-"/>'
    '</hp:ctrl>')


def _t(text: str) -> str:
    return f"<hp:t>{escape(str(text))}</hp:t>"


def _plain(text) -> str:
    """마크다운 마커를 벗긴 평문. _run 경로(제목·라벨·크롬)는 서식 run을 나누지
    않으므로, **별표**가 그대로 인쇄되지 않게 여기서 정리한다(결함 C2)."""
    s = str(text)
    if "*" not in s and "|" not in s:
        return s
    return "".join(t for t, a in md_tokens(s) if t and not a.get("break")) or s


def _run(text: str, char_pr: int = CH_BODY) -> str:
    return f'<hp:run charPrIDRef="{char_pr}">{_t(_plain(text))}</hp:run>'


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
        self.total = 0.0           # 누적 높이 (쪽 나눔 리셋 없이) — 그룹 높이 측정용
        self.tbl_id = 1000
        self.z = 0
        self.force_break = False   # page_break 블록이 다음 문단에 걸어 둠
        self.pin = False           # True면 본문 문단을 '다음 문단과 붙임'으로 방출

    # -- 문단 --------------------------------------------------------------
    def para(self, runs: list[str], para_pr: int = PP_BODY, *, est_pt: float = 20.0,
             page_break: bool = False, style: int = ST_BODY):
        brk = page_break or self.force_break
        self.force_break = False
        if self.pin and para_pr == PP_BODY:
            para_pr = PP_KEEP
        attrs = f'paraPrIDRef="{para_pr}" styleIDRef="{style}"'
        if brk and not self.first:
            attrs += ' pageBreak="1"'
            self.y = 0.0
        body = "".join(runs)
        if self.first:
            body = f'<hp:run charPrIDRef="{CH_TITLE}">{SEC_PR}</hp:run>' + body
            self.first = False
        self.parts.append(f"<hp:p {attrs}>{body}</hp:p>")
        self.y += est_pt
        self.total += est_pt
        if self.y > USABLE_PT:
            self.y = est_pt

    def text_para(self, text, base: int = CH_BODY, para_pr: int = PP_BODY):
        for runs in _md_runs(text, base):
            plain = re.sub(r"<[^>]+>", "", "".join(runs))
            lines = max(1, -(-len(plain) // CHARS_EST))
            # 실측(PDF): 본문 줄 15pt(150%) + 문단 뒤 7pt
            self.para(runs, para_pr, est_pt=15.0 * lines + 7)

    # -- 표 ----------------------------------------------------------------
    def _cell(self, col: int, row: int, w: int, h: int, paras: list[str],
              *, border=BF_SOLID, header=False) -> str:
        body = "".join(paras) or f'<hp:p paraPrIDRef="0" styleIDRef="0">' \
                                 f'<hp:run charPrIDRef="0"><hp:t/></hp:run></hp:p>'
        return (f'<hp:tc name="" header="{1 if header else 0}" hasMargin="1" '
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

    def tbl(self, rows: list[dict], *, table_border=BF_SOLID, widths=None,
            splittable=False):
        """rows: [{cells: [(paras, borderFill, char_est_pt)], height_u, header}]

        splittable=True(데이터 표·괘선 쓰기 공간): 글자처럼 취급을 풀고
        (treatAsChar=0, 위아래 어울림) 셀 단위 쪽나눔을 허용해, 쪽 경계에서
        한글이 행을 직접 나눈다 — 표가 통째로 밀리며 쪽 하단에 대공백을
        남기던 결함(V5)의 근본 해소. 머리행 반복(repeatHeader)도 이때 실제로
        동작한다(V9). y 추정 기반 명시적 쪽나눔은 추정 오차가 그대로 빈 쪽이
        되어 폐기했다(5회차 실측).

        splittable=False(콜아웃·카드·2단·수직선): 작은 상자 — 글자처럼 취급을
        유지해 통째로 움직인다."""
        # 4행 미만은 분할 금지: 2줄 답란이 1+1로 갈라지면 마지막 줄이 다음 쪽에
        # 고아로 남는다(5회차 실채점에서 발견 — 다 모둠 되돌아보기). 작은 표는
        # 통째로 움직여야 지시문(keepWithNext)과 함께 넘어간다.
        if splittable and len(rows) < 4:
            splittable = False
        ncols = max(len(r["cells"]) for r in rows)
        if not widths:
            base = CONTENT_W // ncols
            widths = [base] * (ncols - 1) + [CONTENT_W - base * (ncols - 1)]
        total_h_u = sum(r["height_u"] for r in rows)
        total_pt = total_h_u / U
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
        # 머리행이 있는 표는 쪽을 넘어갈 때 머리행을 반복한다(결함 F6)
        repeat = "1" if any(r.get("header") for r in rows) else "0"
        if splittable:
            page_break, treat, flow = "CELL", "0", "1"
            extra = ' textWrap="TOP_AND_BOTTOM"'
            # 어울림 표는 뒤 문단이 표 밑변에 바로 붙는다 — 본문 문단 뒤 간격(7pt)을
            # outMargin으로 재현
            out_margin = '<hp:outMargin left="0" right="0" top="200" bottom="700"/>'
        else:
            page_break, treat, flow, extra = "NONE", "1", "0", ""
            out_margin = '<hp:outMargin left="0" right="0" top="0" bottom="0"/>'
        xml = (f'<hp:tbl id="{self.tbl_id}" zOrder="{self.z}" numberingType="TABLE" '
               f'pageBreak="{page_break}" repeatHeader="{repeat}" rowCnt="{len(rows)}" '
               f'colCnt="{ncols}" cellSpacing="0" borderFillIDRef="{table_border}" '
               f'noShading="0"{extra}>'
               f'<hp:sz width="{CONTENT_W}" widthRelTo="ABSOLUTE" '
               f'height="{total_h_u}" heightRelTo="ABSOLUTE" protect="0"/>'
               f'<hp:pos treatAsChar="{treat}" affectLSpacing="0" flowWithText="{flow}" '
               'allowOverlap="0" holdAnchorAndSO="0" vertRelTo="PARA" '
               'horzRelTo="PARA" vertAlign="TOP" horzAlign="LEFT" vertOffset="0" '
               'horzOffset="0"/>'
               f'{out_margin}'
               f'<hp:inMargin left="510" right="510" top="{CELL_MARGIN}" '
               f'bottom="{CELL_MARGIN}"/>{"".join(trs)}</hp:tbl>')
        self.para([f'<hp:run charPrIDRef="{CH_BODY}">{xml}</hp:run>'],
                  est_pt=total_pt + 8)

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
    w.para(runs, est_pt=15.0 * max(1, -(-len(str(blk.get('text', ''))) // CHARS_EST)) + 7)
    for extra in body[1:]:
        w.para(extra, est_pt=16.0)


def emit_heading(char_pr, para_pr, style, est_pt=28.0):
    def _f(w, blk, theme):
        # 제목의 쪽 하단 고립 방지는 paraPr keepWithNext가 조판 시점에 지킨다.
        w.para([_run(str(blk.get("text", "")), char_pr)], para_pr, est_pt=est_pt,
               style=style)
    return _f


def emit_phase_header(w, blk, theme):
    runs = [_run(str(blk.get("name", "")), CH_H2)]
    if blk.get("minutes") is not None:
        runs.append(_run(f"   {blk['minutes']}분", CH_GRAY))
    w.para(runs, PP_SEC, est_pt=30.0, style=ST_H2)


def emit_list(w, blk, theme, *, checklist=False):
    if blk.get("label"):
        w.para([_run(chrome_ko(label_text(blk)), CH_BOLD)], est_pt=18.0)
    ordered = bool(blk.get("ordered"))
    for i, item in enumerate(blk.get("items", []), 1):
        prefix = f"{i}. " if ordered else ("□ " if checklist else "• ")
        runs = _md_runs(item)
        first = [_run(prefix, CH_BODY)] + runs[0]
        w.para(first, PP_LIST, est_pt=15.0 * max(1, -(-len(str(item)) // CHARS_EST)) + 2,
               style=ST_LIST)
        for extra in runs[1:]:
            w.para(extra, PP_LIST, est_pt=15.0, style=ST_LIST)


def emit_checklist(w, blk, theme):
    emit_list(w, blk, theme, checklist=True)


def emit_callout(w, blk, theme):
    kind = resolve_callout_kind(blk)
    icon = CALLOUT_ICON_KO.get(kind, "※")
    label = label_text(blk)
    if label.endswith("Target standard"):
        # 구식 라벨("[code] — Target standard" 또는 라벨 단독) 방어 — 지금은
        # lesson_common이 한국어("성취기준 [code]")로 직접 방출한다.
        label = ("성취기준 " + label[: -len("Target standard")].strip(" —")).strip()
    else:
        label = chrome_ko(label)
    text = blk.get("text") or blk.get("body") or blk.get("content") or ""
    bf = CALLOUT_BF.get(kind, BF_CALLOUT)
    paras = []
    head = f"{icon} " + (label or "")
    paras += [f'<hp:p paraPrIDRef="{PP_CELL}" styleIDRef="0">'
              f'{_run(head.strip() + (" " if text else ""), CH_BOLD)}</hp:p>']
    if text:
        paras += _cell_paras(text)
    est = 24 + 16 * max(1, -(-len(str(text)) // (CHARS_EST - 2)))
    w.tbl([{"cells": [(paras, bf)], "height_u": int(est * U * 0.9)}],
          table_border=bf)


def emit_cards(w, blk, theme):
    items = blk.get("items", [])
    if not items:
        return
    cells, est_max = [], 40
    per_line = max(6, CHARS_FULL // max(1, len(items)) - 2)
    for c in items:
        c = c if isinstance(c, dict) else {"title": str(c), "text": ""}
        text = str(c.get("text", ""))
        paras = _cell_paras(c.get("title", ""), CH_BOLD) + (_cell_paras(text) if text else [])
        est_max = max(est_max, 20 + 14 * -(-len(text) // per_line))
        cells.append((paras, BF_CARD))
    w.tbl([{"cells": cells, "height_u": int(est_max * U * 0.9)}], table_border=BF_CARD)


def emit_fill_in(w, blk, theme):
    n = {"short": 12, "med": 28, "long": 60}.get(str(blk.get("size", "med")).lower(), 28)
    runs = []
    if blk.get("label"):
        runs.append(_run(chrome_ko(label_text(blk)) + ": ", CH_BOLD))
    runs.append(_run("_" * n, CH_BODY))
    w.para(runs, est_pt=18.0)


def emit_group(w, blk, theme):
    blocks = blk.get("blocks", [])
    if not blocks:
        return
    # 문제와 답란이 쪽 경계로 갈라지지 않게(HTML의 page-break-inside:avoid 대응):
    # 마지막 블록을 뺀 전 블록의 본문 문단을 '다음 문단과 붙임'(PP_KEEP)으로
    # 방출한다 — y 추정 프로브와 달리 한글 조판기가 실제 위치에서 지킨다(V4).
    prev_pin = w.pin
    w.pin = True
    for b in blocks[:-1]:
        emit_block(w, b, theme)
    w.pin = prev_pin
    emit_block(w, blocks[-1], theme)


def _inline_paras(blocks: list) -> list[str] | None:
    """표 셀 안에 넣을 수 있는 단순 텍스트 블록들을 셀 문단으로 바꾼다.
    복잡한 블록(표·콜아웃·workspace)이 섞이면 None — 호출자가 순차 방출로 폴백."""
    paras: list[str] = []
    for b in blocks:
        t = btype(b)
        if t in ("paragraph", "instructions"):
            paras += _cell_paras(b.get("text", ""))
        elif t == "labeled":
            lbl = chrome_ko(label_text(b))
            paras += _cell_paras(f"**{lbl}{label_sep(lbl)}** {b.get('text', '')}")
        elif t == "h3":
            paras += _cell_paras(str(b.get("text", "")), CH_H3)
        elif t in ("list", "checklist"):
            ordered = bool(b.get("ordered"))
            if b.get("label"):
                paras += _cell_paras(f"**{chrome_ko(label_text(b))}**")
            for i, item in enumerate(b.get("items", []), 1):
                prefix = f"{i}. " if ordered else ("□ " if t == "checklist" else "• ")
                paras += _cell_paras(prefix + str(item))
        elif t == "fill_in":
            n = {"short": 12, "med": 24, "long": 36}.get(
                str(b.get("size", "med")).lower(), 24)
            lbl = (chrome_ko(label_text(b)) + ": ") if b.get("label") else ""
            paras += _cell_paras(lbl + "_" * n)
        else:
            return None
    return paras


def emit_columns(w, blk, theme):
    # 2열: 단순 텍스트 블록이면 테두리 없는 1×2 표로 진짜 나란히 놓는다.
    # 복잡한 블록이 섞이면 좌→우 순차 방출로 폴백(이전 근사).
    left, right = blk.get("left", []), blk.get("right", [])
    lp, rp = _inline_paras(left), _inline_paras(right)
    if lp is None or rp is None:
        for side in (left, right):
            for b in side:
                emit_block(w, b, theme)
        return

    def _est(blocks) -> float:
        half = max(6, CHARS_FULL // 2 - 3)
        total = 0.0
        for b in blocks:
            texts = [str(b.get("text", ""))]
            texts += [str(i) for i in (b.get("items") or [])]
            for s in texts:
                if s:
                    total += 14.0 * max(1, -(-len(s) // half))
        return total + 8
    h = max(_est(left), _est(right), 30.0)
    w.tbl([{"cells": [(lp, BF_NONE), (rp, BF_NONE)], "height_u": int(h * U)}],
          table_border=BF_NONE)


def emit_workspace(w, blk, theme, *, labeled=False):
    if labeled and blk.get("label"):
        w.para([_run(chrome_ko(label_text(blk)), CH_BOLD)], est_pt=18.0)
    h = workspace_height(blk, theme)
    if blk.get("ruled", theme.ruled_default):
        gap = float(theme.answer_gap)
        n = max(2, int(round(h / gap)))
        rows = [{"cells": [([], BF_RULE)], "height_u": int(gap * U)}
                for _ in range(n)]
        w.tbl(rows, table_border=BF_NONE, splittable=True)
    else:
        w.tbl([{"cells": [([], BF_LIGHT)], "height_u": int(h * U)}],
              table_border=BF_LIGHT)


def emit_page_break(w, blk, theme):
    w.force_break = True


def _col_widths(headers: list, rows: list, ncols: int) -> list[int]:
    """내용 기반 열폭: 열별 최장 텍스트의 제곱근 가중 — 라벨 열은 좁게, 서술 열은
    넓게. sqrt는 극단을 눌러 어휘 표(짧은 용어/긴 뜻)가 대략 30/70으로 떨어진다.

    빈 답란 열(데이터 행이 전부 빈 열)은 학생이 쓰는 자리다 — 내용 길이 0으로
    재면 라벨 열보다 좁아져 관계가 뒤집힌다(결함 V2/F12). 라벨+답란 혼합 표는
    답란을 최대 서술 폭으로 치고, 전부 빈 기입표는 머리글 길이를 선형 가중해
    짧은 식별 열(모둠 등)이 좁게 떨어지게 한다."""
    lens, blanks = [], []
    for i in range(ncols):
        vals = [str(r[i]) if i < len(r) else "" for r in rows]
        blanks.append(bool(rows) and all(not v.strip().strip("_ ") for v in vals))
        cand = [len(str(headers[i]))] if i < len(headers) else [0]
        cand += [len(v) for v in vals]
        lens.append(max(cand + [0]))
    if any(blanks) and not all(blanks):
        weights = [math.sqrt(60) if b else math.sqrt(min(max(ln, 6), 60))
                   for ln, b in zip(lens, blanks)]
    elif all(blanks) and rows:
        weights = [float(max(len(str(headers[i])) if i < len(headers) else 0, 2))
                   for i in range(ncols)]
    else:
        weights = [math.sqrt(min(max(ln, 6), 60)) for ln in lens]
    total = sum(weights) or 1.0
    widths = [int(CONTENT_W * x / total) for x in weights]
    widths[-1] = CONTENT_W - sum(widths[:-1])
    return widths


def emit_table(w, blk, theme):
    headers = [chrome_ko(str(h).rstrip(": ")) for h in coerce_headers(blk.get("headers"))]
    rows = coerce_rows(blk.get("rows"))
    ncols = max(len(headers), max((len(r) for r in rows), default=1), 1)
    large = blk.get("display") == "large"
    widths = _col_widths(headers, rows, ncols)
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
            # 행 높이: 각 셀을 자기 열폭 기준으로 접었을 때 가장 긴 셀
            lines = 1
            for i, c in enumerate(cells_txt):
                per_line = max(6, widths[i] // (10 * U))
                lines = max(lines, -(-len(c) // per_line))
            h_u = max(h_u, int((16 * lines + 6) * U * 0.9))
        cells = []
        for i, v in enumerate(cells_txt):
            bold = (large and v.strip() != "") or (not headers and i == 0 and v.strip() != "")
            base = CH_H1 if large and v.strip() else (CH_BOLD if bold else CH_BODY)
            pp = PP_CENTER if large else PP_CELL
            cells.append((_cell_paras(v, base, pp) if v else [], BF_SOLID))
        out_rows.append({"cells": cells, "height_u": h_u})
    w.tbl(out_rows, widths=widths, splittable=True)


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
    """수직선을 1행 눈금표로 근사한다: 각 눈금 값이 셀 하나(위 괘선이 선 역할),
    marks는 그 위 행에 ▼와 라벨로 얹는다. HTML의 그린 수직선과 같은 정보를 담는다."""
    lo, hi = blk.get("min", 0), blk.get("max", 10)
    try:
        ticks = None if blk.get("ticks") is None else int(blk.get("ticks"))
    except (TypeError, ValueError):
        ticks = None
    is_blank = ticks == 0
    n = 10 if ticks in (None, 0) else min(max(1, ticks), 20)
    marks = coerce_marks(blk.get("marks"))
    try:
        lo_f, hi_f = float(lo), float(hi)
        span = hi_f - lo_f or 1.0
    except (TypeError, ValueError):
        lo_f, hi_f, span = 0.0, float(n), float(n)
    # 눈금 값 목록 (빈 수직선이면 양 끝만 표기)
    vals = []
    for i in range(n + 1):
        v = lo_f + span * i / n
        vals.append(v)
    mark_cells, tick_cells = [], []
    for i, v in enumerate(vals):
        near = [lab for mv, lab in marks if abs(mv - v) <= abs(span) / (2 * n)]
        mark_cells.append((_cell_paras("▼ " + (near[0] or "") if near else "",
                                       CH_BOLD, PP_CENTER) if near else [], BF_NONE))
        if is_blank:
            txt = str(lo) if i == 0 else (str(hi) if i == n else "")
        else:
            txt = f"{v:g}"
        tick_cells.append((_cell_paras(txt, CH_BODY, PP_CENTER) if txt else [],
                           BF_RULE))
    rows = []
    if any(c for c, _ in mark_cells):
        rows.append({"cells": mark_cells, "height_u": int(16 * U)})
    rows.append({"cells": tick_cells, "height_u": int(18 * U)})
    w.tbl(rows, table_border=BF_NONE)


_EMITTERS = {
    "paragraph": emit_paragraph,
    "instructions": emit_instructions,
    "labeled": emit_labeled,
    "h1": emit_heading(CH_H1, PP_H1, ST_H1, est_pt=38.0),
    "h2": emit_heading(CH_H2, PP_SEC, ST_H2, est_pt=28.0),
    "h3": emit_heading(CH_H3, PP_H3, ST_H3, est_pt=22.0),
    "phase_header": emit_phase_header,
    "list": emit_list,
    "checklist": emit_checklist,
    "callout": emit_callout,
    "cards": emit_cards,
    "fill_in": emit_fill_in,
    "group": emit_group,
    "columns": emit_columns,
    "workspace": lambda w, b, t: emit_workspace(w, b, t, labeled=True),
    "labeled_box": lambda w, b, t: emit_workspace(w, b, t, labeled=True),
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


# 학생이 답을 쓰는 블록 — 지시 블록과 쪽이 갈리면 안 되는 대상(결함 V4)
_ANSWER_TYPES = {"workspace", "labeled_box", "fill_table", "number_line",
                 "fill_in", "table"}


def _first_answer_tall(blocks, theme) -> bool:
    """단위의 첫 답란이 '높은 행'(그리기 칸·빈 기입 행 40pt+·무괘선 상자)인가.

    높은 행은 쪽 끝 잔여 공간에 머리행+첫 행이 안 들어가 지시문과 갈라진다 —
    이때만 단위 앞 쪽나눔 가드를 쓴다. 보통 표(내용 행 16pt)와 괘선 답란은
    행 단위 쪽나눔이 자연스럽게 채우므로 가드가 오히려 공백을 만든다."""
    for b in blocks:
        t = btype(b)
        if t not in _ANSWER_TYPES:
            continue
        if t == "workspace":
            return not b.get("ruled", theme.ruled_default)
        if t == "labeled_box":
            return True
        if t in ("table", "fill_table"):
            rows = coerce_rows(b.get("rows")) if t == "table" else []
            blankish = t == "fill_table" or any(
                any(not str(c).strip().strip("_ ") for c in r) for r in rows)
            if not blankish:
                return False
            try:
                return table_row_height(b, theme, full_blank=True) > 40
            except Exception:
                return True
        return False
    return False


def emit_section_blocks(w, blocks: list, theme: Theme):
    """절 안 블록을 순서대로 방출하되, 지시 블록(학생 과제 콜아웃·h3)과 바로
    뒤따르는 답란 블록을 암묵 그룹으로 묶어 쪽 경계가 지시문과 답란 사이를
    가르지 않게 한다(결함 V4 — HTML page-break-inside:avoid 대응). JSON이 이미
    group으로 묶은 경우는 emit_group이 그대로 처리한다."""
    i = 0
    n = len(blocks)
    while i < n:
        blk = blocks[i]
        t = btype(blk)
        is_prompt = (t == "h3"
                     or (t == "callout"
                         and resolve_callout_kind(blk) == "student-task"))
        if is_prompt:
            j = i + 1
            unit = [blk]
            # h3 지시 제목 뒤 짧은 지시문 하나까지 같은 단위로 본다
            if t == "h3" and j < n and btype(blocks[j]) in (
                    "paragraph", "instructions", "labeled", "callout"):
                unit.append(blocks[j])
                j += 1
            k = j
            while k < n and btype(blocks[k]) in _ANSWER_TYPES:
                unit.append(blocks[k])
                k += 1
            if k > j:  # 답란이 실제로 붙어 있을 때만 그룹으로 묶는다
                # 첫 답란이 높은 행이면 keepWithNext로도 지시문과 표 시작이
                # 갈릴 수 있다(어울림 표의 실제 위치를 못 봄) — 쪽 끝 부근에서
                # 단위 전체를 다음 쪽으로. 소비량 ≤200pt+est 오차로 판정
                # 기준(⅓쪽, 약 243pt) 부근 이하.
                if _first_answer_tall(unit[1:], theme) and w.y > USABLE_PT - 200:
                    w.force_break = True
                emit_group(w, {"blocks": unit}, theme)
                i = k
                continue
        emit_block(w, blk, theme)
        i += 1


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
    # 머리부 est는 PDF 실측(눈썹줄~첫 절 제목 97pt)에 맞춘다 — 과소 추정이
    # 누적되면 쪽 나눔 판단 전체가 밀린다(5회차 실측 보정).
    if head["eyebrow"]:
        w.para([_run(head["eyebrow"], CH_GRAY_SMALL)], est_pt=22.0, style=ST_CAPTION)
    w.para([_run(head["title"], CH_TITLE)], PP_TITLE, est_pt=36.0, style=ST_TITLE)
    meta = head["meta"] or head["name_line"]
    if meta:
        meta = meta.replace("Materials:", "준비물:")
        w.para([_run(meta, CH_GRAY_SMALL)], est_pt=30.0, style=ST_CAPTION)
    for blk in preamble_blocks(doc):
        emit_block(w, blk, theme)
    for section in doc.get("sections", []):
        heading = str(section.get("heading", "")).rstrip(": ")
        # 절 제목 앞 est 기반 쪽나눔은 두지 않는다: 문단 꼬리가 이미 다음 쪽으로
        # 흘러넘어간 뒤 명시적 쪽나눔이 걸리면 한 쪽이 통째로 비는 것을 5회차에
        # 실측했다(드리프트 -706pt). 제목 고립은 keepWithNext가 조판 시점에 막고,
        # 어울림 데이터 표는 제목 아래에서 행 단위로 채워진다.
        if heading:
            w.para([_run(heading, CH_H1)], PP_H1, est_pt=38.0, style=ST_H1)
        emit_section_blocks(w, section.get("blocks", []), theme)
    if doc.get("footer_note"):
        w.para([_run(str(doc["footer_note"]), CH_GRAY_SMALL)], est_pt=14.0,
               style=ST_CAPTION)
    # 표로 끝나면 한글에서 마지막 표 아래에 커서를 놓을 수 없다(결함 F9) — 빈 문단 마감.
    if w.parts and "<hp:tbl" in w.parts[-1]:
        w.para([_run("", CH_BODY)], est_pt=6.0)

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
           'media-type="application/xml"/>'
           '<opf:item id="prvtext" href="Preview/PrvText.txt" '
           'media-type="text/plain"/></opf:manifest>'
           '<opf:spine><opf:itemref idref="header" linear="no"/>'
           '<opf:itemref idref="section0" linear="yes"/></opf:spine></opf:package>')
    # version.xml·settings.xml — OWPML 표준 패키지 구성(결함 S5). "tagetApplication"
    # 오탈자는 스펙·한컴 산출물 그대로다 — 고치지 않는다.
    version = ('<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'
               '<hv:HCFVersion xmlns:hv="http://www.hancom.co.kr/hwpml/2011/version" '
               'tagetApplication="WORDPROCESSOR" major="5" minor="1" micro="1" '
               'buildNumber="0" os="10" xmlVersion="1.5" '
               'application="science-teacher-skills" appVersion="1.0"/>')
    settings = ('<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>'
                '<ha:HWPApplicationSetting '
                'xmlns:ha="http://www.hancom.co.kr/hwpml/2011/app" '
                'xmlns:config="urn:oasis:names:tc:opendocument:xmlns:config:1.0">'
                '<ha:CaretPosition listIDRef="0" paraIDRef="0" pos="0"/>'
                '</ha:HWPApplicationSetting>')

    with zipfile.ZipFile(out_path, "w") as z:
        z.writestr(zipfile.ZipInfo("mimetype"), "application/hwp+zip",
                   compress_type=zipfile.ZIP_STORED)
        for name, content in (("version.xml", version),
                              ("META-INF/container.xml", container),
                              ("Contents/content.hpf", hpf),
                              ("Contents/header.xml", build_header_xml()),
                              ("Contents/section0.xml", w.xml()),
                              ("settings.xml", settings),
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
