#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""무역상단 조직 2곳 판타지 톤 개명 (현대 어휘 정규화).

  타르타로스 노예 옥션  → 타르타로스 노예 경매장   (옥션=auction 외래어 → 경매)
  테라바이트 마석 유통단 → 무진 마석 유통단         (테라바이트=저장단위 → 무진=끝없음)

보존: `출처:` 경로 줄, `canon_id:` 줄 (원본 추적·내부 식별자 — 손대지 않음).
변경: 본문 + `정본명:`/`조직:` 표시값 + 폴더명/파일명 + mkdocs nav.
idempotent.
"""
import os, re

CANON = "/home/user/canon-forge/docs/canon/2-무대/세력/무역상단"
MKDOCS = "/home/user/canon-forge/mkdocs.yml"

# (폴더슬러그, [(정규식, 치환)...]) — 본문/표시 프론트매터 공용
JOBS = [
    ("테라바이트마석유통단", [
        ("테라바이트", "무진"),
    ]),
    ("타르타로스노예옥션", [
        ("타르타로스 노예 옥션", "타르타로스 노예 경매장"),
        ("옥션", "경매"),
    ]),
]
PRESERVE_PREFIXES = ("출처:", "canon_id:", '  - "01-8')  # 이 줄들은 치환 제외


def apply_repls(text, repls):
    for a, b in repls:
        text = text.replace(a, b)
    return text


def process_file(path, repls):
    lines = open(path, encoding="utf-8").read().split("\n")
    out = []
    for ln in lines:
        stripped = ln.lstrip()
        if any(stripped.startswith(p) for p in PRESERVE_PREFIXES):
            out.append(ln)               # 출처/식별자 줄 보존
        else:
            out.append(apply_repls(ln, repls))
    open(path, "w", encoding="utf-8").write("\n".join(out))


def main():
    renames = []   # (old_dir, new_dir)
    for slug, repls in JOBS:
        d = os.path.join(CANON, slug)
        if not os.path.isdir(d):
            print(f"[MISS] {slug}"); continue
        # 1) 각 .md 본문/표시값 치환
        for f in sorted(os.listdir(d)):
            if f.endswith(".md"):
                process_file(os.path.join(d, f), repls)
        # 2) 조직 개요 파일명(= 슬러그.md) 치환
        new_slug = apply_repls(slug, repls)
        old_ov = os.path.join(d, slug + ".md")
        if os.path.isfile(old_ov):
            os.rename(old_ov, os.path.join(d, new_slug + ".md"))
        # 3) 폴더명 치환
        if new_slug != slug:
            new_d = os.path.join(CANON, new_slug)
            os.rename(d, new_d)
            renames.append((slug, new_slug))
            print(f"[개명] {slug}/  →  {new_slug}/")

    # 4) mkdocs.yml: 경로 + 라벨 일괄 치환
    mk = open(MKDOCS, encoding="utf-8").read()
    for old_slug, new_slug in renames:
        mk = mk.replace(f"무역상단/{old_slug}/", f"무역상단/{new_slug}/")
    # nav 라벨/파일명 표시 치환
    mk = mk.replace("테라바이트마석유통단", "무진마석유통단")
    mk = mk.replace("테라바이트 마석 유통단", "무진 마석 유통단")
    mk = mk.replace("타르타로스노예옥션", "타르타로스노예경매장")
    mk = mk.replace("타르타로스 노예 옥션", "타르타로스 노예 경매장")
    open(MKDOCS, "w", encoding="utf-8").write(mk)
    print("[mkdocs] nav 경로·라벨 갱신")


if __name__ == "__main__":
    main()
