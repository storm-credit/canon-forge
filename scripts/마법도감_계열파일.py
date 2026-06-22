#!/usr/bin/env python3
"""
마법 도감 계열 파일 생성 스크립트 (W3 마법 백과)
- 21계열 × 90주문 (1~9서클 각 10) = ~1,890주문
- 계열별 1파일 (서클 오름차순 ## 섹션, 세부명세 + 권능묘사)
- 헌터 전용 특수 마법 = 별도 1파일 (보일러만 제거)
- 정령/연금 도감과 동일한 계열별 파일 입자도
"""
import re
import sys
from pathlib import Path

BASE = Path("/tmp/tfs/THE FORGOTTEN SUMMONER/01. 아스트라리스 크로니클/01-31. 마법 백과/06. 마법도감")
SRC_ELEM = BASE / "6-1. 원소 마법계"
SRC_TRAIT = BASE / "6-2. 특질 및 초상 마법계"
SRC_HUNTER = BASE / "헌터 전용 특수 마법 (Hunter Arts).md"
DST = Path("/home/user/canon-forge/docs/canon/1-시스템/마법-도감")
TODAY = "2026-06-22"

# 계열 대분류 표시
GROUP_LABEL = {"6-1": "원소 마법계 (Elemental)", "6-2": "특질·초상 마법계 (Trait & Paranormal)"}

# 계열 이모지 (폴더 순서)
SERIES_EMOJI = {
    "6-1-1": "🔥", "6-1-2": "💧", "6-1-3": "❄️", "6-1-4": "⛰️", "6-1-5": "🌪️",
    "6-1-6": "⚡", "6-1-7": "🌿", "6-1-8": "⚙️", "6-1-9": "☀️", "6-1-10": "🌑",
    "6-2-1": "📜", "6-2-2": "🕳️", "6-2-3": "⏳", "6-2-4": "👤", "6-2-5": "💤",
    "6-2-6": "🧠", "6-2-7": "👁️", "6-2-8": "🐍", "6-2-9": "💀", "6-2-10": "🩸", "6-2-11": "🌌",
}


# ── Cleaning (도감_계열파일.py 패턴 재사용) ──────────────────────────────────

def strip_frontmatter(text):
    if text.startswith("---"):
        end = text.find("\n---\n", 3)
        if end != -1:
            return text[end + 5:]
    return text


def strip_boilerplate(text):
    return re.sub(r"> \[!NOTE\].*?(?=\n\n(?!>)|\Z)", "", text, flags=re.DOTALL)


def fix_roamlinks(text, strip_en=False):
    def _sub(m):
        inner = m.group(1)
        parts = [p.strip() for p in re.split(r"[/\\]", inner) if p.strip()]
        last = parts[-1] if parts else inner
        last = re.sub(r"^\[.*?\]\s*", "", last)
        if strip_en:
            last = re.sub(r"\s*\([A-Za-z\s'\-]+\)\s*$", "", last)
        return last.strip()
    return re.sub(r"\[\[([^\]|]+?)(?:\|[^\]]+)?\]\]", _sub, text)


def clean_body(text):
    text = strip_frontmatter(text)
    text = strip_boilerplate(text)
    text = fix_roamlinks(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_sections(text):
    spec_m = re.search(r"### 세부 명세\s*\n(.*?)(?=###|\Z)", text, re.DOTALL)
    desc_m = re.search(r"### 권능 및 묘사\s*\n(.*?)(?=###|\Z)", text, re.DOTALL)
    spec = spec_m.group(1).strip() if spec_m else ""
    desc = desc_m.group(1).strip() if desc_m else ""
    return spec, desc


# ── Series folder name parsing ─────────────────────────────────────────────

def parse_folder(name):
    """'6-1-1. 화염 마법 (Pyromancy)' → ('6-1-1', '화염 마법', 'Pyromancy')."""
    m = re.match(r"(6-\d+-\d+)\.\s*(.+?)\s*\(([^)]+)\)\s*$", name)
    if not m:
        return None, name, ""
    return m.group(1), m.group(2).strip(), m.group(3).strip()


def parse_spell_h1(h1):
    """'# [1서클] 이그나이트 (Ignite)' → (circle:int, name_kr, name_en)."""
    line = h1.lstrip("# ").strip()
    line = fix_roamlinks(line).strip()
    cm = re.match(r"\[(\d+)서클\]\s*", line)
    circle = int(cm.group(1)) if cm else 99
    rest = line[cm.end():] if cm else line
    m = re.match(r"(.+?)\s*\(([^)]+)\)\s*$", rest)
    if m:
        return circle, m.group(1).strip(), m.group(2).strip()
    return circle, rest.strip(), ""


def short_fname(skey, ko):
    """'6-1-1', '화염 마법' → '6-1-1.화염마법.md'."""
    ko_compact = ko.replace(" ", "")
    return f"{skey}.{ko_compact}.md"


def make_series_file(skey, ko, en, src_dir):
    """Returns (filename, content, spell_count)."""
    group = "-".join(skey.split("-")[:2])  # '6-1'
    emoji = SERIES_EMOJI.get(skey, "✨")
    spells = []  # (circle, name_kr, name_en, spec, desc)
    for src_file in sorted(src_dir.iterdir()):
        if src_file.suffix != ".md":
            continue
        text = src_file.read_text(encoding="utf-8")
        h1_m = re.search(r"^# .+$", text, re.MULTILINE)
        if not h1_m:
            continue
        circle, name_kr, name_en = parse_spell_h1(h1_m.group(0))
        body = clean_body(text)
        spec, desc = extract_sections(body)
        spells.append((circle, name_kr, name_en, spec, desc))

    spells.sort(key=lambda x: (x[0], x[1]))

    ko_title = f"{ko} ({en})"
    lines = [
        "---",
        f"canon_id: system.magic.{skey.replace('-','')}.series",
        f"정본명: {ko_title}",
        "유형: 마법 계열 도감",
        f"분류: {GROUP_LABEL.get(group, group)}",
        f'출처: "01-31. 마법 백과/06. 마법도감/{group}/{skey}. {ko} ({en})"',
        f"검증상태: Phase 2 전수 보존 (원문 보존, {TODAY})",
        "---",
        "",
        f"# {emoji} {ko_title}",
        "",
        f"> [마법체계](../마법체계.md)의 부속 도감 — {GROUP_LABEL.get(group, group)}. 총 {len(spells)}주문 (1~9서클).",
        "",
    ]

    cur_circle = None
    for circle, name_kr, name_en, spec, desc in spells:
        if circle != cur_circle:
            lines.append(f"### {circle}서클")
            lines.append("")
            cur_circle = circle
        h2 = f"## [{circle}서클] {name_kr} ({name_en})" if name_en else f"## [{circle}서클] {name_kr}"
        lines.append(h2)
        lines.append("")
        if spec:
            spec_inline = re.sub(r"\s*\n\s*-\s*", " · ", spec)  # 줄바꿈+불릿 → ·
            spec_inline = re.sub(r"^-\s*", "", spec_inline)       # 첫 불릿 제거
            spec_inline = re.sub(r"\s+", " ", spec_inline).strip()
            lines.append(f"**세부 명세**: {spec_inline}")
            lines.append("")
        lines.append(desc if desc else "⚠️미표기")
        lines.append("")
        lines.append("---")
        lines.append("")

    return short_fname(skey, ko), "\n".join(lines), len(spells)


def make_hunter_file():
    text = SRC_HUNTER.read_text(encoding="utf-8")
    body = clean_body(text)
    body = re.sub(r"^# .+\n", "", body, count=1).strip()
    lines = [
        "---",
        "canon_id: system.magic.hunter.arts",
        "정본명: 헌터 전용 특수 마법 (Hunter Arts)",
        "유형: 마법 계열 도감",
        "분류: 야성의 연금술 (Primal Alchemy)",
        '출처: "01-31. 마법 백과/06. 마법도감/헌터 전용 특수 마법 (Hunter Arts)"',
        f"검증상태: Phase 2 전수 보존 (원문 보존, {TODAY})",
        "---",
        "",
        "# 🏹 헌터 전용 특수 마법 (Hunter Arts)",
        "",
        "> [마법체계](../마법체계.md)의 부속 도감 — 마탑 정규 학문과 선을 긋는 야성의 생존 술법. 수명·혈관을 대가로 한 강제 진화술.",
        "",
        body,
    ]
    return "\n".join(lines)


def make_index(series_info):
    lines = [
        "---",
        "canon_id: system.magic.lexicon.index",
        "정본명: 마법 도감 — 21계열 1,890주문 + 헌터 전용",
        "유형: 전체 인덱스",
        '출처: "01-31. 마법 백과/06. 마법도감"',
        f"검증상태: Phase 2 전수 보존 (원문 보존, {TODAY})",
        "---",
        "",
        "# 마법 도감 — 21계열 전수 인덱스 (Magic Lexicon)",
        "",
        "> [마법체계](../마법체계.md)의 부속 인덱스. 서클·심연화·마법사 등급 체계는 마법체계 본문이 정본. "
        "각 계열은 1~9서클의 주문 트리를 ## 섹션으로 전개한다.",
        "",
    ]
    by_group = {}
    for skey, ko, en, fname, cnt in series_info:
        group = "-".join(skey.split("-")[:2])
        by_group.setdefault(group, []).append((skey, ko, en, fname, cnt))

    for group in sorted(by_group):
        lines.append(f"## {GROUP_LABEL.get(group, group)}")
        lines.append("")
        lines.append("| # | 계열 | 주문 수 |")
        lines.append("|---|------|--------|")
        for skey, ko, en, fname, cnt in sorted(by_group[group], key=lambda x: int(x[0].split("-")[2])):
            emoji = SERIES_EMOJI.get(skey, "✨")
            lines.append(f"| {skey} | {emoji} [{ko} ({en})]({fname}) | {cnt} |")
        lines.append("")

    lines.append("## 특수 계열")
    lines.append("")
    lines.append("| 계열 | 링크 |")
    lines.append("|------|------|")
    lines.append("| 🏹 헌터 전용 특수 마법 | [헌터 전용 (Hunter Arts)](헌터전용특수마법.md) |")
    return "\n".join(lines)


def run():
    import shutil
    if DST.exists():
        shutil.rmtree(DST)
    DST.mkdir(parents=True, exist_ok=True)

    series_info = []
    for src_root in (SRC_ELEM, SRC_TRAIT):
        print(f"\n=== {src_root.name} ===")
        for src_dir in sorted(src_root.iterdir()):
            if not src_dir.is_dir():
                continue
            skey, ko, en = parse_folder(src_dir.name)
            if not skey:
                print(f"  [WARN] 파싱 실패: {src_dir.name}", file=sys.stderr)
                continue
            fname, content, cnt = make_series_file(skey, ko, en, src_dir)
            (DST / fname).write_text(content, encoding="utf-8")
            series_info.append((skey, ko, en, fname, cnt))
            print(f"  {SERIES_EMOJI.get(skey,'✨')} {fname} ({cnt}주문)")

    # Hunter arts
    (DST / "헌터전용특수마법.md").write_text(make_hunter_file(), encoding="utf-8")
    print("\n  🏹 헌터전용특수마법.md")

    # Index
    series_info.sort(key=lambda x: (x[0].split("-")[1], int(x[0].split("-")[2])))
    (DST / "index.md").write_text(make_index(series_info), encoding="utf-8")
    print("  index.md")

    total_spells = sum(c for *_, c in series_info)
    print(f"\n완료: {len(series_info)}계열 + 헌터1 + index = {len(series_info)+2}파일 / 총 {total_spells}주문")


if __name__ == "__main__":
    run()
