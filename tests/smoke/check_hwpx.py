"""렌더된 hwpx의 한글 무결성 검사: U+FFFD 없음 + 핵심 한글 문자열 존재.

표준 라이브러리만 사용한다 (렌더러와 동일한 의존성 원칙).
"""
import glob
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from check_lesson import hwpx_text  # noqa: E402


def main(outdir):
    paths = sorted(glob.glob(f"{outdir}/*.hwpx"))
    assert paths, f"no hwpx in {outdir}"
    combined = ""
    for p in paths:
        text = hwpx_text(p)
        assert "�" not in text, f"replacement character in {p}"
        combined += text
        print(f"ok: {p} ({len(text)} chars)")
    for needle in ["과학적으로 탐구할 수 있다", "탐구", "무엇이 보이나요", "설명하지 않고 제시"]:
        assert needle in combined, f"missing: {needle}"
    print("korean smoke test passed")


if __name__ == "__main__":
    main(sys.argv[1])
