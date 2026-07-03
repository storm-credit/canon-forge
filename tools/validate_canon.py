# -*- coding: utf-8 -*-
"""캐논 기계검증 도구 (P1-10 정식화, 2026-07-02)

사용: python tools/validate_canon.py [--links] [--grades] [--vocab] [--dupes] [--all]
리포 루트에서 실행. 출력은 요약 통계 + 위반 목록.
"""
import glob, io, os, re, sys, urllib.parse
from collections import Counter, defaultdict

CANON = 'docs/canon'
ARGS = set(sys.argv[1:]) or {'--all'}
def on(k): return '--all' in ARGS or k in ARGS

META_SKIP = ('_작업계획서', '_커버리지', '_작업프롬프트', '_progress', '_전수분석', '_대륙작업템플릿', '_백과수렴')

def canon_files():
    for p in glob.glob(CANON + '/**/*.md', recursive=True):
        pp = p.replace(os.sep, '/')
        rel = pp.split('docs/canon/')[-1]
        if any(rel.startswith(m) for m in META_SKIP):
            continue
        yield p, rel

fail = 0

if on('--links'):
    lr = re.compile(r'\]\(([^)]+\.md)\)')
    brk = []
    total = 0
    for p, rel in canon_files():
        t = io.open(p, encoding='utf-8', errors='ignore').read()
        d = os.path.dirname(os.path.abspath(p))
        for m in lr.finditer(t):
            u = m.group(1)
            if u.startswith('http'):
                continue
            total += 1
            if not os.path.exists(os.path.normpath(os.path.join(d, urllib.parse.unquote(u)))):
                brk.append((rel, u))
    print(f'[links] 총 {total} / 깨짐 {len(brk)}')
    for f, u in brk[:20]:
        print('   BROKEN', f[:60], '::', u[:70])
    fail += len(brk)

if on('--grades'):
    # 정본 5등급 + 허용 예외
    OK = {'신화급 (Mythic)', '전설급 (Legendary)', '영웅급 (Hero)', '희귀급 (Rare)', '일반급 (Common)'}
    EXC = ('유물급', '아티팩트', '오파츠', '특수 (Special)', '개조 (Modified)', '정예(A)', '미식')
    gr = re.compile(r'\|\s*\*\*등급\*\*\s*\|\s*([^|]+)\|')
    bad = Counter()
    for p, rel in canon_files():
        if '아이템-도감' not in rel:
            continue
        t = io.open(p, encoding='utf-8', errors='ignore').read()
        m = gr.search(t)
        if not m:
            continue
        cell = re.sub(r'[*🔴🟠🟣🔵⚪✨🟡✦]', '', m.group(1)).strip()
        if cell in OK or any(e in cell for e in EXC):
            continue
        bad[cell[:30]] += 1
    print(f'[grades] 비정본 라벨 {sum(bad.values())}건 / {len(bad)}종')
    for k, v in bad.most_common(10):
        print(f'   {v:4d}  {k}')
    fail += sum(bad.values())

if on('--vocab'):
    BAN = ['우주적 십자가', 'Epic Penalty', '우주적 등가교환', '가혹한 참상', 'Bit v4.0 (플레이스홀더', '세계관의 섭리를 비트',
           '숭고한 십자가', '잔혹한 대가', '혹독한 대가', '코스믹 호러', 'Grim Plausibility', '경박한 수치화']
    NEG = ('아니라', '아니다', '폐기', '금지', '없다', '무관', '재정의', '소거')
    hits = []
    for p, rel in canon_files():
        t = io.open(p, encoding='utf-8', errors='ignore').read()
        for b in BAN:
            for m in re.finditer('[^\n]*' + re.escape(b) + '[^\n]*', t):
                ln = m.group(0)
                if any(n in ln for n in NEG):
                    continue  # 부정문·폐기 규정 자체는 정당
                hits.append((rel, b))
                break
    print(f'[vocab] 폐기 어휘 잔존 {len(hits)}건')
    for f, b in hits[:15]:
        print('   ', f[:60], '::', b)
    fail += len(hits)

if on('--dupes'):
    # 정본명 유일성: 동일 정본명이 복수 파일에 존재
    names = defaultdict(list)
    for p, rel in canon_files():
        t = io.open(p, encoding='utf-8', errors='ignore').read(600)
        m = re.search(r'정본명:\s*(.+)', t)
        if m:
            nm = m.group(1).strip().strip('"')
            if nm and nm not in ('무기', '방어구', '악세서리', '유물'):
                names[nm].append(rel)
    dupes = {k: v for k, v in names.items() if len(v) > 1}
    print(f'[dupes] 정본명 중복 {len(dupes)}종 / {sum(len(v) for v in dupes.values())}파일')
    for k, v in sorted(dupes.items(), key=lambda x: -len(x[1]))[:10]:
        print(f'   {len(v)}중복  {k[:44]}')
    # 충돌 대장 갱신
    out = ['---', '정본명: 정본명 유일성 레지스트리', '유형: 기계검증 산출물 (tools/validate_canon.py --dupes)', '---', '',
           '# 정본명 유일성 레지스트리', '',
           '> 동일 정본명이 복수 파일에 존재하는 충돌 목록. 동명이인·의도적 변형은 검토 후 이 목록에서 "허용" 표기, 나머지는 개명 대상.', '']
    for k, v in sorted(dupes.items(), key=lambda x: -len(x[1])):
        out.append(f'## {k}')
        for f in v:
            out.append(f'- {f}')
        out.append('')
    io.open('docs/canon/_정본명_유일성_레지스트리.md', 'w', encoding='utf-8', newline='').write('\n'.join(out))
    print('   → docs/canon/_정본명_유일성_레지스트리.md 갱신')

print()
print('검증 종료 —', ('위반 %d건' % fail) if fail else '전 항목 통과')
sys.exit(1 if fail else 0)
