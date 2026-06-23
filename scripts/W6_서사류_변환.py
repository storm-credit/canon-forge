#!/usr/bin/env python3
"""
W6 서사류 전수 수렴 스크립트
처리 대상: 창세신화·고대문명·연대기·신앙체계·전쟁사·대륙별전쟁기술
각 원본 폴더 → 캐논 폴더로 1:1 정제 미러링
"""
import re, shutil
from pathlib import Path

BASE = Path("/tmp/tfs/THE FORGOTTEN SUMMONER/01. 아스트라리스 크로니클")
CANON_ROOT = Path("/home/user/canon-forge/docs/canon")
TODAY = "2026-06-23"

# (원본 폴더, 캐논 폴더, 정본명, 유형)
TARGETS = [
    ("01-1. 창세 신화",                  "0-헌법/창세신화",     "창세 신화",         "세계 헌법 — 창세 신화"),
    ("01-17. 고대 문명",                 "0-헌법/고대문명",     "고대 문명",         "세계 헌법 — 고대 문명"),
    ("01-16. 연대기",                    "0-헌법/연대기",       "연대기",            "세계 헌법 — 연대기"),
    ("01-10. 세계 종교 및 신앙 체계",    "0-헌법/신앙체계",     "세계 종교 및 신앙 체계", "세계 헌법 — 신앙 체계"),
    ("01-9. 전쟁사",                     "2-무대/전쟁사",       "전쟁사",            "무대 — 전쟁사"),
    ("01-11. 대륙별 전쟁 기술",          "2-무대/전쟁기술",     "대륙별 전쟁 기술",  "무대 — 전쟁 기술"),
]


def strip_frontmatter(text):
    text = text.lstrip("﻿")
    if text.startswith("---"):
        end = text.find("\n---\n", 3)
        if end != -1:
            text = text[end + 5:]
    # 본문 중간 frontmatter 잔재 제거
    text = re.sub(r"\n-{3,}\s*\n(?:tags|aliases|type):.*?\n-{3,}\s*(?=\n|$)",
                  "", text, flags=re.DOTALL)
    return text


def strip_boilerplate(text):
    # [!NOTE]/[!IMPORTANT]/[!CAUTION]/[!WARNING] 콜아웃 전체 제거
    text = re.sub(r"> \[!(?:NOTE|IMPORTANT|CAUTION|WARNING|TIP|INFO)\].*?(?=\n\n(?!>)|\Z)",
                  "", text, flags=re.DOTALL)
    # 고전 명작 섭리 후미 섹션 제거
    text = re.sub(r"\n*---\s*\n##\s*\[\s*고전 명작.*?(?=\n##\s|\Z)", "", text, flags=re.DOTALL)
    text = re.sub(r"\n*##\s*\[\s*고전 명작.*?(?=\n##\s|\Z)", "", text, flags=re.DOTALL)
    # HERO_INJECT_ANCHOR 주석
    text = re.sub(r"<!--\s*HERO_INJECT_ANCHOR\s*--+>?", "", text)
    return text


def flatten_roamlinks(text):
    # [[경로|표시텍스트]] → 표시텍스트
    text = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", lambda m: m.group(2), text)
    # [[경로]] → 마지막 세그먼트(파일명 prefix 제거)
    def _plain(m):
        inner = m.group(1).split("/")[-1]
        inner = re.sub(r"^\d+[.\-]\s*", "", inner)  # 번호 prefix 제거
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


def file_title(name):
    """파일명에서 제목 추출: '신들의 서열 (Divine Hierarchy).md' → '신들의 서열 (Divine Hierarchy)'"""
    t = name[:-3] if name.endswith(".md") else name
    return t.strip()


def slug(name):
    """파일명 slug: 공백→없음, 특수문자 제거"""
    s = name[:-3] if name.endswith(".md") else name
    s = re.sub(r"[()'\"/\\]", "", s)
    s = re.sub(r"\s+", "", s)
    return s + ".md"


def process(src_folder_name, canon_rel, section_title, section_type):
    src = BASE / src_folder_name
    dst = CANON_ROOT / canon_rel

    if not src.exists():
        print(f"  ⚠️  원본 없음: {src}")
        return []

    # 기존 단일 .md 파일이 있으면 제거 (요약본 대체)
    old_md = dst.with_suffix(".md") if not dst.exists() else None
    if old_md and old_md.exists():
        old_md.unlink()
        print(f"  🗑  구 요약본 제거: {old_md.name}")

    dst.mkdir(parents=True, exist_ok=True)

    files = sorted([f for f in src.iterdir()
                    if f.suffix == ".md" and not f.name.startswith("_")],
                   key=lambda f: f.name)

    items = []
    for f in files:
        title = file_title(f.name)
        body = clean(f.read_text(encoding="utf-8-sig"))
        if not body:
            continue
        out_name = slug(f.name)
        content = "\n".join([
            "---",
            f"정본명: {title}",
            f"유형: {section_type}",
            f'출처: "{src_folder_name}/{f.name}"',
            f"검증상태: W6 전수 보존 (원문 보존, {TODAY})",
            "---", "",
            body,
        ])
        (dst / out_name).write_text(content, encoding="utf-8")
        items.append((out_name, title))

    # index.md 생성
    lines = [
        "---",
        f"정본명: {section_title}",
        f"유형: {section_type} 인덱스",
        f'출처: "{src_folder_name}"',
        f"검증상태: W6 전수 보존 (원문 보존, {TODAY})",
        "---", "",
        f"# {section_title}", "",
        "| # | 문서 |",
        "|---|------|",
    ]
    for i, (fn, t) in enumerate(items, 1):
        lines.append(f"| {i} | [{t}]({fn}) |")
    (dst / "index.md").write_text("\n".join(lines), encoding="utf-8")

    print(f"  ✅ {section_title}: {len(items)} 파일 → {canon_rel}/")
    return items


def run():
    print("=== W6 서사류 전수 수렴 시작 ===\n")
    nav_lines = []

    for src_name, canon_rel, section_title, section_type in TARGETS:
        items = process(src_name, canon_rel, section_title, section_type)
        # nav 스니펫
        nav_lines.append(f"          - {section_title}:")
        nav_lines.append(f"              - 전체 인덱스: {canon_rel}/index.md")
        for fn, t in items:
            nav_lines.append(f"              - {t}: {canon_rel}/{fn}")

    total = sum(len(list((CANON_ROOT / cr).glob("*.md"))) - 1  # index 제외
                for _, cr, _, _ in TARGETS if (CANON_ROOT / cr).exists())
    print(f"\n총 {total} md 생성 완료")
    print("\n========== NAV SNIPPET ==========")
    print("\n".join(nav_lines))

    # nav 파일 저장
    nav_path = Path("/tmp/claude-0/-home-user-canon-forge/d347be76-2595-51e7-877d-cd2d97c4518a/scratchpad/W6_nav.yml")
    nav_path.parent.mkdir(parents=True, exist_ok=True)
    nav_path.write_text("\n".join(nav_lines), encoding="utf-8")
    print(f"\n(full nav → {nav_path})")


if __name__ == "__main__":
    run()
