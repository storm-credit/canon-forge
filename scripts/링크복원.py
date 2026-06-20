#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""위키링크 교차참조 복원 모듈 (Hanesis [C] 보강).

원본의 경로형 위키링크 [[01-20. 직업.../19. 용병 (Mercenary)]] 는
캐논 변환 시 마지막 세그먼트만 남겨 '19. 용병 (Mercenary)' 죽은 텍스트가 됐다.
이 모듈은 prefix(백과 분류)를 보고 캐논 시스템 문서로 링크를 되살린다:

  01-20 직업      → [[직업체계|용병]]
  01-19 아이템    → [[아이템-도감|성물]]
  01-31/9 마법    → [[마법체계|...]]
  01-37 소환      → [[소환체계|...]]
  01-35 마공      → [[마공체계|...]]
  01-34 연금      → [[연금체계|...]]
  01-32 정령      → [[정령체계|...]]
  01-10 종교/신앙 → [[신앙체계|...]]
  01-15 인물(에반) → [[에반]]
  그 외           → 캐논에 동명 파일이 있으면 [[슬러그]], 없으면 평문(번호·영문 제거)
"""
import re

# 순서 중요: '마법 공학'(마공)이 '마법'보다 먼저 매칭돼야 한다.
SYSTEM_RULES = [
    (re.compile(r"마법\s*공학|마공|01-35"),          "마공체계"),
    (re.compile(r"직업|Classes|Jobs|01-20"),          "직업체계"),
    (re.compile(r"아이템|Item\s*Enc|01-19"),          "아이템-도감"),
    (re.compile(r"소환|Summon|01-37"),                "소환체계"),
    (re.compile(r"연금|Alchem|01-34"),                "연금체계"),
    (re.compile(r"정령|Spirit|01-32"),                "정령체계"),
    (re.compile(r"주술|Curse|Hex|01-33"),             "주술체계"),
    (re.compile(r"신성|Divin|Holy\s*Sys"),            "신성체계"),
    (re.compile(r"마법|Magic|01-31|01-9(?!\d)"),       "마법체계"),
    (re.compile(r"종교|신앙|Religion|Faith|01-10"),    "신앙체계"),
]


def _strip_label(s):
    """표시명 정규화: 번호접두사·영문괄호·trailing backslash 제거."""
    s = s.split("/")[-1].strip().rstrip("\\").strip()
    s = re.sub(r"^\d+[-.]?\d*\.?\s*", "", s)        # 번호 접두사 (19. / 01-2. 등)
    s = re.sub(r"\s*\([^)]*\)\s*$", "", s).strip()  # 끝의 (English) 괄호
    return s


def _resolve_doc(target):
    """위키링크 대상 경로 → 캐논 시스템 문서명 (없으면 None)."""
    prefix = target.split("/")[0].strip().lstrip("[").strip()
    for rx, doc in SYSTEM_RULES:
        if rx.search(prefix):
            return doc
    if ("인물 백과" in prefix) or ("Character Archive" in prefix):
        if "에반" in target or "Evan" in target:
            return "에반"
        return None  # 일반 인물: 개별 캐논 문서 없음 → 평문 처리
    return None


def restore_wikilinks(text, canon_slugs):
    """text 내 모든 위키링크를 캐논 기준으로 복원. canon_slugs=공백제거 파일stem set."""
    def repl(m):
        inner = m.group(1)
        if "|" in inner:
            target, disp = inner.split("|", 1)
        else:
            target, disp = inner, None
        name = _strip_label(disp if disp is not None else target)
        doc = _resolve_doc(target)
        if doc:
            return f"[[{doc}]]" if doc == name else f"[[{doc}|{name}]]"
        # 시스템 문서가 아님 → 캐논에 동명 파일이 있으면 내부 링크 유지
        slug = name.replace(" ", "")
        if slug and slug in canon_slugs:
            return f"[[{slug}]]" if slug == name else f"[[{slug}|{name}]]"
        return name  # 평문 (번호·영문 제거된 깔끔한 이름)

    # 중첩 [[[...]]] (원본 오기) 정규화 후 처리 — 외톨이 [ 잔존 방지
    text = re.sub(r"\[{3,}", "[[", text)
    text = re.sub(r"\]{3,}", "]]", text)
    return re.sub(r"\[\[([^\[\]]+)\]\]", repl, text)


def build_canon_slugs(canon_root):
    import os
    slugs = set()
    for dp, _, fns in os.walk(canon_root):
        for fn in fns:
            if fn.endswith(".md"):
                slugs.add(fn[:-3].replace(" ", ""))
    return slugs
