#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""성국·왕국연합·자유도시연합 서사 11카테고리 → 캐논 변환 (원문 보존).

배경: 이 3세력은 엔티티(도시·성지·요새·기사단·가문·암약조직·상인협회)만
개별화됐고, 서사 카테고리(외교·역사·사회정치·법률규범·경제상업·종교문화·
예술건축·의복생활·마법체계·생활양식·주요인물)는 세력.md에 축약돼 있었다.
마법협회·정령연합과 동일한 카테고리당 전수 보존 모델로 정합화한다.

규칙(정령연합_변환.py와 동일):
  [제거] 구 YAML frontmatter
  [제거] 끝의 [!CAUTION](세력 우주적 십자가)·[!NOTE](에픽 섭리) 보일러플레이트
  [제거] 해시태그 줄
  [제거] '등가교환' 파일 — 폐기된 Hanesis 주입 레이어(작업프롬프트 WARNING) → 의도적 생략
  [변환] 위키링크 → plain text, H1 → 한국어명
"""
import os, re

ARCHIVE = ("/tmp/tfs/THE FORGOTTEN SUMMONER/01. 아스트라리스 크로니클/"
           "01-8. 세력 아카이브 (국가·조직 정리)/1. 에테르 대륙 (Ether Continent)")
OUT_BASE = "/home/user/canon-forge/docs/canon/2-무대/세력"


def strip_frontmatter(text):
    if text.startswith("---"):
        m = re.match(r"^---\s*\n.*?\n---\s*\n", text, re.DOTALL)
        if m:
            return text[m.end():]
    return text


def strip_boilerplate(text):
    lines = text.split("\n")
    cut = None
    for i, ln in enumerate(lines):
        if ("세력의 우주적 십자가" in ln) or ("에픽 섭리와 유구한 운명" in ln):
            j = i
            while j > 0 and (lines[j-1].strip().startswith(">") or
                             lines[j-1].strip() == "" or lines[j-1].strip() == "---"):
                j -= 1
            cut = j
            break
    if cut is not None:
        lines = lines[:cut]
    return "\n".join(lines)


def strip_hashtag_lines(text):
    out = []
    for ln in text.split("\n"):
        if re.match(r"^#[^#\s]", ln.strip()):
            continue
        out.append(ln)
    return "\n".join(out)


def clean_wikilinks(text):
    text = re.sub(r"\[\[[^\]\|]*\|([^\]]*)\]\]", r"\1", text)
    def repl(m):
        return m.group(1).split("/")[-1].strip()
    return re.sub(r"\[\[([^\]]*)\]\]", repl, text)


def collapse_blanks(text):
    return re.sub(r"\n{3,}", "\n\n", text).strip() + "\n"


def clean_body(raw):
    return collapse_blanks(clean_wikilinks(strip_hashtag_lines(
        strip_boilerplate(strip_frontmatter(raw)))))


# ── 세력 정의 ────────────────────────────────────────────────────────────────
FACTIONS = [
    {"src": "1. 성국 (Saint Haven)",        "out": "성국",        "slug": "saint-haven",     "kr": "성국"},
    {"src": "2. 왕국연합 (Allied Kingdoms)", "out": "왕국연합",    "slug": "allied-kingdoms", "kr": "왕국연합"},
    {"src": "3. 자유도시연합 (Crossroad Cities)", "out": "자유도시연합", "slug": "crossroad-cities", "kr": "자유도시연합"},
]

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

created = []
skipped_deprecated = []

for fac in FACTIONS:
    src_root = os.path.join(ARCHIVE, fac["src"])
    out_root = os.path.join(OUT_BASE, fac["out"])
    kr, slug = fac["kr"], fac["slug"]

    def rel_src(p):
        return f"01-8. 세력 아카이브/1. 에테르 대륙/{fac['src']}/" + os.path.relpath(p, src_root)

    print(f"\n{'='*56}\n{kr}\n{'='*56}")

    for sub, outname, cat, label, prefix in MERGE:
        d = os.path.join(src_root, sub)
        if not os.path.isdir(d):
            print(f"  [MISS] {sub}")
            continue
        files = [f for f in sorted(os.listdir(d)) if f.endswith(".md")]
        parts, srcs = [], []
        for fname in files:
            if EXCLUDE_RE.search(fname):
                skipped_deprecated.append(f"{kr}/{sub}/{fname}")
                continue
            src = os.path.join(d, fname)
            srcs.append(src)
            parts.append(clean_body(open(src, encoding="utf-8", errors="replace").read()))
        if not parts:
            print(f"  [SKIP 빈] {outname}")
            continue
        merged = f"# {kr} {label}\n\n" + "\n\n---\n\n".join(parts)
        fm = ("---\n"
              f"canon_id: faction.{slug}.lore.{prefix}\n"
              f"정본명: {kr} {label}\n"
              f"유형: 세력 — 서사({cat})\n"
              f"세력: {kr}\n"
              "출처:\n" + "".join(f'  - "{rel_src(s)}"\n' for s in srcs) +
              "검증상태: Phase 2 전수 보존 (원문 보존, 2026-06-20)\n---\n\n")
        out_path = os.path.join(out_root, outname)
        os.makedirs(out_root, exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(fm + merged)
        created.append(out_path)
        print(f"  [서사] {outname}  ({len(srcs)}개 원본 병합)")

print(f"\n총 생성 서사 파일: {len(created)}개")
if skipped_deprecated:
    print(f"\n의도적 생략 (등가교환 Hanesis 레이어) {len(skipped_deprecated)}건:")
    for s in skipped_deprecated:
        print("  -", s)
