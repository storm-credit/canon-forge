#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4개 대륙 (에테르·크림슨·프로스트·오벨리스크) 성지금단·중립지역·기타 파일 복원.
1차 캐논화 때 발생한 H3 서브섹션 소실 + 일부 내용 변조를 원본에서 재생성.

처리 규칙:
  [제거] YAML frontmatter
  [제거] [!CAUTION] 세력의 우주적 십자가 블록 + 이후 모든 줄
  [제거] [!NOTE] 에픽 섭리와 유구한 운명 블록 + 이후 모든 줄
  [제거] ### 섹션 헤더에 '에반 무영 라크라시스' 또는 '주인공 일행.../에반' 포함 → 섹션 전체
  [제거] 에반 무영 라크라시스 언급 단독 불릿 줄 (테이블 행 제외)
  [제거] 해시태그 줄 (#마법협회 등)
  [유지] 그 외 모든 내용
  [변환] 위키링크 [[A/B/C|D]] → D, [[A/B/C]] → C (마지막 세그먼트)
  [변환] H1 제목 → 한국어명만 (번호 제거)
"""
import os, re

BASE_SRC = "/tmp/tfs/THE FORGOTTEN SUMMONER/01. 아스트라리스 크로니클"
BASE_OUT = "/home/user/canon-forge/docs/canon/2-무대"

# 에반 보일러플레이트 탐지
EVAN_RE = re.compile(r"에반\s*무영\s*라크라시스|주인공 일행 \(Main Characters\)/에반")

BIG_BOILERPLATE_RE = re.compile(r"세력의 우주적 십자가|에픽 섭리와 유구한 운명")


# ── 공통 변환 함수 ────────────────────────────────────────────────────────────

def strip_frontmatter(text):
    if text.startswith("---"):
        m = re.match(r"^---\s*\n.*?\n---\s*\n", text, re.DOTALL)
        if m:
            return text[m.end():]
    return text


def strip_boilerplate_tail(text):
    """[!CAUTION]/[!NOTE] 에픽 섭리 블록부터 끝까지 제거."""
    lines = text.split("\n")
    cut = None
    for i, ln in enumerate(lines):
        if BIG_BOILERPLATE_RE.search(ln):
            # backtrack to opening line of callout block
            j = i
            while j > 0 and (lines[j-1].strip().startswith(">") or
                              lines[j-1].strip() == "" or
                              lines[j-1].strip() == "---"):
                j -= 1
            cut = j
            break
    if cut is not None:
        lines = lines[:cut]
    return "\n".join(lines)


def strip_evan_sections_and_bullets(text):
    """에반 명시 섹션(### 헤더 포함 섹션 전체) + 단독 불릿 제거."""
    lines = text.split("\n")
    result = []
    skip = False
    skip_level = None

    for ln in lines:
        stripped = ln.strip()

        # 헤더 감지
        m = re.match(r"^(#{2,6})\s", stripped)
        if m:
            level = len(m.group(1))
            if EVAN_RE.search(stripped):
                # 에반 명시 섹션 → 스킵 시작
                skip = True
                skip_level = level
                continue
            elif skip and level <= skip_level:
                # 같은 레벨 이상 헤더 도달 → 스킵 종료
                skip = False
                skip_level = None

        if skip:
            continue

        # 테이블 행이 아닌 단독 불릿에서 에반 무영 언급 → 제거
        if (EVAN_RE.search(ln) and
                not stripped.startswith("|") and
                not stripped.startswith("#")):
            continue

        result.append(ln)

    return "\n".join(result)


def strip_hashtag_lines(text):
    out = []
    for ln in text.split("\n"):
        s = ln.strip()
        if re.match(r"^#[^#\s]", s):
            continue
        out.append(ln)
    return "\n".join(out)


def clean_wikilinks(text):
    # [[A|B]] → B
    text = re.sub(r"\[\[[^\]\|]*\|([^\]]*)\]\]", r"\1", text)
    # [[A]] → last path segment
    def repl(m):
        inner = m.group(1)
        seg = inner.split("/")[-1].strip()
        return seg
    text = re.sub(r"\[\[([^\]]*)\]\]", repl, text)
    return text


def korean_name_from_path(fname):
    base = fname[:-3] if fname.endswith(".md") else fname
    # 앞의 번호 제거 (01-3-5-1. 등)
    base = re.sub(r"^[\d.\-]+\s*", "", base)
    # 뒤의 (English) 제거
    base = re.sub(r"\s*\(.*?\)\s*$", "", base).strip()
    return base


def fix_h1(text, korean_name):
    lines = text.split("\n")
    for i, ln in enumerate(lines):
        if ln.startswith("# "):
            lines[i] = "# " + korean_name
            break
    return "\n".join(lines)


def collapse_blanks(text):
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n"


def transform(src_path, korean_name):
    with open(src_path, encoding="utf-8", errors="replace") as f:
        text = f.read()
    text = strip_frontmatter(text)
    text = strip_boilerplate_tail(text)
    text = strip_evan_sections_and_bullets(text)
    text = strip_hashtag_lines(text)
    text = clean_wikilinks(text)
    text = fix_h1(text, korean_name)
    text = collapse_blanks(text)
    return text


def make_frontmatter(canon_id, name, entity_type, continent_kr, src_rel):
    return (f"---\n"
            f"canon_id: {canon_id}\n"
            f"정본명: {name}\n"
            f"유형: 지리 — {entity_type}\n"
            f"대륙: {continent_kr}\n"
            f'출처:\n  - "{src_rel}"\n'
            f"검증상태: Phase 2 무대 — 원본 전수 보존 + 청소 (2026-06-20)\n"
            f"---\n\n")


# ── 대륙 정의 ────────────────────────────────────────────────────────────────

CONTINENTS = [
    {
        "src_dir": "01-3. 생명의 숲 – 에테르 대륙 (Eter Continent)",
        "out_dir": "에테르대륙",
        "slug": "ether",
        "kr": "에테르 대륙",
        "sacred_dir": "01-3-5. 성지·금단 지역",
        "neutral_dir": "01-3-6. 중립 지역",
        "terrain_dir": "01-3-1. 지형",
        "climate": "01-3-2. 기후 & 생태 (Climate & Ecology).md",
        "history": "01-3-3. 역사 (History).md",
        "culture": "01-3-4. 문화 & 종교 (Culture & Religion).md",
        "magic": "01-3-7. 에테르 대륙 마법 생태계/0. 에테르 대륙 마법 생태계 및 자원 개요.md",
        "terrain_map": {
            "01-3-1-1. 동부 – 황금 곡창 지대 (Eastern Golden Fields).md": "동부-황금곡창.md",
            "01-3-1-2. 북부 – 산맥과 깊은 숲 (Northern Mountains).md": "북부-산맥숲.md",
            "01-3-1-3. 남부 – 호수와 언덕 지대 (Southern Lakes).md": "남부-호수언덕.md",
            "01-3-1-4. 서부 – 국경 요새 지대 (Western Border).md": "서부-국경요새.md",
            "01-3-1-5. 중앙 – 성역 벨트 (Central Sacred Belt).md": "중앙-성역벨트.md",
        },
    },
    {
        "src_dir": "01-4. 붉은 황무지 – 크림슨 대륙 (Crimson Continent)",
        "out_dir": "크림슨대륙",
        "slug": "crimson",
        "kr": "크림슨 대륙",
        "sacred_dir": "01-4-5. 성지·금단 지역",
        "neutral_dir": "01-4-6. 중립 지역",
        "terrain_dir": "01-4-1. 지형",
        "climate": "01-4-2. 기후 & 생태 (Climate & Ecology).md",
        "history": "01-4-3. 역사 (History).md",
        "culture": "01-4-4. 문화 & 종교 (Culture & Religion).md",
        "magic": "01-4-7. 크림슨 대륙 마법 생태계/0. 크림슨 대륙 마법 생태계 및 자원 개요.md",
        "terrain_map": {
            "01-4-1-1. 서부 – 제국의 허리 (Western Heartland).md": "서부-제국의허리.md",
            "01-4-1-2. 동부 – 붉은 폐허와 아르카나의 흔적 (Eastern Ruin Zone).md": "동부-붉은폐허.md",
            "01-4-1-3. 북부 – 바람과 잊혀진 서고의 땅 (Northern Winds).md": "북부-바람의서고.md",
            "01-4-1-4. 남부 – 붉은 황혼 사막과 유랑 부족 (Southern Crimson Sea).md": "남부-황혼사막.md",
        },
    },
    {
        "src_dir": "01-5. 얼음의 땅 – 프로스트 대륙 (Frost Continent)",
        "out_dir": "프로스트대륙",
        "slug": "frost",
        "kr": "프로스트 대륙",
        "sacred_dir": "01-5-5. 성지·금단 지역",
        "neutral_dir": "01-5-6. 중립 지역",
        "terrain_dir": "01-5-1. 지형",
        "climate": "01-5-2. 기후 & 생태 (Climate & Ecology).md",
        "history": "01-5-3. 역사 (History).md",
        "culture": "01-5-4. 문화 & 종교 (Culture & Religion).md",
        "magic": "01-5-7. 프로스트 대륙 마법 생태계/0. 프로스트 대륙 마법 생태계 및 자원 개요.md",
        "terrain_map": {
            "01-5-1-1. 중앙 – 강철산맥 (Stonecrest Mountains).md": "중앙-강철산맥.md",
            "01-5-1-2. 북부 – 혹한 설원 (Frozen Expanse).md": "북부-혹한설원.md",
            "01-5-1-3. 동부 – 빙하 지대 (Glacier Territory).md": "동부-빙하지대.md",
            "01-5-1-4. 남부 – 남부 산지 (Southern Highlands).md": "남부-남부산지.md",
            "01-5-1-5. 서부 – 난류 해역 (Maelstrom Coast).md": "서부-난류해역.md",
        },
    },
    {
        "src_dir": "01-6. 그림자의 대지 – 오벨리스크 대륙 (Obelisk Continent)",
        "out_dir": "오벨리스크대륙",
        "slug": "obelisk",
        "kr": "오벨리스크 대륙",
        "sacred_dir": "01-6-5. 성지·금단 지역",
        "neutral_dir": "01-6-6. 중립 지역",
        "terrain_dir": "01-6-1. 지형",
        "climate": "01-6-2. 기후 & 생태 (Climate & Ecology).md",
        "history": "01-6-3. 역사 (History).md",
        "culture": "01-6-4. 문화 & 종교 (Culture & Religion).md",
        "magic": "01-6-7. 오벨리스크 대륙 마법 생태계/0. 오벨리스크 대륙 마법 생태계 및 자원 개요.md",
        "terrain_map": {
            "01-6-1-1. 중앙 – 흑오벨리스크 황무지 (Black Obelisk Wastes).md": "중앙-흑오벨리스크황무지.md",
            "01-6-1-2. 동부 – 심연 균열 협곡 (Abyssal Canyons).md": "동부-심연균열협곡.md",
            "01-6-1-3. 서부 – 망자의 평원 (Plain of the Dead).md": "서부-망자의평원.md",
            "01-6-1-4. 북부 – 독기 안개 늪지 (Mistscour Swamps).md": "북부-독기안개늪지.md",
        },
    },
]

# 기존 캐논 파일에서 정본명 추출
def read_canon_name(canon_path):
    try:
        with open(canon_path, encoding="utf-8") as f:
            txt = f.read()
        m = re.search(r"^정본명:\s*(.+)$", txt, re.MULTILINE)
        if m:
            return m.group(1).strip()
    except FileNotFoundError:
        pass
    return None


# 기존 캐논 파일에서 frontmatter를 읽어 그대로 재사용하는 헬퍼
def read_existing_frontmatter(canon_path):
    """기존 캐논 파일의 --- ... --- frontmatter 추출."""
    try:
        with open(canon_path, encoding="utf-8") as f:
            txt = f.read()
        if txt.startswith("---"):
            m = re.match(r"^(---\s*\n.*?\n---\s*\n)", txt, re.DOTALL)
            if m:
                return m.group(1)
    except FileNotFoundError:
        pass
    return None


def is_index_file(fname, subdir_name):
    """인덱스/목록 파일인지 판단 (01-3-5. 지형.md 같은 서브디렉터리 이름 파일도 포함)."""
    stem = fname[:-3] if fname.endswith(".md") else fname
    # 번호 끝에 서브디렉터리와 같은 이름 (예: "01-3-5. 성지·금단 지역") → 인덱스
    if subdir_name and os.path.basename(subdir_name) in stem:
        return True
    # "0.", "00." 등으로 시작
    if re.match(r"^0+[.\-]", os.path.basename(fname)):
        return True
    # 디렉터리 자체와 같은 이름의 파일
    return False


created = []
updated = []

for cont in CONTINENTS:
    src_root = os.path.join(BASE_SRC, cont["src_dir"])
    out_root = os.path.join(BASE_OUT, cont["out_dir"])
    slug = cont["slug"]
    kr = cont["kr"]

    print(f"\n{'='*60}")
    print(f"대륙: {kr}")
    print(f"{'='*60}")

    # ── 1. 성지금단 엔티티 ────────────────────────────────────────────────────
    sacred_src = os.path.join(src_root, cont["sacred_dir"])
    sacred_out = os.path.join(out_root, "성지금단")
    if os.path.isdir(sacred_src):
        for fname in sorted(os.listdir(sacred_src)):
            if not fname.endswith(".md"):
                continue
            if is_index_file(fname, cont["sacred_dir"]):
                continue
            src_path = os.path.join(sacred_src, fname)
            kname = korean_name_from_path(fname)
            slug_name = kname.replace(" ", "-")
            out_path = os.path.join(sacred_out, slug_name + ".md")

            # 기존 frontmatter 재사용
            fm = read_existing_frontmatter(out_path)
            if fm is None:
                src_rel = cont["src_dir"] + "/" + cont["sacred_dir"] + "/" + fname
                fm = make_frontmatter(
                    f"stage.continent.{slug}.sacred_forbidden.{kname.replace(' ', '_')}",
                    kname, "성지·금단", kr, src_rel
                )

            body = transform(src_path, kname)
            os.makedirs(sacred_out, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(fm + body)
            print(f"  [성지금단] {kname}")
            updated.append(out_path)

    # ── 2. 중립지역 엔티티 ────────────────────────────────────────────────────
    neutral_src = os.path.join(src_root, cont["neutral_dir"])
    neutral_out = os.path.join(out_root, "중립지역")
    if os.path.isdir(neutral_src):
        for fname in sorted(os.listdir(neutral_src)):
            if not fname.endswith(".md"):
                continue
            if is_index_file(fname, cont["neutral_dir"]):
                continue
            src_path = os.path.join(neutral_src, fname)
            kname = korean_name_from_path(fname)
            slug_name = kname.replace(" ", "-")
            out_path = os.path.join(neutral_out, slug_name + ".md")

            fm = read_existing_frontmatter(out_path)
            if fm is None:
                src_rel = cont["src_dir"] + "/" + cont["neutral_dir"] + "/" + fname
                fm = make_frontmatter(
                    f"stage.continent.{slug}.neutral.{kname.replace(' ', '_')}",
                    kname, "중립 지역", kr, src_rel
                )

            body = transform(src_path, kname)
            os.makedirs(neutral_out, exist_ok=True)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(fm + body)
            print(f"  [중립지역] {kname}")
            updated.append(out_path)

    # ── 3. 지형 개별 권역 엔티티 (명시적 매핑 사용) ────────────────────────────
    terrain_src = os.path.join(src_root, cont["terrain_dir"])
    terrain_out = os.path.join(out_root, "지형")
    terrain_map = cont.get("terrain_map", {})
    if os.path.isdir(terrain_src) and terrain_map:
        for src_fname, canon_fname in terrain_map.items():
            src_path = os.path.join(terrain_src, src_fname)
            out_path = os.path.join(terrain_out, canon_fname)
            if not os.path.exists(src_path):
                print(f"  [지형권역] SKIP (원본 없음): {src_fname}")
                continue
            if not os.path.exists(out_path):
                print(f"  [지형권역] SKIP (캐논 없음): {canon_fname}")
                continue

            fm = read_existing_frontmatter(out_path)
            if fm is None:
                print(f"  [지형권역] SKIP (frontmatter 없음): {canon_fname}")
                continue

            # 기존 정본명을 H1 제목으로 사용
            kname = read_canon_name(out_path) or korean_name_from_path(src_fname)
            body = transform(src_path, kname)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(fm + body)
            print(f"  [지형권역] {canon_fname}")
            updated.append(out_path)

    # ── 4. 서사 파일 (기후생태·역사·문화종교·마법생태) ─────────────────────────
    NARRATIVE = [
        (cont["climate"],  "기후생태.md",  "기후 & 생태"),
        (cont["history"],  "역사.md",     "역사"),
        (cont["culture"],  "문화종교.md",  "문화 & 종교"),
        (cont["magic"],    "마법생태.md",  "마법 생태계"),
    ]
    for src_rel_part, out_fname, label in NARRATIVE:
        src_path = os.path.join(src_root, src_rel_part)
        out_path = os.path.join(out_root, out_fname)
        if not os.path.exists(src_path) or not os.path.exists(out_path):
            continue

        fm = read_existing_frontmatter(out_path)
        if fm is None:
            continue

        kname = f"{kr} {label}"
        body = transform(src_path, kname)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(fm + body)
        print(f"  [서사] {out_fname}")
        updated.append(out_path)

print(f"\n총 갱신 파일: {len(updated)}개")
for p in sorted(updated):
    print(" ", os.path.relpath(p, "/home/user/canon-forge/docs/canon/2-무대"))
