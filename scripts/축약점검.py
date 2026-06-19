#!/usr/bin/env python3
"""
축약 점검 게이트 (Condensation Audit Gate)
==========================================
원본 폴더 ↔ 캐논 산출물을 줄수로 대조해 '축약 사고'를 탐지한다.

핵심: 단순 줄수 비교는 무의미하다. 보일러플레이트(에반 가호·순리 노트·
에픽 섭리 콜아웃·도감 위키링크)는 *제거가 정답*이기 때문이다. 따라서
원본에서 보일러플레이트 추정량을 먼저 차감한 '실질 원본'을 분모로 삼아
**보정 보존율(adjusted retention)**을 계산한다.

판정:
  보정 보존율 ≥ 85%  → ✅ 건강 (정당한 청소)
  70% ~ 85%          → ⚠️ 주의 (검토 권장)
  < 70%              → ❌ 축약 의심 (사람이 직접 대조)

사용법:
  python3 scripts/축약점검.py <원본_대륙_폴더> <캐논_대륙_폴더>
예:
  python3 scripts/축약점검.py \
    "/tmp/tfs/.../01-5. 얼음의 땅 – 프로스트 대륙 (Frost Continent)" \
    "docs/canon/2-무대/프로스트대륙"

종료코드: 축약 의심(❌) 1건 이상이면 1, 아니면 0 (CI 게이트용).
"""
import re
import sys
import unicodedata
from pathlib import Path

# 원본에서 제거가 정답인 보일러플레이트 신호 (이 줄들은 분모에서 차감)
BOILERPLATE_PATTERNS = [
    r"에반\s*무영\s*라크라시스",   # 에반 개입 위키링크/언급
    r"\[!NOTE\]", r"\[!IMPORTANT\]", r"\[!CAUTION\]", r"\[!important\]",
    r"에픽\s*섭리", r"우주적\s*십자가", r"순리\s*노트",
    r"Epic\s*Plausibility", r"Plausibility\s*Note",
    r"\[\[01-\d",                  # 도감 경로 위키링크 [[01-15...]] 등
]
BOILER_RE = re.compile("|".join(BOILERPLATE_PATTERNS))

# 의미 줄만 카운트 (공백·구분선 제외)
def meaningful_lines(text: str) -> int:
    n = 0
    for ln in text.splitlines():
        s = ln.strip()
        if not s or s == "---" or set(s) <= {"-", "=", "|", " ", ":"}:
            continue
        n += 1
    return n

def boiler_lines(text: str) -> int:
    return sum(1 for ln in text.splitlines() if BOILER_RE.search(ln))

# 파일명 정규화 매칭용 (괄호·영문·공백·번호 제거 후 한글 핵심만)
def norm_key(name: str) -> str:
    name = unicodedata.normalize("NFC", name)
    name = re.sub(r"\([^)]*\)", "", name)          # (English) 제거
    name = re.sub(r"^[\d.\-\s]+", "", name)         # 앞 번호 제거
    name = re.sub(r"[\s\-–—.&/··]", "", name)  # 구분자(& · / 등) 제거
    name = re.sub(r"(지역|개요|및자원)$", "", name)  # 인덱스 꼬리 noise 제거
    return name.strip().lower()

def gather(folder: Path):
    out = {}
    for f in folder.rglob("*.md"):
        txt = f.read_text(encoding="utf-8", errors="ignore")
        out[norm_key(f.stem)] = (f, meaningful_lines(txt), boiler_lines(txt))
    return out

def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(2)
    src = gather(Path(sys.argv[1]))
    can = gather(Path(sys.argv[2]))

    print(f"{'엔티티':<24}{'원본':>6}{'보일러':>7}{'실질':>6}{'캐논':>6}{'보정율':>8}  판정")
    print("─" * 72)

    suspect = 0
    matched_src = set()
    for key, (cf, cl, cb) in sorted(can.items()):
        if key in src:
            sf, sl, sb = src[key]
            matched_src.add(key)
            real = max(sl - sb, 1)            # 보일러플레이트 차감한 실질 원본
            pct = cl / real * 100
            if pct >= 85:   verdict = "✅"
            elif pct >= 70: verdict = "⚠️ 검토"
            else:           verdict, _ = "❌ 축약의심", suspect
            if pct < 70: suspect += 1
            name = cf.stem[:22]
            print(f"{name:<24}{sl:>6}{sb:>7}{real:>6}{cl:>6}{pct:>7.0f}%  {verdict}")

    # 원본엔 있으나 캐논에 매칭 안 된 파일 = 통째 누락 의심 (인덱스 .md 제외)
    missing = [src[k][0].name for k in src if k not in matched_src
               and not src[k][0].name.startswith(src[k][0].parent.name)]
    orphan = [k for k in src if k not in matched_src]
    if orphan:
        print("─" * 72)
        print(f"⚠️ 캐논 미매칭 원본 {len(orphan)}건 (인덱스/통합 흡수 여부 수동확인):")
        for k in orphan:
            print(f"   · {src[k][0].name}  ({src[k][1]}줄)")

    print("─" * 72)
    print(f"결과: 축약의심 {suspect}건" + ("  → 사람이 직접 대조 필요" if suspect else "  → 통과"))
    sys.exit(1 if suspect else 0)

if __name__ == "__main__":
    main()
