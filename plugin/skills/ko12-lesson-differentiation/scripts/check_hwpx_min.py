#!/usr/bin/env python3
# Copyright 2026 science-teacher-skills contributors
# SPDX-License-Identifier: Apache-2.0

"""렌더 직후 실행되는 최소 품질 게이트 (render_all.sh가 자동 호출).

전체 품질 검사(저장소의 tests/check_hwpx_quality.py — 서식 회귀·HTML 파리티까지)의
부분집합만 본다: 스킬 런타임은 배포 환경에서 빠르고 의존성 없이 돌아야 하므로
"교사에게 전달되면 안 되는 파일"만 여기서 잡는다. 표준 라이브러리 전용, 1초 내.

  G1 zip·mimetype 구조    G2 XML well-formed    G3 U+FFFD 없음
  G4 본문 텍스트 존재      G5 영어 크롬 잔존 없음  G6 마크다운 리터럴(**) 없음

Usage: python check_hwpx_min.py <outdir>
Exit 0 = 통과, 1 = 실패(렌더 산출물을 교사에게 전달하지 말 것).
"""
from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

ENGLISH_CHROME = ("Target standard", "Students see", "Builds on",
                  "Mathematical practices")


def check(path: Path) -> list[str]:
    errs: list[str] = []
    try:
        zf = zipfile.ZipFile(path)
    except zipfile.BadZipFile:
        return ["G1: zip이 아님"]
    with zf:
        infos = zf.infolist()
        if not infos or infos[0].filename != "mimetype" \
                or infos[0].compress_type != zipfile.ZIP_STORED:
            errs.append("G1: mimetype이 첫 STORED 엔트리가 아님")
        texts: list[str] = []
        for info in infos:
            if not info.filename.endswith((".xml", ".hpf")):
                continue
            try:
                root = ET.fromstring(zf.read(info.filename))
            except ET.ParseError as e:
                errs.append(f"G2: {info.filename} XML 오류: {e}")
                continue
            if "section" in info.filename:
                for el in root.iter():
                    if isinstance(el.tag, str) and el.tag.endswith("}t") and el.text:
                        texts.append(el.text)
        joined = "\n".join(texts)
        if "�" in joined:
            errs.append("G3: U+FFFD(치환 문자) 존재")
        if len(joined.strip()) < 20:
            errs.append("G4: 본문 텍스트가 사실상 비어 있음")
        for chrome in ENGLISH_CHROME:
            if chrome in joined:
                errs.append(f"G5: 영어 크롬 잔존: {chrome!r}")
        if re.search(r"\*\*[^*\n]+\*\*", joined):
            errs.append("G6: 마크다운 리터럴 ** 잔존")
    return errs


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: check_hwpx_min.py OUTDIR", file=sys.stderr)
        return 2
    outdir = Path(sys.argv[1])
    files = sorted(outdir.glob("*.hwpx"))
    if not files:
        print(f"gate: {outdir}에 hwpx 없음", file=sys.stderr)
        return 1
    bad = 0
    for f in files:
        errs = check(f)
        if errs:
            bad += 1
            print(f"gate FAIL: {f.name}", file=sys.stderr)
            for e in errs:
                print(f"  {e}", file=sys.stderr)
        else:
            print(f"gate ok: {f.name}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
