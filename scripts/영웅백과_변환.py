#!/usr/bin/env python3
"""
W4 영웅 백과 전수 수렴기 (1,491파일 / 3대 분류)
- 성장 영웅(115) · 현존 영웅(1,211) · 소환 영웅(165)
- 폴더 구조 그대로 재귀 미러링, 1:1 정제
- 각 폴더에 index.md 생성, nav 스니펫 stdout 출력
- 보일러플레이트 제거:
    · [!IMPORTANT] 7축 거시 엔진 연동 (Hanesis 메타)
    · [!NOTE] 에픽 섭리 + The Anchor (에반 개입 당위성)
    · ## [ 고전 명작 판타지의 섭리 ] 후미 섹션
    · <!-- HERO_INJECT_ANCHOR --> 주석
- _prefix 폴더/파일(메타·백업) 제외
"""
import re
import shutil
from pathlib import Path

BASE = Path("/tmp/tfs/THE FORGOTTEN SUMMONER/01. 아스트라리스 크로니클/01-14. 영웅 백과 (Hero Archive)")
CANON = Path("/home/user/canon-forge/docs/canon/4-인물/영웅-백과")
TODAY = "2026-06-23"

TIER_KW = ["7조약", "7주계", "7기어", "7위계", "5계급", "7주신", "7단계"]

ROOT_TITLE = "영웅 백과 (Hero Archive)"
ROOT_DESC = "아스트라리스 성장·현존·소환 영웅 전수 아카이브 — 3대 분류, 1,491파일."
EMOJI = "⚔️"


def strip_frontmatter(text):
    # UTF-8 BOM 제거
    text = text.lstrip("﻿")
    if text.startswith("---"):
        end = text.find("\n---\n", 3)
        if end != -1:
            text = text[end + 5:]
    # 본문 중간/후미 중복 frontmatter 블록 제거
    text = re.sub(r"\n-{3,}\s*\n(?:tags|aliases|type):.*?\n-{3,}\s*(?=\n|$)",
                  "", text, flags=re.DOTALL)
    return text


def strip_boilerplate(text):
    # [!NOTE]/[!IMPORTANT]/[!CAUTION] 콜아웃 블록 전체 제거
    text = re.sub(r"> \[!(?:NOTE|IMPORTANT|CAUTION|WARNING|TIP|INFO)\].*?(?=\n\n(?!>)|\Z)",
                  "", text, flags=re.DOTALL)
    # 후미 '고전 명작 판타지의 섭리' 섹션 제거
    text = re.sub(r"\n*---\s*\n##\s*\[\s*고전 명작 판타지의 섭리.*?(?=\n##\s|\Z)",
                  "", text, flags=re.DOTALL)
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
        last = re.sub(r"^\d+(-\d+)*\.\s*", "", last)
        last = re.sub(r"^[A-Z]-\d+(-\d+)*\.\s*", "", last)
        last = re.sub(r"^\[[^\]]*\]\s*", "", last)
        return last.strip()
    return re.sub(r"\[\[(.+?)\]\]", _sub, text)


def collapse_tiers(text):
    for kw in TIER_KW:
        text = re.sub(rf"\[(\d+){kw}", rf"[\1{kw[1:]}", text)
    return text


def flatten_md_links(text):
    text = re.sub(r"\[([^\]]+)\]\(<[^>]*\.md>\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\((?:[^()]|\([^()]*\))*?\.md\)", r"\1", text)
    return text


def clean_body(text):
    text = strip_frontmatter(text)
    text = strip_boilerplate(text)
    text = fix_roamlinks(text)
    text = collapse_tiers(text)
    text = flatten_md_links(text)
    text = re.sub(r"^#\s[^\n]*\n", "", text, flags=re.MULTILINE)  # 모든 h1 제거
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def strip_prefix(s):
    return re.sub(r"^[A-Z0-9]+(?:-[A-Z0-9]+)*(?:-\d+)*\.\s*", "", s).strip()


def title_from_name(name):
    t = name[:-3] if name.endswith(".md") else name
    t = re.sub(r"^\[[^\]]*\]\s*", "", t)  # [현존] [히든] 등 태그 제거
    t = strip_prefix(t) or t
    t = re.sub(r"\s+\d+\.\s+", " / ", t)
    t = re.sub(r"\s{2,}", " ", t).strip()
    return t


def compact(name, is_dir=False):
    stem = name if is_dir else (name[:-3] if name.endswith(".md") else name)
    # [현존] 등 태그 제거 후 처리
    stem = re.sub(r"^\[[^\]]*\]\s*", "", stem)
    m = re.match(r"^([A-Z0-9]+(?:-[A-Z0-9]+)*(?:-\d+)*)\.\s*(.+)$", stem)
    num = m.group(1) if m else ""
    rest = m.group(2) if m else stem
    rest = re.sub(r"\[[^\]]*\]", "", rest)
    rest = re.sub(r"\([^)]*\)", "", rest)
    rest = re.sub(r"\s+\d+\.\s+", " ", rest)
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


def process_dir(src_dir, dst_dir, rel_label, is_root, root_title):
    dst_dir.mkdir(parents=True, exist_ok=True)
    child_files = []
    child_dirs = []
    nav = []

    seen_files = set()
    for entry in sorted(src_dir.iterdir(), key=sortkey):
        # _prefix: 메타/백업 제외
        if entry.name.startswith("_"):
            continue
        if entry.is_dir():
            dcompact = compact(entry.name, is_dir=True)
            dtitle = title_from_name(entry.name)
            sub_nav = process_dir(entry, dst_dir / dcompact,
                                  f"{rel_label}/{entry.name}", False, dtitle)
            child_dirs.append((dcompact, dtitle))
            nav.append((dtitle, dcompact, sub_nav, True))
        elif entry.suffix == ".md":
            # ( 접두사: 메타 placeholder 제외
            if entry.name.startswith("("):
                continue
            title = title_from_name(entry.name)
            body = clean_body(entry.read_text(encoding="utf-8-sig"))
            if not body:
                continue
            out_name = compact(entry.name)
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
        "유형: 영웅 백과 인덱스",
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
        lines += ["## 항목", "", "| # | 영웅 |", "|---|------|"]
        for i, (fn, t) in enumerate(child_files, 1):
            lines.append(f"| {i} | [{esc_md(t)}]({fn}) |")
    (dst_dir / "index.md").write_text("\n".join(lines), encoding="utf-8")
    return nav


def emit_nav(nav, indent):
    pad = " " * indent
    base = "4-인물/영웅-백과"
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
    nav = process_dir(BASE, CANON, "01-14. 영웅 백과 (Hero Archive)", True, ROOT_TITLE)
    nfiles = len(list(CANON.rglob("*.md")))
    print(f"  {EMOJI} {CANON}: {nfiles} md")
    print("\n========== NAV SNIPPET ==========")
    snippet = emit_nav(nav, 6)
    nav_path = Path("/tmp/claude-0/-home-user-canon-forge/d347be76-2595-51e7-877d-cd2d97c4518a/scratchpad/hero_nav.yml")
    nav_path.write_text(snippet, encoding="utf-8")
    print(snippet[:3000])
    print(f"\n... (full nav written to scratchpad/hero_nav.yml, {len(snippet.splitlines())} lines)")


if __name__ == "__main__":
    run()
