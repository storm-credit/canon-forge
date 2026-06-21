#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""범대륙 초국가 — 그림자 첩보 조직 (Shadow Intelligence) → 캐논 변환.

범대륙 7번 범주 — 그림자 첩보 조직, 6개 조직.

원본 상태:
- 군사/외교/역사/법률/경제: 실서사 풍부
- 가문(Noble Houses, 5개 조직) / 파벌(Factions, 옴니버스 서고 1개 조직): 실내용
- 장소: 최상위 .md = Wonder 보일러 → 제외, 서브디렉토리 파일은 실내용 → 포함
- 예하부대: 전 조직 보유
- 옴니버스 서고 파벌·예하부대: "등불 삼아/기사도의 권능" 보일러 → 4에이전트 재서술 예정
- 서사적 디테일 섹션 없음 (strip 불요)

처리 전략:
1. 장소 카테고리: 최상위 .md 파일(Wonder 보일러)은 건너뛰고 서브디렉토리 파일만 포함
2. cat3 카테고리: 조직별 차이 — 5개 조직은 "3. 가문 (Noble Houses)" → "가문.md",
                               옴니버스 서고는 "3. 파벌 (Factions)" → "파벌.md"
3. 범주 개요: 원본에 루트 .md 없음 → 합성 개요 사용
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 링크복원 import restore_wikilinks, build_canon_slugs
CANON_SLUGS = build_canon_slugs("/home/user/canon-forge/docs/canon")

ARCHIVE = ("/tmp/tfs/THE FORGOTTEN SUMMONER/01. 아스트라리스 크로니클/"
           "01-8. 세력 아카이브 (국가·조직 정리)")
OUT_BASE = "/home/user/canon-forge/docs/canon/2-무대/세력"

CATEGORY = {
    "src":      "6. 범대륙 초국가 및 중립 세력 (Supranational & Neutral)/6-7. 그림자 첩보 조직 (Shadow Intelligence)",
    "out":      "그림자첩보",
    "kr":       "그림자 첩보 조직",
    "slug":     "shadow-intelligence",
    "overview": None,  # 루트 레벨 개요 없음 → 합성
    "rel_prefix": "01-8. 세력 아카이브/6. 범대륙 초국가/6-7. 그림자 첩보 조직",
    "aliases":  ["그림자 첩보 조직", "Shadow Intelligence", "그림자첩보"],
}

# (디렉토리명, 출력슬러그, 한국어명, 캐논슬러그, 개요파일명, cat3_type)
# cat3_type: "houses" → 가문, "factions" → 파벌
ORGS = [
    ("1. 어둠의 손 (Shadow Hand)",               "어둠의손",        "어둠의 손",        "shadow-hand",          "1. 어둠의 손 (Shadow Hand).md",                               "houses"),
    ("2. 창백한 거미줄 첩보망 (Pale Web Syndicate)", "창백한거미줄",  "창백한 거미줄 첩보망", "pale-web",           "2. 그림자 연맹 (Shadow Syndicate).md",                        "houses"),
    ("3. 검은 여우단 (Black Fox Syndicate)",      "검은여우단",      "검은 여우단",      "black-fox",            "3. 검은 여우단 (Black Fox Syndicate).md",                     "houses"),
    ("4. 황야의 추적자들 (Hunters of the Wild)",  "황야의추적자들",  "황야의 추적자들",  "hunters-of-the-wild",  "4. 황야의 추적자들 (Hunters of the Wild).md",                 "houses"),
    ("5. 황금 손아귀 (Golden Claw)",              "황금손아귀",      "황금 손아귀",      "golden-claw",          "5. 황금 손아귀 (Golden Claw).md",                             "houses"),
    ("7. 옴니버스 서고 (Omnibus Archives)",        "옴니버스서고",    "옴니버스 서고",    "omnibus-archives",     "아스트라 대륙 개척자 연맹 (Omnibus Info-Brokers).md",         "factions"),
]

# cat3 정의 (조직별 동적 치환)
CAT3_DEFS = {
    "houses":   ("3. 가문 (Noble Houses)", "가문.md",  "가문",  "houses",   False),
    "factions": ("3. 파벌 (Factions)",     "파벌.md",  "파벌",  "factions", False),
}

# 장소 처리: 서브디렉토리 파일만 (최상위 .md = Wonder 보일러 → 건너뜀)
CATEGORIES_BASE = [
    ("1. 주요 장소 (Locations)",              "장소.md",     "주요 장소",     "locations",  True),
    ("2. 군사 (Military)",                    "군사.md",     "군사",          "military",   False),
    None,  # cat3 placeholder — 조직별 동적 치환
    ("4. 외교 (Diplomacy)",                   "외교.md",     "외교",          "diplomacy",  False),
    ("5. 역사 (History)",                     "역사.md",     "역사",          "history",    False),
    ("7. 법률 및 규범 (Laws & Norms)",        "법률규범.md", "법률 및 규범",  "law",        False),
    ("8. 경제 및 상업 (Economy & Commerce)",  "경제상업.md", "경제 및 상업",  "economy",    False),
    ("9. 예하 부대 및 기사단 (Military Units)", "예하부대.md", "예하 부대",   "units",      False),
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
                while out and out[-1].strip() in ("", "---"): out.pop()
                while j < n and lines[j].strip() in ("", "---"): j += 1
                if out and out[-1].strip() != "": out.append("")
            i = j; continue
        out.append(lines[i]); i += 1
    return "\n".join(out)


# ── 기타 변환 함수 ────────────────────────────────────────────────────────────
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


def is_wonder_boilerplate(path):
    """최상위 Wonder 보일러 파일 여부 감지."""
    try:
        content = open(path, encoding="utf-8", errors="replace").read()
        return ("대자연의 숨결" in content or "기적과 경이" in content)
    except Exception:
        return False


def walk_md(folder, subdir_only=False):
    """subdir_only=True이면 서브디렉토리 파일만, Wonder 보일러는 제외."""
    out = []
    for root, dirs, files in os.walk(folder):
        dirs.sort()
        for f in sorted(files):
            if not f.endswith(".md"):
                continue
            p = os.path.join(root, f)
            if subdir_only and os.path.dirname(p) == folder:
                continue
            if is_wonder_boilerplate(p):
                continue
            out.append(p)
    return sorted(out)


def en_key(fname):
    m = re.search(r"\(([^)]+)\)\.md$", fname)
    if m: return m.group(1).strip().lower()
    return re.sub(r"^\d+\.\s*", "", fname[:-3]).strip().lower()


def dedup_files(files):
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

# ── 범주 개요 (합성) ──────────────────────────────────────────────────────────
SYNTH_OVERVIEW = """# 그림자 첩보 조직 (Shadow Intelligence)

대아스트라리스 세계의 암살·첩보·공작을 전담하는 6개 초국가 비밀 조직의 범주.
어느 단일 국가의 법제에도 속하지 않으며, 의뢰·계약·정보 독점이라는 음지의 논리로 자생한다.
구성원 전원은 신원이 말소되거나 처음부터 공식 기록에 존재하지 않으며,
대륙 간 분쟁의 이면에 이들의 개입이 없었던 사건은 드물다.

## 소속 조직

| 조직 | 영문 | 핵심 정체성 |
|------|------|------------|
| 어둠의 손 | Shadow Hand | 암살·정치 공작, 점조직 운영, 신원 완전 말소 |
| 창백한 거미줄 첩보망 | Pale Web Syndicate | 전 대륙 암흑가 연합, 첩보·암살 복합 범죄 조직 |
| 검은 여우단 | Black Fox Syndicate | 정보 거래·변장 침투, 가면 뒤의 진실 조작 |
| 황야의 추적자들 | Hunters of the Wild | 광야 추적·포획 전문, 현상금 사냥·실종 처리 |
| 황금 손아귀 | Golden Claw | 재화 갈취·협박, 재정 압박을 통한 세력 잠식 |
| 옴니버스 서고 | Omnibus Archives | 정보 중개·매매, 미개척지 정보 독점 브로커 |
"""

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
        f.write(ov_fm + SYNTH_OVERVIEW)
created.append(ov_path)
print("[범주 개요]", CATEGORY["out"] + ".md")

ORG_FILTER = os.environ.get("ORG_FILTER", "").split(",") if os.environ.get("ORG_FILTER") else None
for org_dir, org_out, org_kr, org_slug, ov_filename, cat3_type in ORGS:
    if ORG_FILTER and org_out not in ORG_FILTER:
        continue
    od = os.path.join(SRC_ROOT, org_dir)
    if not os.path.isdir(od):
        print("  [MISS ORG]", org_dir); continue
    nav_items = []

    # 조직 개요 파일
    main_ov = os.path.join(od, ov_filename)
    if os.path.isfile(main_ov):
        body = transform(main_ov, org_kr)
        fm = frontmatter(f"supranational.{cslug}.org.{org_slug}", org_kr,
                         "조직 개요", org_kr, [main_ov])
        created.append(write_out(os.path.join(org_out, org_out + ".md"), fm, body))
        print(f"  [조직 개요] {org_kr}")
    else:
        print(f"  [MISS 개요] {ov_filename}")

    # cat3 동적 치환
    cat3_entry = CAT3_DEFS[cat3_type]
    categories = [cat3_entry if c is None else c for c in CATEGORIES_BASE]

    for sub, outname, label, prefix, subdir_only in categories:
        d = os.path.join(od, sub)
        if not os.path.isdir(d):
            continue
        files = walk_md(d, subdir_only=subdir_only)
        if prefix in ("houses", "factions"):
            files = dedup_files(files)
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
