#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""범대륙 초국가 — 범주 → 캐논 변환 (원문 보존 / 축약 불가).

세력과 다른 '범주' 모델: 범주 1개 = 복수 조직의 집합.
  캐논: 무역상단.md (범주 개요) + 무역상단/<조직슬러그>/<개요+카테고리>.md

범대륙 2번 범주 — 대륙 무역 상단 (Syndicates), 10개 조직.

콜아웃 정밀 처리 (clean_callouts):
  [제거] `[!CAUTION]/[!NOTE]` 의 에픽섭리·The Anchor(에반 개입 당위성) 소제목
  [제거] `[!INFO] 세력 심층 아카이브` (문서 메타 안내)
  [제거] `[!INFO] 세력 소속 장소` (장소 파일 generic 메타)
  [보존] `가혹한 섭리 (Grim Plausibility)` 소제목 — 개연성 본문
  [보존] `[!INFO] 극한의 변경 거점` — 장소 스텁 본문
  → 같은 [!NOTE] 안에 Grim Plausibility + Anchor 혼재 시 Anchor만 제거

파벌 dedup: 같은 영문명(괄호 안)의 번호변형 중복은 2자리패딩/최장본 1개만 채택.
"""
import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from 링크복원 import restore_wikilinks, build_canon_slugs
CANON_SLUGS = build_canon_slugs("/home/user/canon-forge/docs/canon")

ARCHIVE = ("/tmp/tfs/THE FORGOTTEN SUMMONER/01. 아스트라리스 크로니클/"
           "01-8. 세력 아카이브 (국가·조직 정리)")
OUT_BASE = "/home/user/canon-forge/docs/canon/2-무대/세력"

CATEGORY = {
    "src":      "6. 범대륙 초국가 및 중립 세력 (Supranational & Neutral)/6-2. 대륙 무역 상단 (Syndicates)",
    "out":      "무역상단",
    "kr":       "대륙 무역 상단",
    "slug":     "syndicates",
    "overview": "00. 무역 상단 및 신디케이트 개요.md",
    "rel_prefix": "01-8. 세력 아카이브/6. 범대륙 초국가/6-2. 대륙 무역 상단",
    "aliases":  ["대륙 무역 상단", "Syndicates", "무역 상단"],
}
ORGS = [
    ("01. 황금 나침반 상회 (Golden Compass Consortium)",        "황금나침반상회",       "황금 나침반 상회",       "golden-compass"),
    ("02. 붉은 모래 상인회 (Red Sands Consortium)",             "붉은모래상인회",        "붉은 모래 상인회",       "red-sands"),
    ("03. 심연의 천칭 (Scales of the Abyss)",                  "심연의천칭",           "심연의 천칭",            "scales-abyss"),
    ("04. 크리사오르 해양 무역상회 (Chrysaor Maritime Merchants)", "크리사오르해양무역상회", "크리사오르 해양 무역상회", "chrysaor-maritime"),
    ("05. 데메테르 곡물 연합 (Demeter Grain Consortium)",       "데메테르곡물연합",      "데메테르 곡물 연합",      "demeter-grain"),
    ("06. 테라바이트 마석 유통단 (Terabyte Aether Traders)",    "테라바이트마석유통단",  "테라바이트 마석 유통단",  "terabyte-aether"),
    ("07. 타르타로스 노예 옥션 (Tartarus Slave Auctions)",      "타르타로스노예옥션",    "타르타로스 노예 옥션",    "tartarus-slave"),
    ("08. 판도라의 상자 (Pandora's Box Syndicates)",           "판도라의상자",          "판도라의 상자",           "pandoras-box"),
    ("09. 루벨라이트 보석 상단 (Rubellite Jewel Alliance)",    "루벨라이트보석상단",    "루벨라이트 보석 상단",    "rubellite-jewel"),
    ("11. 제피로스 대상단 (Zephyrus Syndicate)",               "제피로스대상단",        "제피로스 대상단",         "zephyrus-syndicate"),
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
REMOVE_HEADER = ["세력 심층 아카이브", "세력 소속 장소"]  # INFO 메타 → 전체 제거
KEEP_HEADER   = ["변경 거점"]                              # INFO 장소 스텁 → 보존
REMOVE_SUB    = ["Epic Burden", "십자가", "The Anchor", "개입의 당위성",
                 "개입의 맹목적 당위성", "에픽 섭리", "Providence"]
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
    if not segs:                       # 소제목 없는 단순 콜아웃 → 보존(중립)
        return block
    kept = []
    for seg in segs:
        t = "\n".join(seg)
        if any(s in t for s in KEEP_SUB):
            kept.append(seg)
        elif any(s in t for s in REMOVE_SUB):
            pass
        else:
            kept.append(seg)           # 중립 소제목 보존
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
    """파일명 괄호 안 영문을 dedup 키로. 없으면 번호 제거한 한글명."""
    m = re.search(r"\(([^)]+)\)\.md$", fname)
    if m:
        return m.group(1).strip().lower()
    return re.sub(r"^\d+\.\s*", "", fname[:-3]).strip().lower()


def dedup_factions(files):
    """같은 영문명의 번호변형 중복 → 2자리패딩/최장본 1개만."""
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

for org_dir, org_out, org_kr, org_slug in ORGS:
    od = os.path.join(SRC_ROOT, org_dir)
    if not os.path.isdir(od):
        print("  [MISS ORG]", org_dir); continue
    nav_items = []

    # 조직 개요: 루트 .md 파일 (번호 있든 없든 첫 번째 .md)
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
