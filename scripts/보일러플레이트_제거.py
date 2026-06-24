#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""보일러플레이트 콜아웃 블록 일괄 제거 (변환 후처리, idempotent).

strip_boilerplate()가 한글 마커("세력의 우주적 십자가")에만 의존해
조직별 변형("세력의 에픽 십자가" 등)을 놓친 잔존분을 정리한다.

제거 대상: `> [!CAUTION]` / `> [!NOTE]` 로 시작하는 인용 콜아웃 블록 중
  본문에 다음 시그니처를 하나라도 포함하는 것:
    - "Epic Burden"            (영문 공통, 모든 한글 변형 무관)
    - "The Anchor"
    - "개입의 맹목적 당위성"
    - "우주적 십자가" / "에픽 십자가" / "에픽 섭리"
보존 대상: 본문 콜아웃([!INFO] 변경 거점 등) 및 시그니처 없는 [!CAUTION]/[!NOTE].

블록 제거 후 인접한 잉여 빈 줄/`---` 구분선을 정리한다.

사용법: python3 scripts/보일러플레이트_제거.py <폴더|파일> [...]
종료코드 0. 변경된 파일과 제거 블록 수를 출력.
"""
import os, re, sys

SIGNATURES = ("Epic Burden", "The Anchor", "개입의 맹목적 당위성",
              "우주적 십자가", "에픽 십자가", "에픽 섭리와 유구한 운명", "에픽 섭리")
CALLOUT_OPEN = re.compile(r"^\s*>\s*\[!(CAUTION|NOTE|WARNING|IMPORTANT)\]")


def is_quote(ln):
    return ln.lstrip().startswith(">")


def strip_callouts(text):
    lines = text.split("\n")
    out = []
    i = 0
    removed = 0
    n = len(lines)
    while i < n:
        if CALLOUT_OPEN.match(lines[i]):
            # 인용 블록 수집 (연속된 '>' 줄)
            j = i
            while j < n and (is_quote(lines[j]) or lines[j].strip() == ""):
                # 빈 줄은 블록 내부 구분일 수 있으나, 다음이 '>'가 아니면 종료
                if lines[j].strip() == "":
                    if j + 1 < n and is_quote(lines[j + 1]):
                        j += 1
                        continue
                    break
                j += 1
            block = "\n".join(lines[i:j])
            if any(sig in block for sig in SIGNATURES):
                removed += 1
                # 블록 앞 잉여 빈 줄/--- 정리
                while out and out[-1].strip() in ("", "---"):
                    out.pop()
                # 블록 뒤 잉여 빈 줄/--- 정리
                while j < n and lines[j].strip() in ("", "---"):
                    j += 1
                # 단락 구분 위해 빈 줄 하나 보장
                if out and out[-1].strip() != "":
                    out.append("")
                i = j
                continue
        out.append(lines[i])
        i += 1
    result = "\n".join(out)
    result = re.sub(r"\n{3,}", "\n\n", result).strip() + "\n"
    return result, removed


def iter_md(paths):
    for p in paths:
        if os.path.isfile(p) and p.endswith(".md"):
            yield p
        elif os.path.isdir(p):
            for root, _, files in os.walk(p):
                for f in sorted(files):
                    if f.endswith(".md"):
                        yield os.path.join(root, f)


def main(argv):
    if not argv:
        print("사용법: python3 scripts/보일러플레이트_제거.py <폴더|파일> [...]")
        return 0
    total_files, total_blocks = 0, 0
    for fp in iter_md(argv):
        s = open(fp, encoding="utf-8").read()
        new, removed = strip_callouts(s)
        if removed:
            open(fp, "w", encoding="utf-8").write(new)
            total_files += 1
            total_blocks += removed
            print(f"  [{removed}블록 제거] {fp}")
    print(f"\n총 {total_files}개 파일에서 {total_blocks}개 보일러플레이트 블록 제거")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
