#!/usr/bin/env python3
"""
소형 백과 도감 1:1 변환기 (Batch A — 체계.md 기존)
- 소환·주술·신성·직업·마공 도감
- 각 도감 파일(카테고리/직업/학파 1개당 1파일, 서사+표)을 1:1 정제
- 보일러플레이트(NOTE)·frontmatter·roamlink 오염 제거, 본문 전수 보존
"""
import re
import shutil
from pathlib import Path

BASE = Path("/tmp/tfs/THE FORGOTTEN SUMMONER/01. 아스트라리스 크로니클")
DST_ROOT = Path("/home/user/canon-forge/docs/canon/1-시스템")
TODAY = "2026-06-22"

CONFIGS = [
    {
        "key": "summon", "ko": "소환 도감", "emoji": "🌀",
        "src": BASE / "01-37. 소환 백과" / "소환 도감",
        "dst": "소환-도감", "체계": "소환체계", "tier": "조약",
        "src_label": "01-37. 소환 백과/소환 도감",
        "desc": "차원을 찢어 이계 존재를 강제 편입하는 10대 소환 계열. 7대 조약(서클) 트리.",
    },
    {
        "key": "shaman", "ko": "주술 도감", "emoji": "🩸",
        "src": BASE / "01-36. 주술 백과" / "주술 도감",
        "dst": "주술-도감", "체계": "주술체계", "tier": "주계",
        "src_label": "01-36. 주술 백과/주술 도감",
        "desc": "원시 신앙·업보를 매개로 한 13대 주술 계열. 7대 주계 트리.",
    },
    {
        "key": "divine", "ko": "신성 도감", "emoji": "✨",
        "src": BASE / "01-33. 신성 백과" / "6. 신성 도감",
        "dst": "신성-도감", "체계": "신성체계", "tier": "위계",
        "src_label": "01-33. 신성 백과/6. 신성 도감",
        "desc": "신앙의 권능을 구현하는 7대 신성 계열. 7위계 트리.",
    },
    {
        "key": "magitech", "ko": "마법 공학 도감", "emoji": "⚙️",
        "src": BASE / "01-35. 마법 공학 백과" / "마법 공학 도감",
        "dst": "마공-도감", "체계": "마공체계", "tier": "기어",
        "src_label": "01-35. 마법 공학 백과/마법 공학 도감",
        "desc": "마나 동력으로 구동하는 10대 마도 병기 계열. 강철의 7기어 트리.",
    },
    {
        "key": "job", "ko": "직업 도감", "emoji": "🎖️",
        "src": BASE / "01-20. 직업 & 클래스 (Classes & Jobs)" / "직업 도감",
        "dst": "직업-도감", "체계": "직업체계", "tier": None,
        "src_label": "01-20. 직업 & 클래스 (Classes & Jobs)/직업 도감",
        "desc": "대륙 직업 생태계 35종 + 몬스터 헌터. 기원·독점·리스크 전수.",
    },
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
        inner = m.group(1).split("|")[0]                    # alias 분리
        parts = [p.strip() for p in re.split(r"[/\\]", inner) if p.strip()]
        last = parts[-1] if parts else inner
        last = re.sub(r"^\d+(-\d+)*\.\s*", "", last)         # 번호 접두 제거 (10. / 6-1.)
        last = re.sub(r"^\[[^\]]*\]\s*", "", last)           # [히든] 등 선두 태그 제거
        return last.strip()
    # [[path]] — 내부 단일 대괄호([히든]) 허용, 비탐욕 ]] 종료
    return re.sub(r"\[\[(.+?)\]\]", _sub, text)


def collapse_tier(text, tier):
    if not tier:
        return text
    # [17조약 → [1조약, [27주계 → [2주계 등 (tier 키워드의 선두 '7'이 leading digit과 접합된 아티팩트)
    return re.sub(rf"\[(\d+)7{tier}", rf"[\1{tier}", text)


def title_from_name(name):
    t = name[:-3] if name.endswith(".md") else name
    t = re.sub(r"^\d+(-\d+)*\.\s*", "", t)   # 번호 접두 제거
    return t.strip()


def compact_fname(name):
    """'13. [히든] 심연 조각사 (Abyssal Sculptor).md' → '13.심연조각사.md'."""
    stem = name[:-3] if name.endswith(".md") else name
    m = re.match(r"^(\d+(?:-\d+)*)\.\s*(.+)$", stem)
    num = m.group(1) if m else ""
    rest = m.group(2) if m else stem
    rest = re.sub(r"\[[^\]]*\]", "", rest)       # [히든]/[영웅 전설] 제거
    rest = re.sub(r"\([^)]*\)", "", rest)        # (English) 제거
    rest = re.sub(r"\s+", "", rest).strip("-")   # 공백 제거
    return f"{num}.{rest}.md" if num else f"{rest}.md"


def esc_md(s):
    """마크다운 링크 텍스트용 대괄호 이스케이프."""
    return s.replace("[", "\\[").replace("]", "\\]")


def clean_file(src_file, tier):
    text = src_file.read_text(encoding="utf-8")
    text = strip_frontmatter(text)
    text = strip_boilerplate(text)
    text = fix_roamlinks(text)
    text = collapse_tier(text, tier)
    # 원본 messy h1 전부 제거 (상단/중간 'NN-X. ... 도감' 등) — ## 이하 보존
    text = re.sub(r"^#\s[^\n]*\n", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def make_index(cfg, items):
    emoji, ko = cfg["emoji"], cfg["ko"]
    lines = [
        "---",
        f"canon_id: system.{cfg['key']}.lexicon.index",
        f"정본명: {ko}",
        "유형: 전체 인덱스",
        f'출처: "{cfg["src_label"]}"',
        f"검증상태: Phase 2 전수 보존 (원문 보존, {TODAY})",
        "---",
        "",
        f"# {emoji} {ko} (Lexicon)",
        "",
        f"> [{cfg['체계']}]({cfg['체계']}.md)의 부속 도감. {cfg['desc']}",
        "",
        "| # | 항목 |",
        "|---|------|",
    ]
    for i, (fname, title) in enumerate(items, 1):
        lines.append(f"| {i} | [{esc_md(title)}]({fname}) |")
    return "\n".join(lines)


def run():
    summary = []
    for cfg in CONFIGS:
        dst = DST_ROOT / cfg["dst"]
        if dst.exists():
            shutil.rmtree(dst)
        dst.mkdir(parents=True, exist_ok=True)

        items = []
        for src_file in sorted(cfg["src"].iterdir(), key=lambda p: p.name):
            if src_file.suffix != ".md":
                continue
            title = title_from_name(src_file.name)
            body = clean_file(src_file, cfg["tier"])
            content = "\n".join([
                "---",
                f"canon_id: system.{cfg['key']}.{src_file.stem.split('.')[0].strip()}",
                f"정본명: {title}",
                f"유형: {cfg['ko']} 항목",
                f'출처: "{cfg["src_label"]}/{src_file.name}"',
                f"검증상태: Phase 2 전수 보존 (원문 보존, {TODAY})",
                "---",
                "",
                f"# {cfg['emoji']} {title}",
                "",
                body,
            ])
            out_name = compact_fname(src_file.name)  # compact 파일명 (괄호·공백 제거)
            (dst / out_name).write_text(content, encoding="utf-8")
            items.append((out_name, title))

        (dst / "index.md").write_text(make_index(cfg, items), encoding="utf-8")
        summary.append((cfg["ko"], cfg["dst"], len(items)))
        print(f"  {cfg['emoji']} {cfg['dst']}/: {len(items)}항목 + index")

    print("\n=== 완료 ===")
    for ko, dst, n in summary:
        print(f"  {ko}: {n}항목")
    return summary


if __name__ == "__main__":
    run()
