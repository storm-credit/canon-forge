#!/usr/bin/env python3
"""
소형 백과 전체 수렴기 (Batch B — 체계.md 없음)
- 동반수·마도통신·차원공간·마도교통·몬스터
- 서사 챕터 + 도감을 폴더 구조 그대로 재귀 미러링, 1:1 정제
- 각 폴더에 index.md 생성, nav 스니펫 stdout 출력
"""
import re
import shutil
import sys
from pathlib import Path

BASE = Path("/tmp/tfs/THE FORGOTTEN SUMMONER/01. 아스트라리스 크로니클")
CANON = Path("/home/user/canon-forge/docs/canon")
TODAY = "2026-06-22"

TIER_KW = ["7조약", "7주계", "7기어", "7위계", "5계급", "7주신", "7단계"]

CONFIGS = [
    {"key": "companion", "src": "01-38. 동반수 백과", "dst": "1-시스템/동반수-백과",
     "title": "동반수 백과 (Companions & War Mounts)", "emoji": "🐺",
     "desc": "야성과 유대로 맺어지는 군마·동반수 체계. 조련사 5계급, 13대 전술 동반수 계열."},
    {"key": "comms", "src": "01-40. 마도 통신 백과", "dst": "1-시스템/마도통신-백과",
     "title": "마도 통신 백과 (Arcane Communications)", "emoji": "📡",
     "desc": "마석 중계망·지맥 공명·텔레파시로 대륙을 잇는 통신 체계."},
    {"key": "dimension", "src": "01-42. 차원 및 공간 마법 백과", "dst": "1-시스템/차원공간-백과",
     "title": "차원 및 공간 마법 백과 (Dimensional & Spatial Magic)", "emoji": "🌀",
     "desc": "텔레포트·차원 균열·공간 통제의 본질과 금지된 연구. 마법체계 차원 마법의 심화 정본."},
    {"key": "transport", "src": "01-41. 마도 교통 백과", "dst": "2-무대/마도교통-백과",
     "title": "마도 교통 백과 (Arcane Transport)", "emoji": "🚂",
     "desc": "대륙 간 육상·해상·공중·차원 교통망과 교통 패권 전쟁."},
    {"key": "monster", "src": "01-39. 몬스터 백과", "dst": "2-무대/몬스터-도감",
     "title": "몬스터 도감 (Bestiary)", "emoji": "🐉",
     "desc": "5대륙 + 공통·특수 마수 생태 아카이브. 대륙별 서식종 종합 DB."},
]


def strip_frontmatter(text):
    if text.startswith("---"):
        end = text.find("\n---\n", 3)
        if end != -1:
            return text[end + 5:]
    return text


def strip_boilerplate(text):
    return re.sub(r"> \[!NOTE\].*?(?=\n\n(?!>)|\Z)", "", text, flags=re.DOTALL)


def fix_roamlinks(text):
    def _sub(m):
        inner = m.group(1).split("|")[0]
        parts = [p.strip() for p in re.split(r"[/\\]", inner) if p.strip()]
        last = parts[-1] if parts else inner
        last = re.sub(r"^\d+(-\d+)*\.\s*", "", last)
        last = re.sub(r"^\[[^\]]*\]\s*", "", last)
        return last.strip()
    return re.sub(r"\[\[(.+?)\]\]", _sub, text)


def collapse_tiers(text):
    for kw in TIER_KW:
        text = re.sub(rf"\[(\d+){kw}", rf"[\1{kw[1:]}", text)
    return text


def flatten_md_links(text):
    # 원본 파일명 기반 상대 .md 링크 → 텍스트만 보존 (index.md가 항법 대체)
    text = re.sub(r"\[([^\]]+)\]\(<[^>]*\.md>\)", r"\1", text)              # ](<...md>)
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
    return re.sub(r"^[A-Z0-9]+(?:-\d+)*\.\s*", "", s).strip()


def title_from_name(name):
    t = name[:-3] if name.endswith(".md") else name
    return strip_prefix(t) or t


def compact(name, is_dir=False):
    stem = name if is_dir else (name[:-3] if name.endswith(".md") else name)
    m = re.match(r"^([A-Z0-9]+(?:-\d+)*)\.\s*(.+)$", stem)
    num = m.group(1) if m else ""
    rest = m.group(2) if m else stem
    rest = re.sub(r"\[[^\]]*\]", "", rest)
    rest = re.sub(r"\([^)]*\)", "", rest)
    rest = re.sub(r"[&·,/]", "", rest)
    rest = re.sub(r"\s+", "", rest).strip("-")
    base = f"{num}.{rest}" if num else rest
    return base if is_dir else base + ".md"


def esc_md(s):
    return s.replace("[", "\\[").replace("]", "\\]")


def process_dir(src_dir, dst_dir, cfg, rel_label, is_root, root_title):
    """재귀: src_dir → dst_dir, 각 폴더 index 생성. returns nav list (yaml lines)."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    child_files = []   # (out_name, title)
    child_dirs = []    # (dir_compact, title, nav_sublist)
    nav = []

    entries = sorted(src_dir.iterdir(), key=lambda p: (p.is_file(), p.name))
    # 디렉토리 먼저, 그다음 파일 (혹은 이름순). 정렬은 번호 기준 보정
    def sortkey(p):
        m = re.match(r"^([A-Z]?)(\d+)(?:-(\d+))?(?:-(\d+))?", p.name)
        if m:
            alpha = m.group(1) or ""
            nums = tuple(int(g) for g in m.groups()[1:] if g)
            return (0, alpha, nums, p.name)
        return (1, "", (), p.name)

    for entry in sorted(src_dir.iterdir(), key=sortkey):
        if entry.is_dir():
            dcompact = compact(entry.name, is_dir=True)
            dtitle = title_from_name(entry.name)
            sub_nav = process_dir(entry, dst_dir / dcompact, cfg,
                                  f"{rel_label}/{entry.name}", False, dtitle)
            child_dirs.append((dcompact, dtitle))
            nav.append((dtitle, sub_nav, True))
        elif entry.suffix == ".md":
            title = title_from_name(entry.name)
            body = clean_body(entry.read_text(encoding="utf-8"))
            content = "\n".join([
                "---",
                f"정본명: {title}",
                f"유형: {cfg['title']} 항목",
                f'출처: "{rel_label}/{entry.name}"',
                f"검증상태: Phase 2 전수 보존 (원문 보존, {TODAY})",
                "---", "",
                f"# {cfg['emoji']} {title}", "",
                body,
            ])
            out_name = compact(entry.name)
            (dst_dir / out_name).write_text(content, encoding="utf-8")
            child_files.append((out_name, title))
            nav.append((title, out_name, False))

    # index.md
    idx_title = root_title if is_root else f"{cfg['emoji']} {root_title}"
    lines = [
        "---",
        f"정본명: {root_title}",
        "유형: 도감 인덱스",
        f'출처: "{rel_label}"',
        f"검증상태: Phase 2 전수 보존 (원문 보존, {TODAY})",
        "---", "",
        f"# {cfg['emoji']} {root_title}", "",
    ]
    if is_root:
        lines += [f"> {cfg['desc']}", ""]
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


def emit_nav(cfg, nav, indent):
    """nav yaml 스니펫 생성."""
    pad = " " * indent
    out = [f"{pad}- {cfg['title'].split(' (')[0]}:"]
    base = cfg["dst"]
    out.append(f"{pad}    - 전체 인덱스: {base}/index.md")

    def walk(items, prefix_path, lvl):
        p = " " * (indent + 4 * lvl)
        for title, payload, is_dir in items:
            if is_dir:
                dc = compact_dir_lookup[title]
                out.append(f"{p}- {title}:")
                out.append(f"{p}    - 전체 인덱스: {base}/{prefix_path}{dc}/index.md")
                walk(payload, f"{prefix_path}{dc}/", lvl + 1)
            else:
                short = re.sub(r"\s*\([^)]*\)\s*$", "", title)
                out.append(f"{p}- {esc_md(short)}: {base}/{prefix_path}{payload}")
    walk(nav, "", 1)
    return "\n".join(out)


compact_dir_lookup = {}


def run():
    nav_snippets = {}
    for cfg in CONFIGS:
        src = BASE / cfg["src"]
        dst = CANON / cfg["dst"]
        if dst.exists():
            shutil.rmtree(dst)
        root_title = cfg["title"]
        # build compact-dir lookup (title→compact) for nav emit
        for entry in src.rglob("*"):
            if entry.is_dir():
                compact_dir_lookup[title_from_name(entry.name)] = compact(entry.name, is_dir=True)
        nav = process_dir(src, dst, cfg, cfg["src"], True, root_title)
        nfiles = len(list(dst.rglob("*.md")))
        print(f"  {cfg['emoji']} {cfg['dst']}: {nfiles} md")
        nav_snippets[cfg["key"]] = emit_nav(cfg, nav, 10)

    print("\n========== NAV SNIPPETS ==========")
    for k, snip in nav_snippets.items():
        print(f"\n##### {k} #####")
        print(snip)


if __name__ == "__main__":
    run()
