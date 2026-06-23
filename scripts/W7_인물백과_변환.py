#!/usr/bin/env python3
"""
W7 인물 백과 전수 수렴 스크립트
처리 대상: 01-15. 인물 백과 (Character Archive) - 33 md
출력: 4-인물/인물-백과/ (폴더 구조 재귀 미러링)
"""
import re
from pathlib import Path

BASE = Path("/tmp/tfs/THE FORGOTTEN SUMMONER/01. 아스트라리스 크로니클")
SRC  = BASE / "01-15. 인물 백과 (Character Archive)"
DST  = Path("/home/user/canon-forge/docs/canon/4-인물/인물-백과")
TODAY = "2026-06-23"
SECTION_TYPE = "인물 — 인물 백과"


# ──────────────────────────── 정제 함수 ────────────────────────────

def strip_frontmatter(text):
    text = text.lstrip("﻿")
    if text.startswith("---"):
        end = text.find("\n---\n", 3)
        if end != -1:
            text = text[end + 5:]
    text = re.sub(r"\n-{3,}\s*\n(?:tags|aliases|type):.*?\n-{3,}\s*(?=\n|$)",
                  "", text, flags=re.DOTALL)
    return text


def strip_boilerplate(text):
    text = re.sub(r"> \[!(?:NOTE|IMPORTANT|CAUTION|WARNING|TIP|INFO)\].*?(?=\n\n(?!>)|\Z)",
                  "", text, flags=re.DOTALL)
    text = re.sub(r"\n*---\s*\n##\s*\[\s*고전 명작.*?(?=\n##\s|\Z)", "", text, flags=re.DOTALL)
    text = re.sub(r"\n*##\s*\[\s*고전 명작.*?(?=\n##\s|\Z)", "", text, flags=re.DOTALL)
    text = re.sub(r"<!--\s*HERO_INJECT_ANCHOR\s*--+>?", "", text)
    return text


def flatten_roamlinks(text):
    text = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", lambda m: m.group(2), text)
    def _plain(m):
        inner = m.group(1).split("/")[-1]
        inner = re.sub(r"^\d+[.\-]\s*", "", inner)
        inner = re.sub(r"\([^)]*\)\s*$", "", inner).strip()
        return inner or m.group(1)
    text = re.sub(r"\[\[([^\]]+)\]\]", _plain, text)
    return text


def flatten_md_links(text):
    text = re.sub(r"\[([^\]]+)\]\(<[^>]*\.md>\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\((?:[^()]|\([^()]*\))*?\.md\)", r"\1", text)
    return text


def clean(text):
    text = strip_frontmatter(text)
    text = strip_boilerplate(text)
    text = flatten_roamlinks(text)
    text = flatten_md_links(text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def folder_slug(name: str) -> str:
    """폴더명 슬러그: 번호 prefix + 영어괄호 제거 + 공백 제거"""
    s = re.sub(r"^\d+[.\-]\s*", "", name)   # 앞 번호 제거
    s = re.sub(r"\([^)]*\)\s*$", "", s).strip()  # 뒤 영문 괄호 제거
    s = re.sub(r"\s+", "", s)
    return s


def file_slug(name: str) -> str:
    """파일명 슬러그: 번호 prefix + 괄호 + 특수문자 제거"""
    s = name[:-3] if name.endswith(".md") else name
    s = re.sub(r"^\d+[.\-]\s*", "", s)     # 앞 번호 제거
    s = re.sub(r"[()'\"/\\]", "", s)
    s = re.sub(r"\s+", "", s)
    return s + ".md"


def file_title(name: str) -> str:
    """파일명에서 제목 추출: 번호 prefix 제거"""
    t = name[:-3] if name.endswith(".md") else name
    t = re.sub(r"^\d+[.\-]\s*", "", t).strip()
    return t


# ──────────────────────────── 재귀 처리 ────────────────────────────

def process_folder(src: Path, dst: Path, section_label: str) -> list[tuple[str, str]]:
    """
    src 폴더를 dst로 재귀 미러링.
    반환값: [(출력_파일명, 표시_제목), ...]  — 현재 레벨 md 파일들
    """
    dst.mkdir(parents=True, exist_ok=True)
    items = []  # (slug_name, display_title, is_folder)

    entries = sorted(src.iterdir(), key=lambda p: p.name)

    for entry in entries:
        if entry.name.startswith("_"):
            continue

        if entry.is_dir():
            sub_slug = folder_slug(entry.name)
            sub_dst  = dst / sub_slug
            sub_label = re.sub(r"^\d+[.\-]\s*", "", entry.name)
            sub_label = re.sub(r"\([^)]*\)\s*$", "", sub_label).strip()
            sub_items = process_folder(entry, sub_dst, sub_label)
            if sub_items:
                items.append((sub_slug + "/index.md", sub_label, True))

        elif entry.suffix == ".md":
            title = file_title(entry.name)
            body  = clean(entry.read_text(encoding="utf-8-sig"))
            if not body:
                continue
            out_name = file_slug(entry.name)
            rel_src  = entry.relative_to(BASE)
            content  = "\n".join([
                "---",
                f"정본명: {title}",
                f"유형: {SECTION_TYPE}",
                f'출처: "{rel_src}"',
                f"검증상태: W7 전수 보존 (원문 보존, {TODAY})",
                "---", "",
                body,
            ])
            (dst / out_name).write_text(content, encoding="utf-8")
            items.append((out_name, title, False))

    # index.md 생성
    lines = [
        "---",
        f"정본명: {section_label}",
        f"유형: {SECTION_TYPE} 인덱스",
        f'출처: "{src.relative_to(BASE)}"',
        f"검증상태: W7 전수 보존 (원문 보존, {TODAY})",
        "---", "",
        f"# {section_label}", "",
        "| # | 항목 |",
        "|---|------|",
    ]
    for i, (fn, title, is_dir) in enumerate(items, 1):
        lines.append(f"| {i} | [{title}]({fn}) |")
    (dst / "index.md").write_text("\n".join(lines), encoding="utf-8")

    md_count = sum(1 for _, _, d in items if not d)
    dir_count = sum(1 for _, _, d in items if d)
    print(f"  ✅ {section_label}: {md_count}파일 + {dir_count}서브폴더 → {dst.relative_to(Path('/home/user/canon-forge/docs/canon'))}/")
    return items


def build_nav(dst: Path, indent: int = 0) -> list[str]:
    """캐논 폴더를 재귀적으로 읽어 nav YAML 스니펫 생성"""
    lines = []
    prefix = "  " * indent
    idx = dst / "index.md"
    if idx.exists():
        rel = idx.relative_to(Path("/home/user/canon-forge/docs/canon"))
        lines.append(f"{prefix}- 전체 인덱스: {rel}")

    entries = sorted(
        [p for p in dst.iterdir() if p.name != "index.md"],
        key=lambda p: p.name
    )
    for entry in entries:
        if entry.is_dir():
            # get label from index.md 정본명 field
            idx2 = entry / "index.md"
            label = entry.name
            if idx2.exists():
                for line in idx2.read_text(encoding="utf-8").splitlines():
                    if line.startswith("정본명:"):
                        label = line.split(":", 1)[1].strip()
                        break
            lines.append(f"{prefix}- {label}:")
            lines.extend(build_nav(entry, indent + 1))
        elif entry.suffix == ".md":
            txt = entry.read_text(encoding="utf-8")
            label = entry.stem
            for line in txt.splitlines():
                if line.startswith("정본명:"):
                    label = line.split(":", 1)[1].strip()
                    break
            rel = entry.relative_to(Path("/home/user/canon-forge/docs/canon"))
            lines.append(f"{prefix}- {label}: {rel}")
    return lines


def run():
    print("=== W7 인물 백과 전수 수렴 시작 ===\n")

    if not SRC.exists():
        print(f"❌ 원본 없음: {SRC}")
        return

    process_folder(SRC, DST, "인물 백과")

    total = sum(1 for _ in DST.rglob("*.md") if _.name != "index.md")
    print(f"\n총 {total} md 생성 완료 (index 제외)\n")

    nav_lines = ["- 인물 백과:"]
    nav_lines.extend(build_nav(DST, indent=1))
    print("========== NAV SNIPPET ==========")
    print("\n".join(nav_lines))

    nav_path = Path("/tmp/claude-0/-home-user-canon-forge/d347be76-2595-51e7-877d-cd2d97c4518a/scratchpad/W7_nav.yml")
    nav_path.parent.mkdir(parents=True, exist_ok=True)
    nav_path.write_text("\n".join(nav_lines), encoding="utf-8")
    print(f"\n(full nav → {nav_path})")


if __name__ == "__main__":
    run()
