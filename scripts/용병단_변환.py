#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""범대륙 초국가 — 대륙 용병단 (Mercenaries) → 캐논 변환.

무역상단_변환.py와 동일한 '범주' 모델 (범주 1개 = 복수 조직 집합).
  캐논: 용병단.md (범주 개요) + 용병단/<조직슬러그>/<개요+카테고리>.md

범대륙 3번 범주 — 대륙 용병단 (Mercenaries), 13개 조직.
무역상단과 달리 원본이 stub 보일러가 아니라 풍부한 실서사 → transform 변환만 수행.

콜아웃 정밀 처리 / 파벌 dedup 등은 무역상단_변환과 공유(아래 함수 동일).
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 링크복원 import restore_wikilinks, build_canon_slugs
CANON_SLUGS = build_canon_slugs("/home/user/canon-forge/docs/canon")

ARCHIVE = ("/tmp/tfs/THE FORGOTTEN SUMMONER/01. 아스트라리스 크로니클/"
           "01-8. 세력 아카이브 (국가·조직 정리)")
OUT_BASE = "/home/user/canon-forge/docs/canon/2-무대/세력"

CATEGORY = {
    "src":      "6. 범대륙 초국가 및 중립 세력 (Supranational & Neutral)/6-3. 대륙 용병단 (Mercenaries)",
    "out":      "용병단",
    "kr":       "대륙 용병단",
    "slug":     "mercenaries",
    "overview": "00. 용병단 목록.md",
    "rel_prefix": "01-8. 세력 아카이브/6. 범대륙 초국가/6-3. 대륙 용병단",
    "aliases":  ["대륙 용병단", "Mercenaries", "용병단"],
}
ORGS = [
    ("1. 저주받은 용병단 (Cursed Mercenaries)",        "저주받은용병단",   "저주받은 용병단",   "cursed"),
    ("2. 그리핀 기사단 (Order of the Gryphon)",        "그리핀기사단",     "그리핀 기사단",     "gryphon-order"),
    ("3. 붉은 칼날 용병단 (Red Blades Mercenaries)",    "붉은칼날용병단",   "붉은 칼날 용병단",   "red-blades"),
    ("4. 검은 파도 용병단 (Black Tide Mercenaries)",    "검은파도용병단",   "검은 파도 용병단",   "black-tide"),
    ("5. 유랑 기사단 (Wandering Knights)",             "유랑기사단",       "유랑 기사단",       "wandering-knights"),
    ("6. 철혈 부대 (Iron Blood Corps)",                "철혈부대",         "철혈 부대",         "iron-blood"),
    ("7. 바람의 칼날 (Wind Blades)",                   "바람의칼날",       "바람의 칼날",       "wind-blades"),
    ("8. 바이퍼 해적단 (Viper Raiders)",               "바이퍼해적단",     "바이퍼 해적단",     "viper-raiders"),
    ("9. 황금 기계단 (Golden Mechanists)",             "황금기계단",       "황금 기계단",       "golden-mechanists"),
    ("10. 강철의 형제단 (Brotherhood of Steel)",       "강철의형제단",     "강철의 형제단",     "brotherhood-steel"),
    ("11. 신성 계약단 (Divine Covenant)",              "신성계약단",       "신성 계약단",       "divine-covenant"),
    ("12. 자연의 방랑자 (Wanderers of Nature)",        "자연의방랑자",     "자연의 방랑자",     "wanderers-nature"),
    ("13. 발키리아 용병단 (Valkyria Mercenaries)",     "발키리아용병단",   "발키리아 용병단",   "valkyria"),
]
CATEGORIES = [
    ("1. 주요 장소 (Locations)",             "장소.md",     "주요 장소",     "locations"),
    ("2. 군사 (Military)",                   "군사.md",     "군사",          "military"),
    ("3. 파벌 (Factions)",                   "파벌.md",     "파벌",          "factions"),
    ("4. 외교 (Diplomacy)",                  "외교.md",     "외교",          "diplomacy"),
    ("5. 역사 (History)",                    "역사.md",     "역사",          "history"),
    ("7. 법률 및 규범 (Laws & Norms)",       "법률규범.md", "법률 및 규범",  "law"),
    ("8. 경제 및 상업 (Economy & Commerce)", "경제상업.md", "경제 및 상업",  "economy"),
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
    if any(s in header for s in REMOVE_HEADER):
        return []
    if any(s in header for s in KEEP_HEADER):
        return block
    segs, cur = [], []
    for ln in block[1:]:
        if _SUB.match(ln):
            if cur:
                segs.append(cur)
            cur = [ln]
        else:
            cur.append(ln)
    if cur:
        segs.append(cur)
    if not segs:
        return block
    kept = []
    for seg in segs:
        t = "\n".join(seg)
        if any(s in t for s in KEEP_SUB):
            kept.append(seg)
        elif any(s in t for s in REMOVE_SUB):
            pass
        else:
            kept.append(seg)
    if not kept:
        return []
    res = [header]
    for seg in kept:
        res.extend(seg)
    while res and res[-1].strip() in (">", ""):
        res.pop()
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
                while out and out[-1].strip() in ("", "---"):
                    out.pop()
                while j < n and lines[j].strip() in ("", "---"):
                    j += 1
                if out and out[-1].strip() != "":
                    out.append("")
            i = j
            continue
        out.append(lines[i]); i += 1
    return "\n".join(out)


# ── 기타 변환 함수 ────────────────────────────────────────────────────────────
def strip_frontmatter(text):
    if text.startswith("---"):
        m = re.match(r"^---\s*\n.*?\n---\s*\n", text, re.DOTALL)
        if m:
            return text[m.end():]
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
            lines[i] = "# " + korean_name
            break
    return "\n".join(lines)


def clean_body(raw):
    t = clean_callouts(strip_frontmatter(raw))
    return collapse_blanks(clean_wikilinks(strip_hashtag_lines(t)))


def transform(src_path, korean_name):
    raw = open(src_path, encoding="utf-8", errors="replace").read()
    t = clean_callouts(strip_frontmatter(raw))
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
    if m:
        return m.group(1).strip().lower()
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
