#!/usr/bin/env python3
"""
도감 재구조화 스크립트
정령 도감(20계열×10) + 연금 도감(10분파×20) → 개별 파일 + 폴더 구조
"""
import re
import sys
from pathlib import Path
from collections import defaultdict

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


# ── Cleaning helpers ─────────────────────────────────────────────────────────

def strip_frontmatter(text: str) -> str:
    if text.startswith("---"):
        end = text.find("\n---\n", 3)
        if end != -1:
            return text[end + 5:]
    return text


def strip_boilerplate(text: str) -> str:
    return re.sub(r"> \[!NOTE\].*?(?=\n\n(?!>)|\Z)", "", text, flags=re.DOTALL)


def fix_roamlinks(text: str, strip_en_suffix: bool = False) -> str:
    def _sub(m):
        inner = m.group(1)
        parts = [p.strip() for p in re.split(r"[/\\]", inner) if p.strip()]
        last = parts[-1] if parts else inner
        last = re.sub(r"^\[.*?\]\s*", "", last)
        if strip_en_suffix:
            last = re.sub(r"\s*\([A-Za-z\s'\-]+\)\s*$", "", last)
        return last.strip()
    return re.sub(r"\[\[([^\]|]+?)(?:\|[^\]]+)?\]\]", _sub, text)


def clean_body(text: str) -> str:
    text = strip_frontmatter(text)
    text = strip_boilerplate(text)
    text = fix_roamlinks(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_sections(text: str):
    spec_m = re.search(r"### 세부 명세\s*\n(.*?)(?=###|\Z)", text, re.DOTALL)
    desc_m = re.search(r"### 권능 및 묘사\s*\n(.*?)(?=###|\Z)", text, re.DOTALL)
    spec = spec_m.group(1).strip() if spec_m else ""
    desc = desc_m.group(1).strip() if desc_m else ""
    return spec, desc


def safe_fname(name: str) -> str:
    name = name.strip().replace(" ", "")
    name = re.sub(r"[^\w가-힣ㄱ-ㅎㅏ-ㅣ]", "", name)
    return name


def series_key(folder_name: str) -> str:
    m = re.match(r"(6-\d+)\.", folder_name)
    return m.group(1) if m else None


# ── Spirit parsing ────────────────────────────────────────────────────────────

SPIRIT_GRADE_MAP = {
    "정령왕": "정령왕",
    "상급": "상급(대정령)",
    "중급": "중급",
    "하급": "하급",
}


def parse_spirit_h1(h1: str):
    """Returns (grade, name_kr, name_en, subtitle)."""
    line = h1.lstrip("# ").strip()

    grade_m = re.match(r"\[([^\]]+)\]\s*", line)
    if not grade_m:
        return "미확인", line, "", ""
    grade_raw = grade_m.group(1).strip()
    grade = SPIRIT_GRADE_MAP.get(grade_raw, grade_raw)
    rest = line[grade_m.end():]

    # Strip roamlinks (also remove English suffix inside roamlink so we get only Korean)
    rest = fix_roamlinks(rest, strip_en_suffix=True)
    rest = rest.strip()

    # Pattern: 이름 (English - 부제목) or 이름 (English)
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
        name_kr = rest
        name_en = ""
        subtitle = ""

    return grade, name_kr, name_en, subtitle


def process_spirit_file(src: Path, skey: str, meta: dict):
    """Returns (out_fname, content, (grade, name_kr, name_en, subtitle))."""
    text = src.read_text(encoding="utf-8")

    h1_m = re.search(r"^# .+$", text, re.MULTILINE)
    if not h1_m:
        print(f"  [WARN] no H1 in {src.name}", file=sys.stderr)
        return None, None, None

    grade, name_kr, name_en, subtitle = parse_spirit_h1(h1_m.group(0))
    body = clean_body(text)
    _spec, desc = extract_sections(body)

    out_fname = safe_fname(name_kr) + ".md"
    if not out_fname or out_fname == ".md":
        out_fname = safe_fname(name_en) + ".md"

    grade_disp = GRADE_DISPLAY.get(grade, grade)
    h1_line = f"# {name_kr} ({name_en})" if name_en else f"# {name_kr}"
    if subtitle:
        h1_line += f" — {subtitle}"

    # Skadi 동명이물 note
    skadi_note = ""
    if name_kr == "스카디" and skey == "6-4":
        skadi_note = (
            "\n\n> **⚠️ 동명이물 주의** — 이 스카디는 **빙하 원소의 정령왕**이다. "
            "프로스트본 연합 대족장 **스카디 아이스블러드(인간 영웅)**와 이름만 같은 별개 존재. "
            "→ 정령 속성은 본 파일이 정본, 인간 영웅 속성은 [[영웅-인덱스]] §G가 정본."
        )

    sko, sen = meta['ko'], meta['en']
    spirit_src = f'출처: "01-32. 정령 백과/6. 정령 도감/{skey}. {sko} 정령 ({sen})"'
    lines = [
        "---",
        f"canon_id: system.spirit.{skey.replace('-','')}.{safe_fname(name_en).lower() or safe_fname(name_kr).lower()}",
        f"정본명: {name_kr} ({name_en})" if name_en else f"정본명: {name_kr}",
        "유형: 정령",
        f"계열: {sko} ({sen})",
        f"등급: {grade}",
        spirit_src,
        f"검증상태: Phase 2 전수 보존 (원문 보존, {TODAY})",
        "---",
        "",
        h1_line,
        "",
        f"**등급**: {grade_disp} · **계열**: {meta['emoji']} {meta['ko']} · **극점**: {meta['pole']}" + skadi_note,
        "",
        "## 권능 및 묘사",
        "",
        desc if desc else "⚠️미표기",
    ]
    return out_fname, "\n".join(lines), (grade, name_kr, name_en, subtitle)


# ── Continental spirit files ──────────────────────────────────────────────────

CONTINENT_FILES = {
    "6-1. 에테르 정령 (Aether Spirits).md":    ("에테르정령", "에테르 대륙 정령 (Aether Spirits)"),
    "6-2. 크림슨 정령 (Crimson Spirits).md":   ("크림슨정령", "크림슨 대륙 정령 (Crimson Spirits)"),
    "6-3. 프로스트 정령 (Frost Spirits).md":   ("프로스트정령","프로스트 대륙 정령 (Frost Spirits)"),
    "6-4. 오벨리스크 정령 (Obelisk Spirits).md":("오벨리스크정령","오벨리스크 대륙 정령 (Obelisk Spirits)"),
    "6-5. 해양 정령 (Oceanic Spirits).md":     ("해양정령", "해양 대륙 정령 (Oceanic Spirits)"),
}


def process_continent_file(src: Path, out_fname: str, title: str):
    text = src.read_text(encoding="utf-8")
    body = clean_body(text)
    # Remove the H1 from body (we'll add our own)
    body = re.sub(r"^# .+\n", "", body, count=1).strip()

    lines = [
        "---",
        f"canon_id: system.spirit.continental.{safe_fname(out_fname).lower()}",
        f"정본명: {title}",
        "유형: 대륙 정령 도감",
        f'출처: "01-32. 정령 백과/6. 정령 도감/{src.name}"',
        f"검증상태: Phase 2 전수 보존 (원문 보존, {TODAY})",
        "---",
        "",
        f"# {title}",
        "",
        body,
    ]
    return "\n".join(lines)


# ── Alchemy parsing ───────────────────────────────────────────────────────────

def parse_alchemy_h1(h1: str):
    """Returns (level_prefix, name_kr, name_en)."""
    line = h1.lstrip("# ").strip()
    # Strip roamlinks (keeping Korean, removing English suffix)
    line = fix_roamlinks(line, strip_en_suffix=True)
    line = line.strip()

    # Pattern: [level_prefix: name_kr] (name_en)
    m = re.match(r"\[([^\]:]+)(?::\s*(.+?))?\]\s*\((.+?)\)\s*$", line)
    if m:
        level_prefix = m.group(1).strip()
        name_kr = (m.group(2) or "").strip()
        name_en = m.group(3).strip()
        return level_prefix, name_kr, name_en
    return line, "", ""


def process_alchemy_file(src: Path, bkey: str, meta: dict):
    """Returns (out_fname, content, (level_prefix, name_kr, name_en))."""
    text = src.read_text(encoding="utf-8")

    h1_m = re.search(r"^# .+$", text, re.MULTILINE)
    if not h1_m:
        print(f"  [WARN] no H1 in {src.name}", file=sys.stderr)
        return None, None, None

    level_prefix, name_kr, name_en = parse_alchemy_h1(h1_m.group(0))
    body = clean_body(text)
    spec, desc = extract_sections(body)

    # Level number
    level_m = re.match(r"(\d+)", level_prefix)
    level_num = level_m.group(1) if level_m else "?"
    is_truth = "진리의 연성" in level_prefix or "단계" in level_prefix

    display_prefix = f"{level_num}단계 진리" if is_truth else f"{level_num}연성식"

    out_fname = safe_fname(name_kr) + ".md" if name_kr else safe_fname(name_en) + ".md"
    h1_line = f"# {display_prefix} — {name_kr} ({name_en})" if name_kr else f"# {display_prefix} ({name_en})"

    canon_slug = safe_fname(name_kr).lower() or safe_fname(name_en).lower()

    ako, aen = meta['ko'], meta['en']
    alchemy_src = f'출처: "01-34. 연금 백과/연금 도감/{bkey}. {ako} ({aen})"'
    sections = [
        "---",
        f"canon_id: system.alchemy.{safe_fname(ako).lower()}.{canon_slug}",
        f"정본명: {display_prefix} — {name_kr}" if name_kr else f"정본명: {display_prefix}",
        "유형: 연성식",
        f"분파: {ako} ({aen})",
        f"등급: {level_num}단계",
        alchemy_src,
        f"검증상태: Phase 2 전수 보존 (원문 보존, {TODAY})",
        "---",
        "",
        h1_line,
        "",
        f"**분파**: {meta['ko']} · **등급**: {level_num}단계",
    ]

    if spec:
        sections += ["", "## 세부 명세", "", spec]

    sections += ["", "## 권능 및 묘사", "", desc if desc else "⚠️미표기"]

    return out_fname, "\n".join(sections), (level_prefix, name_kr, name_en)


# ── Index generators ──────────────────────────────────────────────────────────

def make_spirit_series_index(skey: str, meta: dict, spirits: list) -> str:
    """spirits: list of (grade, name_kr, name_en, subtitle, fname)"""
    spirits_sorted = sorted(spirits, key=lambda x: (GRADE_ORDER.get(x[0], 99), x[1]))

    rows = []
    for grade, name_kr, name_en, subtitle, fname in spirits_sorted:
        disp = GRADE_DISPLAY.get(grade, grade)
        sub = f" — {subtitle}" if subtitle else ""
        rows.append(f"| {disp} | [{name_kr}]({fname}) | {name_en}{sub} |")

    iko, ien = meta['ko'], meta['en']
    idx_src = f'출처: "01-32. 정령 백과/6. 정령 도감/{skey}. {iko} 정령 ({ien})"'
    lines = [
        "---",
        f"canon_id: system.spirit.{skey.replace('-','')}.index",
        f"정본명: {iko} 정령 ({ien} Spirits)",
        "유형: 계열 인덱스",
        idx_src,
        f"검증상태: Phase 2 전수 보존 (원문 보존, {TODAY})",
        "---",
        "",
        f"# {meta['emoji']} {meta['ko']} 정령 ({meta['en']} Spirits)",
        "",
        f"**정령왕**: {meta['king']} · **극점**: {meta['pole']}",
        "",
        "| 등급 | 이름 | 영문·부제 |",
        "|------|------|----------|",
        *rows,
    ]
    return "\n".join(lines)


def make_alchemy_branch_index(bkey: str, meta: dict, formulas: list) -> str:
    """formulas: list of (level_prefix, name_kr, name_en, fname)"""
    formulas_sorted = sorted(formulas, key=lambda x: (int(re.search(r"\d+", x[0]).group(0)) if re.search(r"\d+", x[0]) else 99, x[1]))

    rows = []
    for level_prefix, name_kr, name_en, fname in formulas_sorted:
        level_m = re.match(r"(\d+)", level_prefix)
        lvl = level_m.group(1) if level_m else "?"
        is_truth = "진리" in level_prefix
        disp_level = f"{lvl}단계 진리" if is_truth else f"{lvl}연성식"
        rows.append(f"| {disp_level} | [{name_kr}]({fname}) | {name_en} |")

    bko, ben = meta['ko'], meta['en']
    bidx_src = f'출처: "01-34. 연금 백과/연금 도감/{bkey}. {bko} ({ben})"'
    lines = [
        "---",
        f"canon_id: system.alchemy.{safe_fname(bko).lower()}.index",
        f"정본명: {bko} ({ben})",
        "유형: 분파 인덱스",
        bidx_src,
        f"검증상태: Phase 2 전수 보존 (원문 보존, {TODAY})",
        "---",
        "",
        f"# {meta['ko']} ({meta['en']})",
        "",
        f"총 {len(formulas)}종 연성식",
        "",
        "| 단계 | 이름 | 영문명 |",
        "|------|------|--------|",
        *rows,
    ]
    return "\n".join(lines)


def make_spirit_top_index(series_data: dict) -> str:
    """series_data: {skey: (meta, [(grade, name_kr, name_en, subtitle, fname)])}"""
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
        "> [[정령체계]]의 부속 인덱스. 체계(공명 단계·계약·정령 전쟁 등)는 [[정령체계]] 본문이 정본.",
        "",
        "> **⚠️ 동명이물 — 스카디**: 빙하계 **정령왕 스카디**(Skadi)는 정령 존재. "
        "**스카디 아이스블러드**(인간 영웅, 프로스트본 연합 대족장)와 이름만 같은 별개 존재. "
        "→ 정령 속성: [[6-4.빙하계/스카디]] 정본 / 인간 영웅: [[영웅-인덱스]] §G 정본.",
        "",
        "## A. 20계열 200정령",
        "",
        "| # | 계열 | 정령왕 | 극점 |",
        "|---|------|--------|------|",
    ]

    for i, skey in enumerate(sorted(series_data.keys(), key=lambda k: int(k.split("-")[1])), 1):
        meta, spirits = series_data[skey]
        folder = f"{skey}.{meta['ko']}"
        lines.append(f"| {i} | {meta['emoji']} [{meta['ko']} ({meta['en']})]({folder}/index.md) | {meta['king']} | {meta['pole']} |")

    lines += [
        "",
        "## B. 5대륙 대표 정령",
        "",
        "| 대륙 | 링크 |",
        "|------|------|",
        "| 에테르 대륙 | [에테르 정령](대륙정령/에테르정령.md) |",
        "| 크림슨 대륙 | [크림슨 정령](대륙정령/크림슨정령.md) |",
        "| 프로스트 대륙 | [프로스트 정령](대륙정령/프로스트정령.md) |",
        "| 오벨리스크 대륙 | [오벨리스크 정령](대륙정령/오벨리스크정령.md) |",
        "| 해양 | [해양 정령](대륙정령/해양정령.md) |",
    ]
    return "\n".join(lines)


def make_alchemy_top_index(branch_data: dict) -> str:
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
        "> [[연금체계]]의 부속 인덱스. 연성 7진리·공정·계급 체계는 [[연금체계]] 본문이 정본.",
        "",
        "| # | 분파 | 연성식 수 |",
        "|---|------|----------|",
    ]

    for i, bkey in enumerate(sorted(branch_data.keys(), key=lambda k: int(k.split("-")[1])), 1):
        meta, formulas = branch_data[bkey]
        folder = f"{bkey}.{meta['ko']}"
        lines.append(f"| {i} | [{meta['ko']} ({meta['en']})]({folder}/index.md) | {len(formulas)} |")

    return "\n".join(lines)


# ── Main ─────────────────────────────────────────────────────────────────────

def run():
    total_spirit = 0
    total_alchemy = 0
    errors = []

    # ── 정령 도감 처리 ──────────────────────────────────────────────────────

    print("=== 정령 도감 처리 ===")
    series_data = {}  # {skey: (meta, [spirits])}

    for src_dir in sorted(SRC_SPIRIT.iterdir()):
        if not src_dir.is_dir():
            continue
        skey = series_key(src_dir.name)
        if skey not in SPIRIT_META:
            print(f"  [SKIP dir] {src_dir.name}")
            continue

        meta = SPIRIT_META[skey]
        folder_ko = f"{skey}.{meta['ko']}"
        dst_dir = DST_SPIRIT / folder_ko
        dst_dir.mkdir(parents=True, exist_ok=True)

        spirits_in_series = []

        for src_file in sorted(src_dir.iterdir()):
            if src_file.suffix != ".md":
                continue
            fname, content, info = process_spirit_file(src_file, skey, meta)
            if fname is None:
                errors.append(src_file)
                continue
            grade, name_kr, name_en, subtitle = info
            out_path = dst_dir / fname
            out_path.write_text(content, encoding="utf-8")
            spirits_in_series.append((grade, name_kr, name_en, subtitle, fname))
            total_spirit += 1

        # Series index
        idx_content = make_spirit_series_index(skey, meta, spirits_in_series)
        (dst_dir / "index.md").write_text(idx_content, encoding="utf-8")
        series_data[skey] = (meta, spirits_in_series)
        print(f"  {meta['emoji']} {skey}.{meta['ko']}: {len(spirits_in_series)} 정령")

    # Continental spirit files
    continent_dir = DST_SPIRIT / "대륙정령"
    continent_dir.mkdir(parents=True, exist_ok=True)

    for src_fname, (out_base, title) in CONTINENT_FILES.items():
        src_file = SRC_SPIRIT / src_fname
        if not src_file.exists():
            print(f"  [WARN] not found: {src_file}", file=sys.stderr)
            continue
        content = process_continent_file(src_file, out_base, title)
        (continent_dir / f"{out_base}.md").write_text(content, encoding="utf-8")
        print(f"  대륙정령: {out_base}.md")

    # Top-level spirit index
    top_idx = make_spirit_top_index(series_data)
    (DST_SPIRIT / "index.md").write_text(top_idx, encoding="utf-8")

    print(f"\n  정령 총계: {total_spirit}개 파일")

    # ── 연금 도감 처리 ──────────────────────────────────────────────────────

    print("\n=== 연금 도감 처리 ===")
    branch_data = {}

    for src_dir in sorted(SRC_ALCHEMY.iterdir()):
        if not src_dir.is_dir():
            continue
        bkey = series_key(src_dir.name)
        if bkey not in ALCHEMY_META:
            print(f"  [SKIP dir] {src_dir.name}")
            continue

        meta = ALCHEMY_META[bkey]
        folder_ko = f"{bkey}.{meta['ko']}"
        dst_dir = DST_ALCHEMY / folder_ko
        dst_dir.mkdir(parents=True, exist_ok=True)

        formulas_in_branch = []
        seen_fnames: dict[str, int] = {}

        for src_file in sorted(src_dir.iterdir()):
            if src_file.suffix != ".md":
                continue
            fname, content, info = process_alchemy_file(src_file, bkey, meta)
            if fname is None:
                errors.append(src_file)
                continue

            # Deduplicate filenames
            if fname in seen_fnames:
                seen_fnames[fname] += 1
                base = fname[:-3]
                fname = f"{base}_{seen_fnames[fname]}.md"
            else:
                seen_fnames[fname] = 0

            level_prefix, name_kr, name_en = info
            out_path = dst_dir / fname
            out_path.write_text(content, encoding="utf-8")
            formulas_in_branch.append((level_prefix, name_kr, name_en, fname))
            total_alchemy += 1

        # Branch index
        idx_content = make_alchemy_branch_index(bkey, meta, formulas_in_branch)
        (dst_dir / "index.md").write_text(idx_content, encoding="utf-8")
        branch_data[bkey] = (meta, formulas_in_branch)
        print(f"  {bkey}.{meta['ko']}: {len(formulas_in_branch)} 연성식")

    # Top-level alchemy index
    alchemy_top = make_alchemy_top_index(branch_data)
    (DST_ALCHEMY / "index.md").write_text(alchemy_top, encoding="utf-8")

    print(f"\n  연금 총계: {total_alchemy}개 파일")

    if errors:
        print(f"\n  [ERRORS] {len(errors)}건:")
        for e in errors:
            print(f"    {e}")
    else:
        print("\n  오류 없음")

    print(f"\n완료: 정령 {total_spirit} + 연금 {total_alchemy} = {total_spirit+total_alchemy}개 파일 생성")


if __name__ == "__main__":
    run()
