#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""잊혀진 서고단 (Forgotten Library Order) 세력 아카이브 → 캐논 변환.

카테고리당 전수 보존 모델. 축약 불가.

특이사항:
  - 주요 장소 = 도시(1) + 거점(4) + 금단구역(2) + 유적(1)
  - 학파(5) = 다른 세력의 '가문'에 해당, 학파.md 개요 포함
  - 군사 부대 9개 (01~09 접두사)
  - 군사 전략 4파일 (0-1~0-5) → 전략심화.md 병합
  - 암약조직 2개 (각 1파일씩)
  - 서사 11카테고리
"""
import os, re, sys
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 링크복원 import restore_wikilinks, build_canon_slugs
CANON_SLUGS = build_canon_slugs("/home/user/canon-forge/docs/canon")

ARCHIVE = ("/tmp/tfs/THE FORGOTTEN SUMMONER/01. 아스트라리스 크로니클/"
           "01-8. 세력 아카이브 (국가·조직 정리)")
OUT_BASE = "/home/user/canon-forge/docs/canon/2-무대/세력"

FACTION = {
    "src":        "2. 크림슨 대륙 (Crimson Continent)/5. 잊혀진 서고단 (Forgotten Library Order)",
    "overview":   "잊혀진 서고단.md",
    "out":        "잊혀진서고단",
    "slug":       "forgotten-library-order",
    "kr":         "잊혀진 서고단",
    "continent":  "crimson",
    "nav_region": "크림슨·동부",
    "rel_prefix": "01-8. 세력 아카이브/2. 크림슨 대륙/5. 잊혀진 서고단",
    "aliases":    ["잊혀진 서고단", "Forgotten Library Order", "서고단", "기억의 수호자들"],
}

# 엔티티: (원본 하위경로, 출력 하위폴더, 유형 라벨, canon_prefix)
ENTITY = [
    ("1. 주요 장소 (Locations)/도시",     "도시",     "도시",     "city"),
    ("1. 주요 장소 (Locations)/거점",     "거점",     "거점",     "base"),
    ("1. 주요 장소 (Locations)/금단구역", "금단구역", "금단구역", "forbidden"),
    ("1. 주요 장소 (Locations)/유적",     "유적",     "유적",     "ruin"),
    ("3. 학파 (Schools)",                 "학파",     "학파",     "school"),
]
SCHOOL_INDEX_SRC = "3. 학파 (Schools)/0. 잊혀진 서고단 관계도.md"

MILITARY_UNITS_DIR = "16. 예하 부대 및 기사단 (Military Units)"
MILITARY_STRATEGY_DIR = "2. 군사 (Military)"
CLANDESTINE_DIR = "9. 내부 암약 조직 (Clandestine Organizations)"

# 서사 11종: (원본 폴더, 출력 파일, 유형 라벨, 제목 라벨, canon_prefix)
MERGE = [
    ("4. 외교 (Diplomacy)",                  "외교.md",     "외교",          "외교",      "diplomacy"),
    ("5. 역사 (History)",                    "역사.md",     "역사",          "역사",      "history"),
    ("6. 사회 및 정치 (Society & Politics)", "사회정치.md", "사회 및 정치",  "사회·정치", "society"),
    ("7. 법률 및 규범 (Laws & Norms)",       "법률규범.md", "법률 및 규범",  "법률·규범", "law"),
    ("8. 경제 및 상업 (Economy & Commerce)", "경제상업.md", "경제 및 상업",  "경제·상업", "economy"),
    ("10. 종교 및 문화 (Religion & Culture)", "종교문화.md", "종교 및 문화", "종교·문화", "religion"),
    ("11. 예술 및 건축 (Art & Architecture)", "예술건축.md", "예술 및 건축", "예술·건축", "art"),
    ("12. 의복 및 생활양식",                 "의복생활.md", "의복 및 생활양식", "의복·생활", "clothing"),
    ("13. 마법 체계 (Magic System)",         "마법체계.md", "마법 체계",     "마법체계",  "magic"),
    ("14. 생활양식",                         "생활양식.md", "생활양식",      "생활양식",  "lifestyle"),
    ("15. 주요 인물 (Key Figures)",          "주요인물.md", "주요 인물",     "주요인물",  "figures"),
]

EXCLUDE_RE = re.compile(r"등가교환")


# ── 변환 함수 ────────────────────────────────────────────────────────────────
def strip_frontmatter(text):
    if text.startswith("---"):
        m = re.match(r"^---\s*\n.*?\n---\s*\n", text, re.DOTALL)
        if m:
            return text[m.end():]
    return text


def strip_boilerplate(text):
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
    return "\n".join(ln for ln in text.split("\n")
                     if not re.match(r"^#[^#\s]", ln.strip()))


def clean_wikilinks(text):
    return restore_wikilinks(text, CANON_SLUGS)


def fix_h1(text, korean_name):
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        if ln.startswith("# "):
            lines[i] = "# " + korean_name
            break
    return "\n".join(lines)


def collapse_blanks(text):
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def korean_name_from(fname):
    base = fname[:-3] if fname.endswith(".md") else fname
    base = re.sub(r"^\d+[-.]?\d*\.?\s*", "", base)
    base = re.sub(r"\s*\(.*?\)\s*$", "", base).strip()
    return base


def slug_from(korean):
    return korean.replace(" ", "")


def clean_body(raw):
    return collapse_blanks(clean_wikilinks(strip_hashtag_lines(
        strip_boilerplate(strip_frontmatter(raw)))))


def transform(src_path, korean_name):
    raw = open(src_path, encoding="utf-8", errors="replace").read()
    return collapse_blanks(fix_h1(clean_wikilinks(strip_hashtag_lines(
        strip_boilerplate(strip_frontmatter(raw)))), korean_name))


def is_list_file(fname):
    return bool(re.match(r"^0+[-.]", fname)) or fname.startswith("0.")


# ── 실행 ─────────────────────────────────────────────────────────────────────
SRC_ROOT = os.path.join(ARCHIVE, FACTION["src"])
OUT_ROOT = os.path.join(OUT_BASE, FACTION["out"])
slug, kr = FACTION["slug"], FACTION["kr"]


def rel_src(p):
    return FACTION["rel_prefix"] + "/" + os.path.relpath(p, SRC_ROOT)


def frontmatter(canon_id, name, category, srcs):
    out = ("---\n"
           f"canon_id: {canon_id}\n"
           f"정본명: {name}\n"
           f"유형: 세력 — {category}\n"
           f"세력: {kr}\n")
    if srcs:
        out += "출처:\n" + "".join(f'  - "{rel_src(s)}"\n' for s in srcs)
    out += "검증상태: Phase 2 전수 보존 (원문 보존, 2026-06-20)\n---\n\n"
    return out


def write_out(rel_out, fm, body):
    path = os.path.join(OUT_ROOT, rel_out)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(fm + body)
    return path


created = []
nav_entities = defaultdict(list)

# 1) 개요 ----------------------------------------------------------------------
ov_src = os.path.join(SRC_ROOT, FACTION["overview"])
ov_body = transform(ov_src, FACTION["kr"] + " (Forgotten Library Order)")
ov_fm = ("---\n"
         "tags:\n"
         "  - canon/phase2\n  - lore/faction\n"
         f"  - faction/{slug}\n  - continent/{FACTION['continent']}\n"
         "aliases:\n" + "".join(f"  - {a}\n" for a in FACTION["aliases"]) +
         "type: 세력\n"
         "검증상태: Phase 2 전수 보존 (원문 보존, 2026-06-20)\n---\n\n")
ov_path = os.path.join(OUT_BASE, FACTION["out"] + ".md")
with open(ov_path, "w", encoding="utf-8") as f:
    f.write(ov_fm + ov_body)
created.append(ov_path)
print("[개요]", FACTION["out"] + ".md")

# 2) 엔티티 (도시·거점·금단구역·유적·학파) ----------------------------------------
for sub, outsub, cat, prefix in ENTITY:
    d = os.path.join(SRC_ROOT, sub)
    if not os.path.isdir(d):
        print("  [MISS]", sub); continue
    for fname in sorted(os.listdir(d)):
        if not fname.endswith(".md") or is_list_file(fname):
            continue
        src = os.path.join(d, fname)
        kname = korean_name_from(fname)
        body = transform(src, kname)
        sl = slug_from(kname)
        fm = frontmatter(f"faction.{slug}.{prefix}.{sl}", kname, cat, [src])
        created.append(write_out(os.path.join(outsub, sl + ".md"), fm, body))
        nav_entities[outsub].append((kname, f"{outsub}/{sl}.md"))
        print(f"  [{cat}] {kname}")

# 2-b) 학파 관계도 → 학파.md 개요 -----------------------------------------------
si = os.path.join(SRC_ROOT, SCHOOL_INDEX_SRC)
if os.path.exists(si):
    body = transform(si, f"{kr} 학파")
    fm = frontmatter(f"faction.{slug}.school.index", f"{kr} 학파 관계도",
                     "학파(개요)", [si])
    created.append(write_out("학파.md", fm, body))
    print("  [학파 개요] 학파.md")

# 3) 군사 부대 (16. 예하 부대) -------------------------------------------------
mu = os.path.join(SRC_ROOT, MILITARY_UNITS_DIR)
if os.path.isdir(mu):
    for fname in sorted(os.listdir(mu)):
        if not fname.endswith(".md") or is_list_file(fname):
            continue
        src = os.path.join(mu, fname)
        kname = korean_name_from(fname)
        body = transform(src, kname)
        sl = slug_from(kname)
        fm = frontmatter(f"faction.{slug}.unit.{sl}", kname, "군사 부대", [src])
        created.append(write_out(os.path.join("군사/부대", sl + ".md"), fm, body))
        nav_entities["부대"].append((kname, f"군사/부대/{sl}.md"))
        print(f"  [부대] {kname}")

# 4) 군사 전략 심화 (2. 군사) --------------------------------------------------
ms = os.path.join(SRC_ROOT, MILITARY_STRATEGY_DIR)
if os.path.isdir(ms):
    files = [f for f in sorted(os.listdir(ms)) if f.endswith(".md")]
    parts, srcs = [], []
    for fname in files:
        src = os.path.join(ms, fname)
        srcs.append(src)
        parts.append(clean_body(open(src, encoding="utf-8", errors="replace").read()))
    if parts:
        merged = f"# {kr} 군사 전략 심화\n\n" + "\n\n---\n\n".join(parts)
        fm = frontmatter(f"faction.{slug}.lore.military", f"{kr} 군사 전략 심화",
                         "서사(군사 전략)", srcs)
        created.append(write_out("군사/전략심화.md", fm, merged))
        print(f"  [군사] 전략심화.md  ({len(srcs)}개 병합)")

# 5) 암약조직 (중첩 폴더) ------------------------------------------------------
clan = os.path.join(SRC_ROOT, CLANDESTINE_DIR)
if os.path.isdir(clan):
    for orgdir in sorted(os.listdir(clan)):
        od = os.path.join(clan, orgdir)
        if not os.path.isdir(od):
            continue
        kname = korean_name_from(orgdir)
        parts, srcs = [], []
        for fname in sorted(os.listdir(od)):
            if not fname.endswith(".md"):
                continue
            src = os.path.join(od, fname)
            srcs.append(src)
            parts.append(clean_body(open(src, encoding="utf-8", errors="replace").read()))
        merged = "\n\n---\n\n".join(parts)
        sl = slug_from(kname)
        fm = frontmatter(f"faction.{slug}.clandestine.{sl}", kname, "암약조직", srcs)
        created.append(write_out(os.path.join("암약조직", sl + ".md"), fm, merged))
        nav_entities["암약조직"].append((kname, f"암약조직/{sl}.md"))
        print(f"  [암약조직] {kname}")

# 6) 서사 11종 -----------------------------------------------------------------
for sub, outname, cat, label, prefix in MERGE:
    d = os.path.join(SRC_ROOT, sub)
    if not os.path.isdir(d):
        print("  [MISS MERGE]", sub); continue
    files = [f for f in sorted(os.listdir(d)) if f.endswith(".md")]
    parts, srcs = [], []
    skipped = []
    for fname in files:
        if EXCLUDE_RE.search(fname):
            skipped.append(fname); continue
        src = os.path.join(d, fname)
        srcs.append(src)
        parts.append(clean_body(open(src, encoding="utf-8", errors="replace").read()))
    if not parts:
        print(f"  [SKIP 빈] {outname}"); continue
    merged = f"# {kr} {label}\n\n" + "\n\n---\n\n".join(parts)
    fm = frontmatter(f"faction.{slug}.lore.{prefix}", f"{kr} {label}",
                     f"서사({cat})", srcs)
    created.append(write_out(outname, fm, merged))
    note = f"  (등가교환 {len(skipped)}건 제외)" if skipped else ""
    print(f"  [서사] {outname}  ({len(srcs)}개 병합){note}")

# ── 결과 + nav 스니펫 ────────────────────────────────────────────────────────
print(f"\n총 생성 파일: {len(created)}개")
print("\n─── mkdocs nav 스니펫 ───")
print(f"              - {kr} ({FACTION.get('nav_region', '크림슨')}):")
print(f"                  - 개요: 2-무대/세력/{FACTION['out']}.md")
for _, outname, cat, label, prefix in MERGE:
    print(f"                  - 서사 — {label}: 2-무대/세력/{FACTION['out']}/{outname}")
print(f"                  - 군사 — 전략 심화: 2-무대/세력/{FACTION['out']}/군사/전략심화.md")
nav_order = [(outsub, outsub) for _, outsub, _, _ in ENTITY]
nav_order += [("부대", "군사 — 부대"), ("암약조직", "암약조직")]
for grp, label in nav_order:
    items = list(nav_entities[grp])
    if grp == "학파" and os.path.exists(os.path.join(OUT_ROOT, "학파.md")):
        items = [("학파 관계도 (개요)", "학파.md")] + items
    if not items:
        continue
    print(f"                  - {label}:")
    for nm, path in items:
        print(f"                      - {nm}: 2-무대/세력/{FACTION['out']}/{path}")
