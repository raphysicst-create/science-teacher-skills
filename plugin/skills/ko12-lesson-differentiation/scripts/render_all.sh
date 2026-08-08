#!/usr/bin/env bash
# Copyright 2026 Anthropic, PBC
# Copyright 2026 Learning Commons
# SPDX-License-Identifier: Apache-2.0

# Render all four artifacts (teacher plan + three tier worksheets) from one
# differentiation.json in a single invocation. Writes an editable .hwpx (the teacher
# deliverable — opens in 한글) and an .html twin of each (a browser preview). Standard
# library only — no third-party packages, nothing to install.
# Fail-fast: any renderer error stops the run.
#
# Usage: bash scripts/render_all.sh differentiation.json "$OUTPUT_DIR"
set -euo pipefail

json="${1:?usage: render_all.sh DIFFERENTIATION_JSON OUTPUT_DIR}"
outdir="${2:?usage: render_all.sh DIFFERENTIATION_JSON OUTPUT_DIR}"
here="$(cd "$(dirname "$0")" && pwd)"

mkdir -p "$outdir"
python3 "$here/render_documents.py" "$json" --outdir "$outdir"
python3 "$here/render_lesson_hwpx.py" "$json" --outdir "$outdir"
# 최소 품질 게이트: 구조·인코딩·영어 크롬·마크다운 리터럴. 실패하면 여기서 멈춘다 —
# 게이트에 걸린 산출물은 교사에게 전달하지 않는다. (전체 검사는 저장소의
# tests/check_hwpx_quality.py — hwpx-quality-loop 참고.)
python3 "$here/check_hwpx_min.py" "$outdir"
# Persist the source JSON alongside the rendered artifacts so later revision
# turns can re-render from it (same guarantee the lesson-planning renderer
# makes with lesson.json).
cp "$json" "$outdir/differentiation.json" 2>/dev/null || true

# Delivery guarantee: when $OUTPUT_DIR is set and the render went elsewhere
# (a staging dir like /tmp/out), mirror EVERYTHING into $OUTPUT_DIR too.
# Revision turns re-render from the differentiation.json that lands there;
# hand-copying a subset there is the failure this removes.
if [ -n "${OUTPUT_DIR:-}" ] && [ "$(cd "$outdir" && pwd)" != "$(mkdir -p "$OUTPUT_DIR" && cd "$OUTPUT_DIR" && pwd)" ]; then
  cp -R "$outdir"/. "$OUTPUT_DIR"/
fi
