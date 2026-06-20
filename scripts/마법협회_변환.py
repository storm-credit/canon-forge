#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""마법협회 세력 아카이브 → 캐논 변환 (원문 보존 / 축약 불가).
규칙: 본문 그대로 유지. 제거 대상은 (1) 구 YAML frontmatter,
(2) 끝의 [!CAUTION](세력 우주적 십자가)·[!NOTE](에픽 섭리) 보일러플레이트,
(3) 해시태그 줄. 위키링크는 plain text로 정리.
"""
import os, re, sys

SRC_ROOT = "/tmp/tfs/THE FORGOTTEN SUMMONER/01. 아스트라리스 크로니클/01-8. 세력 아카이브 (국가·조직 정리)/1. 에테르 대륙 (Ether Continent)/4. 마법협회 (Arcane Society)"
OUT_ROOT = "/home/user/canon-forge/docs/canon/2-무대/세력/마법협회"

def strip_frontmatter(text):
    if text.startswith("---"):
        m = re.match(r"^---\s*\n.*?\n---\s*\n", text, re.DOTALL)
        if m:
            return text[m.end():]
    return text

def strip_boilerplate(text):
    """[!CAUTION] 우주적 십자가 / [!NOTE] 에픽 섭리 보일러플레이트 콜아웃만 제거.
    앞의 실제 콘텐츠 콜아웃(예: [!note] 순리 노트)은 보존한다."""
    lines = text.split("\n")
    marker = None
    for i, ln in enumerate(lines):
        if ("세력의 우주적 십자가" in ln) or ("에픽 섭리와 유구한 운명" in ln):
            marker = i
            break
    if marker is None:
        return text
    j = marker
    while j > 0 and lines[j-1].strip().startswith(">"):
        is_opener = re.match(r"^>\s*\[!\w+\]", lines[j-1].strip())
        j -= 1
        if is_opener:
            break
    while j > 0 and lines[j-1].strip() in ("", "---"):
        j -= 1
    return "\n".join(lines[:j])

def strip_hashtag_lines(text):
    out = []
    for ln in text.split("\n"):
        s = ln.strip()
        # tag line: '#' followed by a non-'#', non-space char (e.g. "#마법협회 #세력").
        # markdown headers ("## ", "### ") start with '#' then '#', so they are NOT matched.
        if re.match(r"^#[^#\s]", s):
            continue
        out.append(ln)
    return "\n".join(out)

def clean_wikilinks(text):
    # [[A|B]] -> B
    text = re.sub(r"\[\[[^\]\|]*\|([^\]]*)\]\]", r"\1", text)
    # [[A]] -> last path segment, plain text
    def repl(m):
        inner = m.group(1)
        seg = inner.split("/")[-1].strip()
        return seg
    text = re.sub(r"\[\[([^\]]*)\]\]", repl, text)
    return text

def fix_h1(text, korean_name):
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        if ln.startswith("# "):
            lines[i] = "# " + korean_name
            break
    return "\n".join(lines)

def collapse_blanks(text):
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"

def korean_name_from(fname):
    base = fname[:-3] if fname.endswith(".md") else fname
    base = re.sub(r"^\d+[-.]?\d*\.?\s*", "", base)  # strip leading number
    base = re.sub(r"\s*\(.*?\)\s*$", "", base).strip()  # strip trailing (English)
    return base

def slug_from(korean):
    return korean.replace(" ", "")

def transform(src_path, korean_name):
    with open(src_path, encoding="utf-8") as f:
        text = f.read()
    text = strip_frontmatter(text)
    text = strip_boilerplate(text)
    text = strip_hashtag_lines(text)
    text = clean_wikilinks(text)
    text = fix_h1(text, korean_name)
    text = collapse_blanks(text)
    return text

def rel_src(src_path):
    return "01-8. 세력 아카이브/1. 에테르 대륙/4. 마법협회/" + os.path.relpath(src_path, SRC_ROOT)

def frontmatter(canon_id, name, category, src_path=None):
    out = ("---\n"
           f"canon_id: {canon_id}\n"
           f"정본명: {name}\n"
           f"유형: 세력 — {category}\n"
           "세력: 마법협회\n")
    if src_path:
        out += "출처:\n" + f'  - "{rel_src(src_path)}"\n'
    out += "검증상태: Phase 2 전수 보존 (원문 보존, 2026-06-20)\n---\n\n"
    return out

def write_out(rel_out, fm, body):
    path = os.path.join(OUT_ROOT, rel_out)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(fm + body)
    return path

# entity dirs: one canon file per source file (skip 0./00. list files)
ENTITY = [
    # (src subdir, out subdir, category, canon_prefix)
    ("1. 주요 장소 (Locations)/도시", "도시", "도시", "city"),
    ("1. 주요 장소 (Locations)/탑", "탑", "탑", "tower"),
    ("1. 주요 장소 (Locations)/시설", "시설", "시설", "facility"),
    ("3. 학파 (Schools)", "학파", "학파", "school"),
    ("16. 예하 부대 및 기사단 (Military Units)", "군사/기사단", "군사 부대", "unit"),
]
# merge dirs: concatenate all files into one output
MERGE = [
    ("4. 외교 (Diplomacy)", "외교.md", "외교", "외교", "diplomacy"),
    ("5. 역사 (History)", "역사.md", "역사", "역사", "history"),
    ("6. 사회 및 정치 (Society & Politics)", "사회정치.md", "사회 및 정치", "사회·정치", "society"),
    ("7. 법률 및 규범 (Laws & Norms)", "법률규범.md", "법률 및 규범", "법률·규범", "law"),
    ("8. 경제 및 상업 (Economy & Commerce)", "경제상업.md", "경제 및 상업", "경제·상업", "economy"),
    ("10. 종교 및 문화 (Religion & Culture)", "종교문화.md", "종교 및 문화", "종교·문화", "religion"),
    ("11. 예술 및 건축 (Art & Architecture)", "예술건축.md", "예술 및 건축", "예술·건축", "art"),
    ("12. 의복 및 생활양식", "의복생활.md", "의복 및 생활양식", "의복·생활", "clothing"),
    ("13. 마법 체계 (Magic System)", "마법체계.md", "마법 체계", "마법체계", "magic"),
    ("14. 생활양식", "생활양식.md", "생활양식", "생활양식", "lifestyle"),
    ("15. 주요 인물 (Key Figures)", "주요인물.md", "주요 인물", "주요인물", "figures"),
    ("2. 군사 (Military)", "군사/기사단-심화.md", "군사 전략 심화", "군사전략", "military"),
]

def is_list_file(fname):
    return re.match(r"^0+[-.]", fname) or fname.startswith("0.")

created = []

# overview file
ov_src = os.path.join(SRC_ROOT, "마법협회 (Arcane Society).md")
ov_body = transform(ov_src, "마법협회 (Arcane Society)")
ov_fm = ("---\n"
         "tags:\n  - canon/phase2\n  - lore/faction\n  - faction/arcane-society\n  - continent/ether\n"
         "aliases:\n  - 마법협회\n  - Arcane Society\n  - 아르카노스\n"
         "type: 세력\n"
         "검증상태: Phase 2 전수 보존 (원문 보존, 2026-06-20)\n"
         "---\n\n")
p = os.path.join(OUT_ROOT, "마법협회.md")  # placed inside folder? we want sibling
# overview goes to 세력/마법협회.md (sibling of folder)
ov_path = "/home/user/canon-forge/docs/canon/2-무대/세력/마법협회.md"
with open(ov_path, "w", encoding="utf-8") as f:
    f.write(ov_fm + ov_body)
created.append(ov_path)

# entity dirs
for sub, outsub, cat, prefix in ENTITY:
    d = os.path.join(SRC_ROOT, sub)
    if not os.path.isdir(d):
        print("MISSING DIR:", d); continue
    for fname in sorted(os.listdir(d)):
        if not fname.endswith(".md"): continue
        if is_list_file(fname): continue
        src = os.path.join(d, fname)
        kname = korean_name_from(fname)
        body = transform(src, kname)
        slug = slug_from(kname)
        fm = frontmatter(f"faction.arcane-society.{prefix}.{slug}", kname, cat, src)
        outname = slug + ".md"
        created.append(write_out(os.path.join(outsub, outname), fm, body))

# clandestine orgs: nested folders -> one file per org
clan = os.path.join(SRC_ROOT, "9. 내부 암약 조직 (Clandestine Organizations)")
for orgdir in sorted(os.listdir(clan)):
    od = os.path.join(clan, orgdir)
    if not os.path.isdir(od): continue
    kname = korean_name_from(orgdir)
    parts = []
    srcs = []
    for fname in sorted(os.listdir(od)):
        if not fname.endswith(".md"): continue
        src = os.path.join(od, fname)
        srcs.append(src)
        parts.append(transform(src, kname) if fname == sorted(os.listdir(od))[0] else
                     collapse_blanks(clean_wikilinks(strip_hashtag_lines(strip_boilerplate(strip_frontmatter(open(src,encoding='utf-8').read()))))))
    body = "\n\n---\n\n".join(parts)
    slug = slug_from(kname)
    fm = ("---\n"
          f"canon_id: faction.arcane-society.clandestine.{slug}\n"
          f"정본명: {kname}\n"
          "유형: 세력 — 암약조직\n세력: 마법협회\n"
          "출처:\n" + "".join(f'  - "{rel_src(s)}"\n' for s in srcs) +
          "검증상태: Phase 2 전수 보존 (원문 보존, 2026-06-20)\n---\n\n")
    created.append(write_out(os.path.join("암약조직", slug + ".md"), fm, body))

# merge dirs
for sub, outname, cat, label, prefix in MERGE:
    d = os.path.join(SRC_ROOT, sub)
    if not os.path.isdir(d):
        print("MISSING MERGE DIR:", d); continue
    parts = []
    srcs = []
    title = label
    files = [f for f in sorted(os.listdir(d)) if f.endswith(".md")]
    # For 군사(2.) skip the per-unit 01..10 files (those are entities elsewhere); keep 0-x strategy files
    if sub.startswith("2. 군사"):
        files = [f for f in files if re.match(r"^0-\d", f)]
    for i, fname in enumerate(files):
        src = os.path.join(d, fname)
        srcs.append(src)
        raw = open(src, encoding="utf-8").read()
        body = collapse_blanks(clean_wikilinks(strip_hashtag_lines(strip_boilerplate(strip_frontmatter(raw)))))
        parts.append(body)
    merged = f"# 마법협회 {title}\n\n" + "\n\n---\n\n".join(parts)
    fm = ("---\n"
          f"canon_id: faction.arcane-society.lore.{prefix}\n"
          f"정본명: 마법협회 {title}\n"
          f"유형: 세력 — 서사({cat})\n세력: 마법협회\n"
          "출처:\n" + "".join(f'  - "{rel_src(s)}"\n' for s in srcs) +
          "검증상태: Phase 2 전수 보존 (원문 보존, 2026-06-20)\n---\n\n")
    created.append(write_out(outname, fm, merged))

print(f"생성 파일 수: {len(created)}")
for c in sorted(created):
    print(" ", os.path.relpath(c, "/home/user/canon-forge/docs/canon/2-무대/세력"))
