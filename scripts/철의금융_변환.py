#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""범대륙 초국가 — 철의 금융 연맹 (Iron Bank) → 캐논 변환.

범대륙 5번 범주 — 철의 금융 연맹, 9개 조직.
마도공학_변환.py와 완전히 동일한 구조 (장소 제외, ## 2. 서사적 디테일 제거).
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 링크복원 import restore_wikilinks, build_canon_slugs
CANON_SLUGS = build_canon_slugs("/home/user/canon-forge/docs/canon")

ARCHIVE = ("/tmp/tfs/THE FORGOTTEN SUMMONER/01. 아스트라리스 크로니클/"
           "01-8. 세력 아카이브 (국가·조직 정리)")
OUT_BASE = "/home/user/canon-forge/docs/canon/2-무대/세력"

CATEGORY = {
    "src":      "6. 범대륙 초국가 및 중립 세력 (Supranational & Neutral)/6-5. 철의 금융 연맹 (Iron Bank)",
    "out":      "철의금융",
    "kr":       "철의 금융 연맹",
    "slug":     "iron-bank",
    "overview": "00. 철의 금융 카르텔 개요.md",
    "rel_prefix": "01-8. 세력 아카이브/6. 범대륙 초국가/6-5. 철의 금융 연맹",
    "aliases":  ["철의 금융 연맹", "Iron Bank", "철의금융연맹"],
}

ORGS = [
    ("01. 하이본 기축 은행 (Highborn Central Bank)",       "하이본기축은행",       "하이본 기축 은행",       "highborn-bank"),
    ("02. 무혈의 징수단 (The Bloodless Ring)",             "무혈의징수단",          "무혈의 징수단",          "bloodless-ring"),
    ("03. 카이저 기축 중앙은행 (Kaiser Central Bank)",     "카이저기축중앙은행",    "카이저 기축 중앙은행",   "kaiser-bank"),
    ("04. 옵시디언 중립 금고 (Obsidian Vaults)",           "옵시디언중립금고",      "옵시디언 중립 금고",     "obsidian-vaults"),
    ("05. 하데스 무혈 징수단 (Hades Bloodless Ring)",      "하데스무혈징수단",      "하데스 무혈 징수단",     "hades-ring"),
    ("06. 스틱스 고위험 신용금고 (Styx Risk Depository)", "스틱스고위험신용금고",  "스틱스 고위험 신용금고", "styx-depository"),
    ("07. 엘도라도 카지노 연합 (Eldorado Casino Cartel)", "엘도라도카지노연합",    "엘도라도 카지노 연합",   "eldorado-casino"),
    ("08. 미다스의 손 환전소 (Hand of Midas Exchange)",   "미다스의손환전소",      "미다스의 손 환전소",     "midas-exchange"),
    ("09. 템플러 성기사 금고 (Templar's Holy Vault)",     "템플러성기사금고",      "템플러 성기사 금고",     "templar-vault"),
]

CATEGORIES = [
    # ("1. 주요 장소 (Locations)", "장소.md", "주요 장소", "locations"),  # Wonder 보일러 → 생략
    ("2. 군사 (Military)",                    "군사.md",     "군사",          "military"),
    ("3. 파벌 (Factions)",                    "파벌.md",     "파벌",          "factions"),
    ("4. 외교 (Diplomacy)",                   "외교.md",     "외교",          "diplomacy"),
    ("5. 역사 (History)",                     "역사.md",     "역사",          "history"),
    ("7. 법률 및 규범 (Laws & Norms)",        "법률규범.md", "법률 및 규범",  "law"),
    ("8. 경제 및 상업 (Economy & Commerce)",  "경제상업.md", "경제 및 상업",  "economy"),
    ("9. 예하 부대 및 기사단 (Military Units)", "예하부대.md", "예하 부대",   "units"),
]

# ── 콜아웃 정밀 처리 ──────────────────────────────────────────────────────────
REMOVE_HEADER = ["세력 심층 아카이브", "세력 소속 장소"]
KEEP_HEADER   = ["변경 거점"]
REMOVE_SUB    = ["Epic Burden", "십자가", "The Anchor", "개입의 당위성",
                 "개입의 맹목적 당위성", "개입의 낭만적 당위성", "에픽 섭리", "Providence"]
KEEP_SUB      = ["Grim Plausibility", "가혹한 섭리"]
_OPEN = re.compile(r"^\s*>\s*\[!(?:CAUTION|NOTE|WARNING|IMPORTANT|INFO)\]")
_SUB  = re.compile(r"^\s*>\s*\*\*\[")


def _process_block(block):
    header = block[0]
    if any(s in header for s in REMOVE_HEADER): return []
    if any(s in header for s in KEEP_HEADER): return block
    segs, cur = [], []
    for ln in block[1:]:
        if _SUB.match(ln):
            if cur: segs.append(cur)
            cur = [ln]
        else:
            cur.append(ln)
    if cur: segs.append(cur)
    if not segs: return block
    kept = []
    for seg in segs:
        t = "\n".join(seg)
        if any(s in t for s in KEEP_SUB):    kept.append(seg)
        elif any(s in t for s in REMOVE_SUB): pass
        else:                                  kept.append(seg)
    if not kept: return []
    res = [header]
    for seg in kept: res.extend(seg)
    while res and res[-1].strip() in (">", ""): res.pop()
    return res


def clean_callouts(text):
    lines = text.split("\n")
    out = []
    i, n = 0, len(lines)
    while i < n:
        if _OPEN.match(lines[i]):
            j = i + 1
            block = [lines[i]]
            while j < n and (lines[j].lstrip().startswith(">") or
                             (lines[j].strip() == "" and j + 1 < n and
                              lines[j + 1].lstrip().startswith(">"))):
                block.append(lines[j]); j += 1
            kept = _process_block(block)
            if kept:
                out.extend(kept)
            else:
                while out and out[-1].strip() in ("", "---"): out.pop()
                while j < n and lines[j].strip() in ("", "---"): j += 1
                if out and out[-1].strip() != "": out.append("")
            i = j; continue
        out.append(lines[i]); i += 1
    return "\n".join(out)


_EPIC_DETAIL_H = re.compile(r"^## 2\. 서사적 디테일\s*(?:\(Epic Detail\))?", re.MULTILINE)

def strip_epic_detail(text):
    lines = text.split("\n")
    out = []
    skip = False
    for ln in lines:
        if _EPIC_DETAIL_H.match(ln.strip()):
            skip = True; continue
        if skip:
            if re.match(r"^#{1,6}\s", ln):
                skip = False; out.append(ln)
        else:
            out.append(ln)
    return "\n".join(out)


def strip_frontmatter(text):
    if text.startswith("---"):
        m = re.match(r"^---\s*\n.*?\n---\s*\n", text, re.DOTALL)
        if m: return text[m.end():]
    return text


def strip_hashtag_lines(text):
    return "\n".join(ln for ln in text.split("\n")
                     if not re.match(r"^#[^#\s]", ln.strip()))


def clean_wikilinks(text):
    return restore_wikilinks(text, CANON_SLUGS)


def collapse_blanks(text):
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def fix_h1(text, korean_name):
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        if ln.startswith("# "):
            lines[i] = "# " + korean_name; break
    return "\n".join(lines)


def clean_body(raw):
    t = clean_callouts(strip_frontmatter(raw))
    t = strip_epic_detail(t)
    return collapse_blanks(clean_wikilinks(strip_hashtag_lines(t)))


def transform(src_path, korean_name):
    raw = open(src_path, encoding="utf-8", errors="replace").read()
    t = clean_callouts(strip_frontmatter(raw))
    t = strip_epic_detail(t)
    return collapse_blanks(fix_h1(clean_wikilinks(strip_hashtag_lines(t)), korean_name))


def read(p):
    return open(p, encoding="utf-8", errors="replace").read()


def walk_md(folder):
    out = []
    for root, _, files in os.walk(folder):
        for f in sorted(files):
            if f.endswith(".md"):
                out.append(os.path.join(root, f))
    return sorted(out)


def en_key(fname):
    m = re.search(r"\(([^)]+)\)\.md$", fname)
    if m: return m.group(1).strip().lower()
    return re.sub(r"^\d+\.\s*", "", fname[:-3]).strip().lower()


def dedup_factions(files):
    groups = {}
    for f in files:
        groups.setdefault(en_key(os.path.basename(f)), []).append(f)
    chosen = []
    for fs in groups.values():
        if len(fs) == 1:
            chosen.append(fs[0]); continue
        def score(p):
            b = os.path.basename(p)
            pad = 1 if re.match(r"^0\d[.\s]", b) else 0
            return (pad, len(read(p)))
        chosen.append(max(fs, key=score))
    return sorted(chosen)


# ── 실행 ─────────────────────────────────────────────────────────────────────
SRC_ROOT = os.path.join(ARCHIVE, CATEGORY["src"])
OUT_ROOT = os.path.join(OUT_BASE, CATEGORY["out"])
kr, cslug = CATEGORY["kr"], CATEGORY["slug"]
NAV_ONLY = bool(os.environ.get("NAV_ONLY"))


def rel_src(p):
    return CATEGORY["rel_prefix"] + "/" + os.path.relpath(p, SRC_ROOT)


def frontmatter(canon_id, name, category, org_kr, srcs):
    out = ("---\n"
           f"canon_id: {canon_id}\n"
           f"정본명: {name}\n"
           f"유형: 범대륙 — {category}\n"
           f"범주: {kr}\n")
    if org_kr:
        out += f"조직: {org_kr}\n"
    if srcs:
        out += "출처:\n" + "".join(f'  - "{rel_src(s)}"\n' for s in srcs)
    out += "검증상태: Phase 2 전수 보존 (원문 보존, 2026-06-21)\n---\n\n"
    return out


def write_out(rel_out, fm, body):
    path = os.path.join(OUT_ROOT, rel_out)
    if NAV_ONLY:
        return path
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(fm + body)
    return path


created = []
nav_orgs = []

ov_src = os.path.join(SRC_ROOT, CATEGORY["overview"])
ov_body = transform(ov_src, CATEGORY["kr"] + f" ({CATEGORY['aliases'][1]})")
ov_fm = ("---\n"
         "tags:\n"
         "  - canon/phase2\n  - lore/supranational\n"
         f"  - supranational/{cslug}\n"
         "aliases:\n" + "".join(f"  - {a}\n" for a in CATEGORY["aliases"]) +
         "type: 범대륙\n"
         "검증상태: Phase 2 전수 보존 (원문 보존, 2026-06-21)\n---\n\n")
ov_path = os.path.join(OUT_BASE, CATEGORY["out"] + ".md")
if not NAV_ONLY:
    with open(ov_path, "w", encoding="utf-8") as f:
        f.write(ov_fm + ov_body)
created.append(ov_path)
print("[범주 개요]", CATEGORY["out"] + ".md")

ORG_FILTER = os.environ.get("ORG_FILTER", "").split(",") if os.environ.get("ORG_FILTER") else None
for org_dir, org_out, org_kr, org_slug in ORGS:
    if ORG_FILTER and org_out not in ORG_FILTER:
        continue
    od = os.path.join(SRC_ROOT, org_dir)
    if not os.path.isdir(od):
        print("  [MISS ORG]", org_dir); continue
    nav_items = []

    main_ov = None
    for f in sorted(os.listdir(od)):
        if f.endswith(".md"):
            main_ov = os.path.join(od, f); break
    if main_ov:
        body = transform(main_ov, org_kr)
        fm = frontmatter(f"supranational.{cslug}.org.{org_slug}", org_kr,
                         "조직 개요", org_kr, [main_ov])
        created.append(write_out(os.path.join(org_out, org_out + ".md"), fm, body))
        print(f"  [조직 개요] {org_kr}")

    for sub, outname, label, prefix in CATEGORIES:
        d = os.path.join(od, sub)
        if not os.path.isdir(d):
            print(f"    [MISS] {org_kr}/{sub}"); continue
        files = walk_md(d)
        if prefix == "factions":
            files = dedup_factions(files)
        if not files:
            print(f"    [빈] {org_kr}/{label}"); continue
        parts = [clean_body(read(p)) for p in files]
        merged = f"# {org_kr} — {label}\n\n" + "\n\n---\n\n".join(parts)
        fm = frontmatter(f"supranational.{cslug}.{org_slug}.{prefix}",
                         f"{org_kr} {label}", label, org_kr, files)
        created.append(write_out(os.path.join(org_out, outname), fm, merged))
        nav_items.append((label, outname, len(files)))
        print(f"    [{label}] {outname}  ({len(files)}개 병합)")

    nav_orgs.append((org_kr, org_out, nav_items))

print(f"\n총 생성 파일: {len(created)}개")
print("\n─── mkdocs nav 스니펫 ───")
print(f"              - {kr} (범대륙):")
print(f"                  - 범주 개요: 2-무대/세력/{CATEGORY['out']}.md")
for org_kr, org_out, items in nav_orgs:
    print(f"                  - {org_kr}:")
    print(f"                      - 조직 개요: 2-무대/세력/{CATEGORY['out']}/{org_out}/{org_out}.md")
    for label, outname, _ in items:
        print(f"                      - {label}: 2-무대/세력/{CATEGORY['out']}/{org_out}/{outname}")
