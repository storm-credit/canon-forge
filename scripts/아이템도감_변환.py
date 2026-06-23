#!/usr/bin/env python3
"""
W5 아이템 도감 전수 수렴기 (729파일 / 93폴더 / 5대 카테고리)
- 무기·방어구·악세서리·유물·헌터 특수 장비
- 폴더 구조 그대로 재귀 미러링, 1:1 정제
- 각 폴더에 index.md 생성, nav 스니펫 stdout 출력
- 아이템 특유 보일러플레이트 제거:
    · [!IMPORTANT] 7축 거시 엔진 연동 (Hanesis 메타)
    · [!NOTE] 에픽 섭리 + The Anchor (에반 개입 당위성)
    · ## [ 고전 명작 판타지의 섭리 (Classic Epic Providence) ] 후미 섹션
    · <!-- HERO_INJECT_ANCHOR -- 주석
"""
import re
import shutil
from pathlib import Path

BASE = Path("/tmp/tfs/THE FORGOTTEN SUMMONER/01. 아스트라리스 크로니클/01-19. 아이템 도감 (Item Encyclopedia)")
CANON = Path("/home/user/canon-forge/docs/canon/3-사물/아이템-도감")
TODAY = "2026-06-23"

TIER_KW = ["7조약", "7주계", "7기어", "7위계", "5계급", "7주신", "7단계"]

ROOT_TITLE = "아이템 도감 (Item Encyclopedia)"
ROOT_DESC = "아스트라리스 5대 아이템 계열 — 무기·방어구·악세서리·유물·헌터 특수 장비 전수 아카이브."
EMOJI = "🗡️"


def strip_frontmatter(text):
    if text.startswith("---"):
        end = text.find("\n---\n", 3)
        if end != -1:
            text = text[end + 5:]
    # 본문 중간/후미 중복 frontmatter 블록 제거 (병합 아이템: ---\ntags:/aliases:/type: ...---)
    text = re.sub(r"\n-{3,}\s*\n(?:tags|aliases|type):.*?\n-{3,}\s*(?=\n|$)",
                  "", text, flags=re.DOTALL)
    return text


def strip_boilerplate(text):
    # [!NOTE]/[!IMPORTANT]/[!CAUTION] 콜아웃 블록 전체 제거 (연속 > 줄)
    text = re.sub(r"> \[!(?:NOTE|IMPORTANT|CAUTION|WARNING|TIP|INFO)\].*?(?=\n\n(?!>)|\Z)",
                  "", text, flags=re.DOTALL)
    # 후미 '고전 명작 판타지의 섭리' 섹션 제거 (헤더부터 파일 끝/다음 h2까지)
    text = re.sub(r"\n*---\s*\n##\s*\[\s*고전 명작 판타지의 섭리.*?(?=\n##\s|\Z)",
                  "", text, flags=re.DOTALL)
    # 잔존 단독 '고전 명작 판타지의 섭리' 헤더 (--- 없는 변종)
    text = re.sub(r"\n*##\s*\[\s*고전 명작 판타지의 섭리.*?(?=\n##\s|\Z)",
                  "", text, flags=re.DOTALL)
    # HERO_INJECT_ANCHOR 주석
    text = re.sub(r"<!--\s*HERO_INJECT_ANCHOR\s*--+>?", "", text)
    return text


def fix_roamlinks(text):
    def _sub(m):
        inner = m.group(1).split("|")[0]
        parts = [p.strip() for p in re.split(r"[/\\]", inner) if p.strip()]
        last = parts[-1] if parts else inner
        last = re.sub(r"^\d+(-\d+)*\.\s*", "", last)       # 선두 번호 제거
        last = re.sub(r"^[A-Z]-\d+(-\d+)*\.\s*", "", last)  # W-HW-01. 류
        last = re.sub(r"^\[[^\]]*\]\s*", "", last)          # [히든] 등
        return last.strip()
    # 중첩 대괄호 허용 (non-greedy)
    return re.sub(r"\[\[(.+?)\]\]", _sub, text)


def collapse_tiers(text):
    for kw in TIER_KW:
        text = re.sub(rf"\[(\d+){kw}", rf"[\1{kw[1:]}", text)
    return text


def flatten_md_links(text):
    text = re.sub(r"\[([^\]]+)\]\(<[^>]*\.md>\)", r"\1", text)                 # ](<...md>)
    text = re.sub(r"\[([^\]]+)\]\((?:[^()]|\([^()]*\))*?\.md\)", r"\1", text)  # ](...md)
    return text


def clean_body(text):
    text = strip_frontmatter(text)
    text = strip_boilerplate(text)
    text = fix_roamlinks(text)
    text = collapse_tiers(text)
    text = flatten_md_links(text)
    text = re.sub(r"^#\s[^\n]*\n", "", text, flags=re.MULTILINE)   # 모든 h1 제거
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def strip_prefix(s):
    return re.sub(r"^[A-Z0-9]+(?:-[A-Z0-9]+)*(?:-\d+)*\.\s*", "", s).strip()


def title_from_name(name):
    t = name[:-3] if name.endswith(".md") else name
    t = strip_prefix(t) or t
    # 묶음 파일명 중간 번호("엘리시온  124. 루멘 블레이드") → " / " 구분
    t = re.sub(r"\s+\d+\.\s+", " / ", t)
    t = re.sub(r"\s{2,}", " ", t).strip()
    return t


def compact(name, is_dir=False):
    stem = name if is_dir else (name[:-3] if name.endswith(".md") else name)
    m = re.match(r"^([A-Z0-9]+(?:-[A-Z0-9]+)*(?:-\d+)*)\.\s*(.+)$", stem)
    num = m.group(1) if m else ""
    rest = m.group(2) if m else stem
    rest = re.sub(r"\[[^\]]*\]", "", rest)
    rest = re.sub(r"\([^)]*\)", "", rest)
    rest = re.sub(r"\s+\d+\.\s+", " ", rest)   # 묶음 중간 번호 제거
    rest = re.sub(r"[&·,/«»'\"]", "", rest)
    rest = re.sub(r"\s+", "", rest).strip("-")
    base = f"{num}.{rest}" if num else rest
    base = base or "항목"
    return base if is_dir else base + ".md"


def esc_md(s):
    return s.replace("[", "\\[").replace("]", "\\]")


def sortkey(p):
    m = re.match(r"^([A-Z]*)(\d+)(?:-(\d+))?(?:-(\d+))?", p.name)
    if m:
        alpha = m.group(1) or ""
        nums = tuple(int(g) for g in m.groups()[1:] if g)
        return (0, alpha, nums, p.name)
    return (1, "", (), p.name)


# title→compact 디렉토리 룩업 (nav emit용)
compact_dir_lookup = {}


def process_dir(src_dir, dst_dir, rel_label, is_root, root_title):
    dst_dir.mkdir(parents=True, exist_ok=True)
    child_files = []   # (out_name, title)
    child_dirs = []    # (dir_compact, title)
    nav = []

    seen_files = set()
    for entry in sorted(src_dir.iterdir(), key=sortkey):
        if entry.is_dir():
            dcompact = compact(entry.name, is_dir=True)
            dtitle = title_from_name(entry.name)
            sub_nav = process_dir(entry, dst_dir / dcompact,
                                  f"{rel_label}/{entry.name}", False, dtitle)
            child_dirs.append((dcompact, dtitle))
            nav.append((dtitle, dcompact, sub_nav, True))
        elif entry.suffix == ".md":
            # 메타 placeholder 템플릿 제외 ('(개연성 심화 구조)' 등)
            if entry.name.startswith("("):
                continue
            # 카테고리 자기명 분류표(폴더명.md)도 본문으로 보존
            title = title_from_name(entry.name)
            body = clean_body(entry.read_text(encoding="utf-8"))
            if not body:
                continue
            out_name = compact(entry.name)
            # 충돌 방지
            base_out = out_name
            n = 2
            while out_name in seen_files:
                out_name = base_out[:-3] + f"_{n}.md"
                n += 1
            seen_files.add(out_name)
            content = "\n".join([
                "---",
                f"정본명: {title}",
                f"유형: {ROOT_TITLE} 항목",
                f'출처: "{rel_label}/{entry.name}"',
                f"검증상태: Phase 3 전수 보존 (원문 보존, {TODAY})",
                "---", "",
                f"# {EMOJI} {title}", "",
                body,
            ])
            (dst_dir / out_name).write_text(content, encoding="utf-8")
            child_files.append((out_name, title))
            nav.append((title, out_name, None, False))

    # index.md
    lines = [
        "---",
        f"정본명: {root_title}",
        "유형: 도감 인덱스",
        f'출처: "{rel_label}"',
        f"검증상태: Phase 3 전수 보존 (원문 보존, {TODAY})",
        "---", "",
        f"# {EMOJI} {root_title}", "",
    ]
    if is_root:
        lines += [f"> {ROOT_DESC}", ""]
    if child_dirs:
        lines += ["## 하위 분류", "", "| 분류 | 링크 |", "|------|------|"]
        for dc, dt in child_dirs:
            lines.append(f"| {esc_md(dt)} | [{esc_md(dt)}]({dc}/index.md) |")
        lines.append("")
    if child_files:
        lines += ["## 항목", "", "| # | 항목 |", "|---|------|"]
        for i, (fn, t) in enumerate(child_files, 1):
            lines.append(f"| {i} | [{esc_md(t)}]({fn}) |")
    (dst_dir / "index.md").write_text("\n".join(lines), encoding="utf-8")
    return nav


def emit_nav(nav, indent):
    pad = " " * indent
    base = "3-사물/아이템-도감"
    out = [f"{pad}- {ROOT_TITLE.split(' (')[0]}:"]
    out.append(f"{pad}    - 전체 인덱스: {base}/index.md")

    def walk(items, prefix_path, lvl):
        p = " " * (indent + 4 * lvl)
        for title, dc, payload, is_dir in items:
            if is_dir:
                out.append(f"{p}- {esc_md(title)}:")
                out.append(f"{p}    - 전체 인덱스: {base}/{prefix_path}{dc}/index.md")
                walk(payload, f"{prefix_path}{dc}/", lvl + 1)
            else:
                short = re.sub(r"\s*\([^)]*\)\s*$", "", title).strip() or title
                out.append(f"{p}- {esc_md(short)}: {base}/{prefix_path}{dc}")
    walk(nav, "", 1)
    return "\n".join(out)


def run():
    if CANON.exists():
        shutil.rmtree(CANON)
    # 디렉토리 룩업 사전 구축
    for entry in BASE.rglob("*"):
        if entry.is_dir():
            compact_dir_lookup[title_from_name(entry.name)] = compact(entry.name, is_dir=True)
    nav = process_dir(BASE, CANON, "01-19. 아이템 도감 (Item Encyclopedia)", True, ROOT_TITLE)
    nfiles = len(list(CANON.rglob("*.md")))
    print(f"  {EMOJI} {CANON}: {nfiles} md")
    print("\n========== NAV SNIPPET ==========")
    snippet = emit_nav(nav, 6)
    Path("/tmp/claude-0/-home-user-canon-forge/d347be76-2595-51e7-877d-cd2d97c4518a/scratchpad/item_nav.yml").write_text(snippet, encoding="utf-8")
    print(snippet[:2000])
    print(f"\n... (full nav written to scratchpad/item_nav.yml, {len(snippet.splitlines())} lines)")


if __name__ == "__main__":
    run()
