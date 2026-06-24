#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""세력 폴더 단위 in-place 위키링크 복원 (본문 보존, 재변환 불가 세력용).

성국·왕국연합·자유도시연합 엔티티는 [C][D] 수동 검수를 거쳐 전용 재변환
스크립트가 없다. 재변환하면 그 수동 정비가 날아가므로, **본문은 그대로 두고
죽은 위키링크(평문)만** 원본을 출처로 복원한다.

방식:
  1) 원본 세력 폴더 전체를 스캔 → 각 위키링크의 (납작한텍스트 → 복원형) 매핑 수집
     - 납작한텍스트 = 옛 clean_wikilinks 결과(마지막 세그먼트 또는 |뒤 별칭)
     - 복원형      = 링크복원.restore_wikilinks 결과 ([[직업체계|성기사]] 등)
  2) 캐논 세력 폴더의 각 .md 본문에서 그 납작한텍스트를 복원형으로 치환
     - frontmatter(출처 경로 등)는 건드리지 않는다
     - 긴 텍스트부터 치환(부분문자열 충돌 방지)
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 링크복원 import restore_wikilinks, build_canon_slugs

ARCHIVE = ("/tmp/tfs/THE FORGOTTEN SUMMONER/01. 아스트라리스 크로니클/"
           "01-8. 세력 아카이브 (국가·조직 정리)")
CANON = "/home/user/canon-forge/docs/canon"
SLUGS = build_canon_slugs(CANON)

CHRON = "/tmp/tfs/THE FORGOTTEN SUMMONER/01. 아스트라리스 크로니클"

# (원본 세력 폴더 절대경로, 캐논 세력/대륙 폴더명)
TARGETS = [
    # (원본 폴더, 캐논 2-무대 하위경로)
    (os.path.join(ARCHIVE, "1. 에테르 대륙 (Ether Continent)/1. 성국 (Saint Haven)"),        "세력/성국"),
    (os.path.join(ARCHIVE, "1. 에테르 대륙 (Ether Continent)/2. 왕국연합 (Allied Kingdoms)"), "세력/왕국연합"),
    (os.path.join(ARCHIVE, "1. 에테르 대륙 (Ether Continent)/3. 자유도시연합 (Crossroad Cities)"), "세력/자유도시연합"),
    # 5대륙 (세력 아카이브 밖 — 01-3~7)
    (os.path.join(CHRON, "01-3. 생명의 숲 – 에테르 대륙 (Eter Continent)"),        "에테르대륙"),
    (os.path.join(CHRON, "01-4. 붉은 황무지 – 크림슨 대륙 (Crimson Continent)"),    "크림슨대륙"),
    (os.path.join(CHRON, "01-5. 얼음의 땅 – 프로스트 대륙 (Frost Continent)"),      "프로스트대륙"),
    (os.path.join(CHRON, "01-6. 그림자의 대지 – 오벨리스크 대륙 (Obelisk Continent)"), "오벨리스크대륙"),
]

WIKILINK_RE = re.compile(r"\[\[([^\[\]]+)\]\]")


def flatten_old(inner):
    """옛 clean_wikilinks가 만들던 납작한 텍스트 재현."""
    if "|" in inner:
        # [[A|B]] -> B  (표 셀의 \| 이스케이프 포함)
        return inner.split("|", 1)[1].strip()
    return inner.split("/")[-1].strip()


def collect_mapping(src_folder):
    mapping = {}
    for dp, _, fns in os.walk(src_folder):
        for fn in fns:
            if not fn.endswith(".md"):
                continue
            raw = open(os.path.join(dp, fn), encoding="utf-8", errors="replace").read()
            raw = re.sub(r"\[{3,}", "[[", raw)
            raw = re.sub(r"\]{3,}", "]]", raw)
            for m in WIKILINK_RE.finditer(raw):
                inner = m.group(1)
                flat = flatten_old(inner)
                if not flat or flat.startswith("["):
                    continue
                # 안전장치: 번호접두사(NN. / NN-N.) 있는 죽은텍스트만 치환 대상.
                # '성국'·'솔라리스' 같은 일반명사 flat은 본문 곳곳을 오염시키므로 제외.
                if not re.match(r"^\d+[-.]", flat):
                    continue
                restored = restore_wikilinks("[[" + inner + "]]", SLUGS)
                if restored != flat:
                    mapping[flat] = restored
    return mapping


def split_frontmatter(text):
    m = re.match(r"^---\s*\n.*?\n---\s*\n", text, re.DOTALL)
    if m:
        return text[:m.end()], text[m.end():]
    return "", text


def apply_to_canon(canon_folder, canon_md, mapping):
    files = []
    if os.path.isfile(canon_md):
        files.append(canon_md)
    for dp, _, fns in os.walk(canon_folder):
        for fn in fns:
            if fn.endswith(".md"):
                files.append(os.path.join(dp, fn))
    # 긴 flat 먼저 (부분문자열 충돌 방지)
    keys = sorted(mapping.keys(), key=len, reverse=True)
    changed = 0
    for path in files:
        text = open(path, encoding="utf-8").read()
        fm, body = split_frontmatter(text)
        out_lines = []
        dirty = False
        for line in body.split("\n"):
            # 헤더 줄(# ~ ######)은 치환하지 않는다 (헤더에 위키링크 주입 방지)
            if re.match(r"^#{1,6}\s", line):
                out_lines.append(line); continue
            new_line = line
            for flat in keys:
                if flat in new_line:
                    new_line = new_line.replace(flat, mapping[flat])
            if new_line != line:
                dirty = True
            out_lines.append(new_line)
        if dirty:
            open(path, "w", encoding="utf-8").write(fm + "\n".join(out_lines))
            changed += 1
    return changed, len(files)


def main():
    for src_folder, canon_name in TARGETS:
        if not os.path.isdir(src_folder):
            print(f"[MISS] {canon_name}"); continue
        mapping = collect_mapping(src_folder)
        canon_folder = os.path.join(CANON, "2-무대", canon_name)
        canon_md = os.path.join(CANON, "2-무대", canon_name + ".md")
        changed, total = apply_to_canon(canon_folder, canon_md, mapping)
        print(f"[{canon_name}] 매핑 {len(mapping)}종 · {changed}/{total} 파일 패치")


if __name__ == "__main__":
    main()
