#!/usr/bin/env python3
"""
도감 계열 파일 생성 스크립트
- 정령 도감: 20계열 × 1 파일 (계열 안에 10정령을 ## 섹션으로)
- 연금 도감: 10분파 × 1 파일 (분파 안에 전 연성식을 ## 섹션으로)
"""
import re
import sys
from pathlib import Path

SRC_SPIRIT = Path("/tmp/tfs/THE FORGOTTEN SUMMONER/01. 아스트라리스 크로니클/01-32. 정령 백과/6. 정령 도감 (Spirit Lexicon)")
SRC_ALCHEMY = Path("/tmp/tfs/THE FORGOTTEN SUMMONER/01. 아스트라리스 크로니클/01-34. 연금 백과/연금 도감")
DST_SPIRIT = Path("/home/user/canon-forge/docs/canon/1-시스템/정령-도감")
DST_ALCHEMY = Path("/home/user/canon-forge/docs/canon/1-시스템/연금-도감")
TODAY = "2026-06-22"

SPIRIT_META = {
    "6-1":  {"ko":"화염계",   "en":"Fire",      "king":"이프리트 (Ifrit)",          "pole":"크림슨 극점: 소멸과 정화의 인과",             "emoji":"🔥"},
    "6-2":  {"ko":"용암계",   "en":"Magma",     "king":"수르트 (Surtr)",             "pole":"크림슨 하층: 지층의 호흡과 제련",             "emoji":"🌋"},
    "6-3":  {"ko":"수계",     "en":"Water",     "king":"스카일라 (Scylla)",          "pole":"해양 표층: 포용과 만물의 융해",               "emoji":"💧"},
    "6-4":  {"ko":"빙하계",   "en":"Ice",       "king":"스카디 (Skadi)",             "pole":"프로스트 극야: 시간의 정지와 영원한 보존",    "emoji":"❄️"},
    "6-5":  {"ko":"대지계",   "en":"Earth",     "king":"티탄 (Titan)",               "pole":"프로스트 심층: 역사의 매장과 웅장한 무게",    "emoji":"⛰️"},
    "6-6":  {"ko":"바람계",   "en":"Wind",      "king":"가루다 (Garuda)",            "pole":"에테르 창공: 방랑과 기억의 전달자",           "emoji":"🌪️"},
    "6-7":  {"ko":"뇌전계",   "en":"Lightning", "king":"퀘찰코아틀 (Quetzalcoatl)", "pole":"에테르 단층: 찢어지는 단죄와 각성",           "emoji":"⚡"},
    "6-8":  {"ko":"빛계",     "en":"Light",     "king":"세라핌 (Seraphim)",          "pole":"솔라리안 상층: 이면이 없는 절대적 진실",      "emoji":"☀️"},
    "6-9":  {"ko":"생명계",   "en":"Life",      "king":"파나케이아 (Panacea)",       "pole":"에테르 성역: 발아하는 우주의 심장박동",        "emoji":"🌿"},
    "6-10": {"ko":"어둠계",   "en":"Darkness",  "king":"에레보스 (Erebus)",          "pole":"오벨리스크 후면: 모든 것을 품는 우주적 요람", "emoji":"🌑"},
    "6-11": {"ko":"부패계",   "en":"Decay",     "king":"파주주 (Pazuzu)",            "pole":"오벨리스크 폐허: 필멸성을 관장하는 가을의 신","emoji":"🍂"},
    "6-12": {"ko":"맹독계",   "en":"Poison",    "king":"요르문간드 (Jörmungandr)",   "pole":"크림슨 하향: 혈관의 시련과 역치 돌파",        "emoji":"🐍"},
    "6-13": {"ko":"금속계",   "en":"Metal",     "king":"아이언 메이든 (Iron Maiden)","pole":"딥 포지 왕국: 무기질의 불변성과 다이아몬드 지조","emoji":"⚙️"},
    "6-14": {"ko":"철혈계",   "en":"Ironblood", "king":"블라드 (Vlad)",              "pole":"어둠의 솔라리안: 굽히지 않는 투지와 선혈의 맹세","emoji":"🩸"},
    "6-15": {"ko":"사령계",   "en":"Death",     "king":"타나토스 (Thanatos)",        "pole":"망자의 강안: 별이 지는 밤의 나루터 보트맨",   "emoji":"👻"},
    "6-16": {"ko":"진혼계",   "en":"Requiem",   "king":"레퀴엠 (Requiem)",           "pole":"수많은 전장: 남겨진 사연의 합창 지휘자",      "emoji":"🕯️"},
    "6-17": {"ko":"정신계",   "en":"Mind",      "king":"크툴가 (Cthugha)",           "pole":"사념의 회랑: 얽히고설킨 뇌파의 은하계",       "emoji":"🧠"},
    "6-18": {"ko":"환영계",   "en":"Illusion",  "king":"파놉티콘 (Panopticon)",      "pole":"신기루 지대: 갈망이 만들어낸 완벽한 거짓 영지","emoji":"👁️"},
    "6-19": {"ko":"심해계",   "en":"Deep Sea",  "king":"레비아탄 (Leviathan)",       "pole":"해양 심해구: 시공간이 멈춘 영원한 중력의 요람","emoji":"🕳️"},
    "6-20": {"ko":"이질규격", "en":"Eldritch",  "king":"아자토스 (Azathoth)",        "pole":"창세의 이면 공간: 섭리 밖의 닫힘과 소거",     "emoji":"🌌"},
}

ALCHEMY_META = {
    "6-1":  {"ko":"투기금속연성", "en":"Steel Transmutation"},
    "6-2":  {"ko":"연소화학",     "en":"Combustion Alchemy"},
    "6-3":  {"ko":"폭발역학",     "en":"Explosive Transmutation"},
    "6-4":  {"ko":"생명연성영약", "en":"Elixir Crafting"},
    "6-5":  {"ko":"생체개조연성", "en":"Biomancy"},
    "6-6":  {"ko":"키메라육종",   "en":"Chimera Forging"},
    "6-7":  {"ko":"맹독조향",     "en":"Lethal Apothecary"},
    "6-8":  {"ko":"광역화학병기", "en":"Chemical Gas Weapons"},
    "6-9":  {"ko":"호문쿨루스",   "en":"Homunculus"},
    "6-10": {"ko":"인공영혼제어", "en":"Soul Binding"},
}

GRADE_DISPLAY = {
    "정령왕": "👑 정령왕",
    "상급(대정령)": "🔴 상급(대정령)",
    "중급": "🟡 중급",
    "하급": "🟢 하급",
}

GRADE_ORDER = {"정령왕": 0, "상급(대정령)": 1, "중급": 2, "하급": 3}

SPIRIT_GRADE_MAP = {
    "정령왕": "정령왕",
    "상급": "상급(대정령)",
    "중급": "중급",
    "하급": "하급",
}


# ── Cleaning ──────────────────────────────────────────────────────────────────

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


def series_key(folder_name):
    m = re.match(r"(6-\d+)\.", folder_name)
    return m.group(1) if m else None


# ── Spirit parsing ────────────────────────────────────────────────────────────

def parse_spirit_h1(h1):
    line = h1.lstrip("# ").strip()
    grade_m = re.match(r"\[([^\]]+)\]\s*", line)
    if not grade_m:
        return "미확인", line, "", ""
    grade_raw = grade_m.group(1).strip()
    grade = SPIRIT_GRADE_MAP.get(grade_raw, grade_raw)
    rest = line[grade_m.end():]
    rest = fix_roamlinks(rest, strip_en=True).strip()
    m = re.match(r"(.+?)\s+\((.+?)\)\s*$", rest)
    if m:
        name_kr = m.group(1).strip()
        inner = m.group(2).strip()
        if " - " in inner:
            parts = inner.split(" - ", 1)
            name_en, subtitle = parts[0].strip(), parts[1].strip()
        else:
            name_en, subtitle = inner, ""
    else:
        name_kr, name_en, subtitle = rest, "", ""
    return grade, name_kr, name_en, subtitle


def make_spirit_series_file(skey, meta, src_dir):
    """Returns (filename, content)."""
    sko, sen = meta['ko'], meta['en']
    src_path = f'출처: "01-32. 정령 백과/6. 정령 도감/{skey}. {sko} 정령 ({sen})"'

    spirits = []  # (grade, name_kr, name_en, subtitle, desc)
    for src_file in sorted(src_dir.iterdir()):
        if src_file.suffix != ".md":
            continue
        text = src_file.read_text(encoding="utf-8")
        h1_m = re.search(r"^# .+$", text, re.MULTILINE)
        if not h1_m:
            continue
        grade, name_kr, name_en, subtitle = parse_spirit_h1(h1_m.group(0))
        body = clean_body(text)
        _, desc = extract_sections(body)
        spirits.append((grade, name_kr, name_en, subtitle, desc))

    spirits.sort(key=lambda x: (GRADE_ORDER.get(x[0], 99), x[1]))

    lines = [
        "---",
        f"canon_id: system.spirit.{skey.replace('-','')}.series",
        f"정본명: {sko} 정령 ({sen} Spirits)",
        "유형: 계열 도감",
        src_path,
        f"검증상태: Phase 2 전수 보존 (원문 보존, {TODAY})",
        "---",
        "",
        f"# {meta['emoji']} {sko} 정령 ({sen} Spirits)",
        "",
        f"**정령왕**: {meta['king']} · **극점**: {meta['pole']}",
        "",
    ]

    # Skadi continental warning
    if skey == "6-4":
        lines += [
            "> **⚠️ 동명이물 — 스카디**: 빙하 **정령왕 스카디**(Skadi)는 빙하 원소의 정점인 정령. "
            "**스카디 아이스블러드**(인간 영웅, 프로스트본 연합 대족장)와 이름만 같은 별개 존재. "
            "→ 정령 속성은 이 파일 §스카디 정본 / 인간 영웅: [영웅-인덱스](../../4-인물/영웅-인덱스.md) §G 정본.",
            "",
        ]

    for grade, name_kr, name_en, subtitle, desc in spirits:
        grade_disp = GRADE_DISPLAY.get(grade, grade)
        h2 = f"## {grade_disp} {name_kr} ({name_en})"
        if subtitle:
            h2 += f" — {subtitle}"
        lines.append(h2)
        lines.append("")
        lines.append(desc if desc else "⚠️미표기")
        lines.append("")
        lines.append("---")
        lines.append("")

    fname = f"{skey}.{sko}.md"
    return fname, "\n".join(lines)


# ── Alchemy parsing ───────────────────────────────────────────────────────────

def parse_alchemy_h1(h1):
    line = h1.lstrip("# ").strip()
    line = fix_roamlinks(line, strip_en=True).strip()
    # Remove number prefixes like "06. " from roamlink residue
    line = re.sub(r"\b(\d+\.\s+)(?=[가-힣])", "", line)
    m = re.match(r"\[([^\]:]+)(?::\s*(.+?))?\]\s*\((.+?)\)\s*$", line)
    if m:
        level_prefix = m.group(1).strip()
        name_kr = (m.group(2) or "").strip()
        name_en = m.group(3).strip()
        return level_prefix, name_kr, name_en
    return line, "", ""


def make_alchemy_branch_file(bkey, meta, src_dir):
    """Returns (filename, content)."""
    ako, aen = meta['ko'], meta['en']
    src_path = f'출처: "01-34. 연금 백과/연금 도감/{bkey}. {ako} ({aen})"'

    formulas = []  # (level_prefix, name_kr, name_en, spec, desc)
    for src_file in sorted(src_dir.iterdir()):
        if src_file.suffix != ".md":
            continue
        text = src_file.read_text(encoding="utf-8")
        h1_m = re.search(r"^# .+$", text, re.MULTILINE)
        if not h1_m:
            continue
        level_prefix, name_kr, name_en = parse_alchemy_h1(h1_m.group(0))
        body = clean_body(text)
        spec, desc = extract_sections(body)
        formulas.append((level_prefix, name_kr, name_en, spec, desc))

    def sort_key(f):
        m = re.search(r"\d+", f[0])
        return int(m.group(0)) if m else 99

    formulas.sort(key=sort_key)

    lines = [
        "---",
        f"canon_id: system.alchemy.{ako}.series",
        f"정본명: {ako} ({aen})",
        "유형: 분파 도감",
        src_path,
        f"검증상태: Phase 2 전수 보존 (원문 보존, {TODAY})",
        "---",
        "",
        f"# {ako} ({aen})",
        "",
        f"총 {len(formulas)}종 연성식",
        "",
    ]

    for level_prefix, name_kr, name_en, spec, desc in formulas:
        level_m = re.match(r"(\d+)", level_prefix)
        level_num = level_m.group(1) if level_m else "?"
        is_truth = "진리의 연성" in level_prefix or ("단계" in level_prefix and int(level_num) == 7)
        display_prefix = f"{level_num}단계 진리" if is_truth else f"{level_num}연성식"

        h2 = f"## {display_prefix} — {name_kr} ({name_en})" if name_kr else f"## {display_prefix} ({name_en})"
        lines.append(h2)
        lines.append("")
        if spec:
            lines.append(f"**세부 명세**: {spec}")
            lines.append("")
        lines.append(desc if desc else "⚠️미표기")
        lines.append("")
        lines.append("---")
        lines.append("")

    fname = f"{bkey}.{ako}.md"
    return fname, "\n".join(lines)


# ── Continental spirit files ──────────────────────────────────────────────────

CONTINENT_FILES = {
    "6-1. 에테르 정령 (Aether Spirits).md":     ("에테르정령.md", "에테르 대륙 정령 (Aether Spirits)"),
    "6-2. 크림슨 정령 (Crimson Spirits).md":    ("크림슨정령.md", "크림슨 대륙 정령 (Crimson Spirits)"),
    "6-3. 프로스트 정령 (Frost Spirits).md":    ("프로스트정령.md", "프로스트 대륙 정령 (Frost Spirits)"),
    "6-4. 오벨리스크 정령 (Obelisk Spirits).md": ("오벨리스크정령.md", "오벨리스크 대륙 정령 (Obelisk Spirits)"),
    "6-5. 해양 정령 (Oceanic Spirits).md":      ("해양정령.md", "해양 대륙 정령 (Oceanic Spirits)"),
}


def process_continent_file(src, title):
    text = src.read_text(encoding="utf-8")
    body = clean_body(text)
    body = re.sub(r"^# .+\n", "", body, count=1).strip()
    src_name = src.name
    lines = [
        "---",
        f"canon_id: system.spirit.continental.{src_name.split('.')[0].replace(' ', '')}",
        f"정본명: {title}",
        "유형: 대륙 정령 도감",
        f'출처: "01-32. 정령 백과/6. 정령 도감/{src_name}"',
        f"검증상태: Phase 2 전수 보존 (원문 보존, {TODAY})",
        "---",
        "",
        f"# {title}",
        "",
        body,
    ]
    return "\n".join(lines)


# ── Top index files ───────────────────────────────────────────────────────────

def make_spirit_index(series_info):
    lines = [
        "---",
        "canon_id: system.spirit.lexicon.index",
        "정본명: 정령 도감 — 20계열 200정령 + 5대륙 대표",
        "유형: 전체 인덱스",
        '출처: "01-32. 정령 백과/6. 정령 도감 (Spirit Lexicon)"',
        f"검증상태: Phase 2 전수 보존 (원문 보존, {TODAY})",
        "---",
        "",
        "# 정령 도감 — 20계열 전수 인덱스 (Spirit Lexicon)",
        "",
        "> [정령체계](../정령체계.md)의 부속 인덱스. 공명 단계·계약·정령 전쟁 체계는 정령체계 본문이 정본.",
        "",
        "> **⚠️ 동명이물 — 스카디**: 빙하계 **정령왕 스카디**(Skadi, 빙하 원소의 정령)는 "
        "인간 영웅 **스카디 아이스블러드**(프로스트본 연합 대족장)와 이름만 같은 별개 존재. "
        "→ 정령 속성: [6-4.빙하계](6-4.빙하계.md) §스카디 정본 / 인간 영웅: [영웅-인덱스](../../4-인물/영웅-인덱스.md) §G 정본.",
        "",
        "## A. 20계열 200정령",
        "",
        "| # | 계열 | 정령왕 | 극점 |",
        "|---|------|--------|------|",
    ]

    for i, (skey, meta, fname) in enumerate(series_info, 1):
        lines.append(f"| {i} | {meta['emoji']} [{meta['ko']} ({meta['en']})]({fname}) | {meta['king']} | {meta['pole']} |")

    lines += [
        "",
        "## B. 5대륙 대표 정령",
        "",
        "| 대륙 | 링크 |",
        "|------|------|",
        "| 에테르 대륙 | [에테르 정령](에테르정령.md) |",
        "| 크림슨 대륙 | [크림슨 정령](크림슨정령.md) |",
        "| 프로스트 대륙 | [프로스트 정령](프로스트정령.md) |",
        "| 오벨리스크 대륙 | [오벨리스크 정령](오벨리스크정령.md) |",
        "| 해양 | [해양 정령](해양정령.md) |",
    ]
    return "\n".join(lines)


def make_alchemy_index(branch_info):
    lines = [
        "---",
        "canon_id: system.alchemy.lexicon.index",
        "정본명: 연금 도감 — 10분파 199연성식",
        "유형: 전체 인덱스",
        '출처: "01-34. 연금 백과/연금 도감"',
        f"검증상태: Phase 2 전수 보존 (원문 보존, {TODAY})",
        "---",
        "",
        "# 연금 도감 — 10분파 전수 인덱스 (Alchemy Lexicon)",
        "",
        "> [연금체계](../연금체계.md)의 부속 인덱스. 연성 7진리·공정·계급 체계는 연금체계 본문이 정본.",
        "",
        "| # | 분파 | 연성식 수 | 링크 |",
        "|---|------|----------|------|",
    ]

    for i, (bkey, meta, fname, count) in enumerate(branch_info, 1):
        lines.append(f"| {i} | {meta['ko']} ({meta['en']}) | {count} | [{meta['ko']}]({fname}) |")

    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────────────

def run():
    import shutil

    # Clean up previous individual-file structure
    print("=== 기존 폴더 구조 정리 ===")
    if DST_SPIRIT.exists():
        shutil.rmtree(DST_SPIRIT)
        print(f"  삭제: {DST_SPIRIT}")
    if DST_ALCHEMY.exists():
        shutil.rmtree(DST_ALCHEMY)
        print(f"  삭제: {DST_ALCHEMY}")

    DST_SPIRIT.mkdir(parents=True, exist_ok=True)
    DST_ALCHEMY.mkdir(parents=True, exist_ok=True)

    # ── 정령 도감 ────────────────────────────────────────────────────────────
    print("\n=== 정령 도감 계열 파일 생성 ===")
    series_info = []

    for src_dir in sorted(SRC_SPIRIT.iterdir()):
        if not src_dir.is_dir():
            continue
        skey = series_key(src_dir.name)
        if skey not in SPIRIT_META:
            continue
        meta = SPIRIT_META[skey]
        fname, content = make_spirit_series_file(skey, meta, src_dir)
        (DST_SPIRIT / fname).write_text(content, encoding="utf-8")
        series_info.append((skey, meta, fname))
        print(f"  {meta['emoji']} {fname}")

    # Sort by series number
    series_info.sort(key=lambda x: int(x[0].split("-")[1]))

    # Continental files
    for src_fname, (out_fname, title) in CONTINENT_FILES.items():
        src = SRC_SPIRIT / src_fname
        if not src.exists():
            print(f"  [WARN] {src_fname} not found", file=sys.stderr)
            continue
        content = process_continent_file(src, title)
        (DST_SPIRIT / out_fname).write_text(content, encoding="utf-8")
        print(f"  대륙: {out_fname}")

    # Top index
    top_idx = make_spirit_index(series_info)
    (DST_SPIRIT / "index.md").write_text(top_idx, encoding="utf-8")
    print(f"  index.md")
    print(f"  → 총 {len(series_info)} 계열 파일 + 5 대륙 파일 + index.md")

    # ── 연금 도감 ────────────────────────────────────────────────────────────
    print("\n=== 연금 도감 분파 파일 생성 ===")
    branch_info = []

    for src_dir in sorted(SRC_ALCHEMY.iterdir()):
        if not src_dir.is_dir():
            continue
        bkey = series_key(src_dir.name)
        if bkey not in ALCHEMY_META:
            continue
        meta = ALCHEMY_META[bkey]
        fname, content = make_alchemy_branch_file(bkey, meta, src_dir)
        (DST_ALCHEMY / fname).write_text(content, encoding="utf-8")
        count = content.count("\n## ")
        branch_info.append((bkey, meta, fname, count))
        print(f"  {fname} ({count}연성식)")

    branch_info.sort(key=lambda x: int(x[0].split("-")[1]))

    # Top index
    alchemy_idx = make_alchemy_index(branch_info)
    (DST_ALCHEMY / "index.md").write_text(alchemy_idx, encoding="utf-8")
    print(f"  index.md")
    print(f"  → 총 {len(branch_info)} 분파 파일 + index.md")

    total = len(series_info) + 5 + 1 + len(branch_info) + 1
    print(f"\n완료: 정령 {len(series_info)+6} + 연금 {len(branch_info)+1} = {total}개 파일")


if __name__ == "__main__":
    run()
