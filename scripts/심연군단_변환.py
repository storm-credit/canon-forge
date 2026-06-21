#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""세력 아카이브 → 캐논 변환 (원문 보존 / 축약 불가).

마법협회·정령연합·3세력과 동일한 카테고리당 전수 보존 모델.
세력 하나씩 디테일하게, 내용 축약 없이 처리한다.

규칙:
  [제거] 구 YAML frontmatter
  [제거] 끝의 [!CAUTION](세력 우주적 십자가)·[!NOTE](에픽 섭리) 보일러플레이트 tail
  [제거] 해시태그 줄
  [유지] 그 외 모든 본문 (서사 포인트·에반 접점 등 실제 콘텐츠 보존)
  [변환] 위키링크 [[A/B|C]]→C, [[A/B]]→마지막 세그먼트, H1→한국어명

엔티티: 카테고리 폴더의 파일 1개 → 캐논 1개 (00.목록·0.관계도 파일 제외)
서사  : 카테고리 폴더의 여러 파일 → 1개 병합
"""
import os, re, sys
from collections import defaultdict
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 링크복원 import restore_wikilinks, build_canon_slugs
CANON_SLUGS = build_canon_slugs("/home/user/canon-forge/docs/canon")

ARCHIVE = ("/tmp/tfs/THE FORGOTTEN SUMMONER/01. 아스트라리스 크로니클/"
           "01-8. 세력 아카이브 (국가·조직 정리)")
OUT_BASE = "/home/user/canon-forge/docs/canon/2-무대/세력"

# ── 변환할 세력 설정 (이번 실행 대상) ────────────────────────────────────────
FACTION = {
    "src":        "4. 오벨리스크 대륙 (Obelisk Continent)/1. 심연 군단 (Abyssal Legion)",
    "overview":   "심연 군단 (Abyssal Legion).md",
    "out":        "심연군단",
    "slug":       "abyssal-legion",
    "kr":         "심연 군단",
    "continent":  "obelisk",
    "nav_region": "오벨리스크·심연",
    "rel_prefix": "01-8. 세력 아카이브/4. 오벨리스크 대륙/1. 심연 군단",
    "aliases":    ["심연 군단", "Abyssal Legion", "어비설 리전", "심연의 군세", "악마 군단"],
}

# 엔티티 디렉터리: (원본 하위경로, 출력 하위폴더, 유형 라벨, canon_prefix)
ENTITY = [
    ("1. 주요 장소 (Locations)/도시",     "도시",     "도시",     "city"),
    ("1. 주요 장소 (Locations)/성지",     "성지",     "성지",     "sanctuary"),
    ("1. 주요 장소 (Locations)/요새",     "요새",     "요새",     "fortress"),
    ("1. 주요 장소 (Locations)/금단구역", "금단구역", "금단구역", "forbidden"),
    ("3. 파벌 (Factions)",                "파벌",     "파벌",     "faction-group"),
]
HOUSE_INDEX_SRC = "3. 파벌 (Factions)/0. 심연 군단 세력 관계도.md"

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

EXCLUDE_RE = re.compile(r"등가교환")  # 폐기된 Hanesis 레이어


# ── 변환 함수 ────────────────────────────────────────────────────────────────
def strip_frontmatter(text):
    if text.startswith("---"):
        m = re.match(r"^---\s*\n.*?\n---\s*\n", text, re.DOTALL)
        if m:
            return text[m.end():]
    return text


def strip_boilerplate(text):
    """[!CAUTION] 우주적 십자가 / [!NOTE] 에픽 섭리 보일러플레이트 콜아웃만 제거.

    핵심: 보일러플레이트 콜아웃 블록(> [!CAUTION]/[!NOTE] ... )만 잘라내고,
    그 앞에 있는 실제 콘텐츠 콜아웃(예: > [!note] 제국의 상징)은 보존한다.
    역추적은 '연속된 > 줄'에 한정하고, 보일러플레이트 블록의 opener
    (> [!XXX])에 닿으면 그 블록만 포함하고 멈춘다 — 빈 줄을 건너
    앞 콜아웃까지 빨아들이지 않는다.
    """
    lines = text.split("\n")
    marker = None
    for i, ln in enumerate(lines):
        if ("세력의 우주적 십자가" in ln) or ("에픽 섭리와 유구한 운명" in ln):
            marker = i
            break
    if marker is None:
        return text
    # 이 보일러플레이트 콜아웃 블록의 opener까지만 역추적 (연속 > 줄 한정)
    j = marker
    while j > 0 and lines[j-1].strip().startswith(">"):
        is_opener = re.match(r"^>\s*\[!\w+\]", lines[j-1].strip())
        j -= 1
        if is_opener:
            break
    # opener 직전의 빈 줄·--- 만 정리 (콘텐츠 줄은 건드리지 않음)
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
ov_body = transform(ov_src, FACTION["kr"] + f" ({FACTION['aliases'][1]})")
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

# 2) 엔티티 (도시·성지·요새·가문) ----------------------------------------------
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

# 2-b) 파벌 관계도 → 파벌.md 개요 ----------------------------------------------
hi = os.path.join(SRC_ROOT, HOUSE_INDEX_SRC)
if os.path.exists(hi):
    body = transform(hi, f"{kr} 파벌")
    fm = frontmatter(f"faction.{slug}.faction-group.index", f"{kr} 파벌 관계도",
                     "파벌(개요)", [hi])
    created.append(write_out("파벌.md", fm, body))
    print("  [파벌 개요] 파벌.md")

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
# 엔티티 그룹 순서: ENTITY 정의 순 + 부대 + 암약조직
nav_order = [(outsub, outsub) for _, outsub, _, _ in ENTITY]
nav_order += [("부대", "군사 — 부대"), ("암약조직", "암약조직")]
for grp, label in nav_order:
    items = list(nav_entities[grp])
    if grp == "파벌" and os.path.exists(os.path.join(OUT_ROOT, "파벌.md")):
        items = [("파벌 관계도 (개요)", "파벌.md")] + items
    if not items:
        continue
    print(f"                  - {label}:")
    for nm, path in items:
        print(f"                      - {nm}: 2-무대/세력/{FACTION['out']}/{path}")
