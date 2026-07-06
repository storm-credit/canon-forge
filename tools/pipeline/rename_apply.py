# -*- coding: utf-8 -*-
"""아이템 파일명 정본화 적용기.
입력: decisions JSON [{file, action, newKo, newEn, note}], 대상 폴더.
동작: 파일명 개명 + 프론트매터 정본명/이명 갱신 + H1 교체 + 이명 보존 + 리포 전역 인바운드 링크 재작성.
사용: python rename_apply.py <decisions.json> <folder> [--apply]
"""
import io, json, glob, os, re, sys, urllib.parse

dec_path, folder = sys.argv[1], sys.argv[2]
APPLY = '--apply' in sys.argv
decisions = json.load(open(dec_path, encoding='utf-8'))

BADFS = re.compile(r'[\\/:*?"<>|]')
renames = []  # (old_base, new_base)
skips = []

# 리포 전체 기존 파일명 인덱스 (충돌 검사)
all_bases = set()
for p in glob.glob('docs/canon/**/*.md', recursive=True):
    all_bases.add(os.path.basename(p))

planned = set()
for d in decisions:
    if d.get('action') != 'rename':
        continue
    old = d['file']
    oldp = os.path.join(folder, old)
    if not os.path.exists(oldp):
        skips.append((old, '원본 없음')); continue
    ko = BADFS.sub('', (d.get('newKo') or '').strip())
    en = BADFS.sub('', (d.get('newEn') or '').strip())
    en = re.sub(r'[가-힣]', '', en).strip()
    if not ko or not en:
        skips.append((old, 'newKo/newEn 불량')); continue
    new = f'{ko} ({en}).md'
    if new == old:
        continue
    if new in all_bases or new in planned:
        skips.append((old, '충돌: ' + new)); continue
    planned.add(new)
    renames.append((old, new, ko, en))

print(f'개명 계획 {len(renames)} / 건너뜀 {len(skips)}')
for o, r in skips:
    print('  SKIP', o[:50], '::', r)

if not APPLY:
    for o, n, *_ in renames[:20]:
        print('  ', o[:55], '→', n)
    print('[DRY-RUN]'); sys.exit(0)

# 1) 파일 내부 갱신 + 개명
for old, new, ko, en in renames:
    oldp = os.path.join(folder, old)
    oldtitle = old[:-3]
    newtitle = f'{ko} ({en})'
    t = io.open(oldp, encoding='utf-8', errors='ignore').read()
    # 프론트매터 정본명 + 이명
    m = re.search(r'^정본명:\s*(.+)$', t, re.M)
    if m:
        rep = f'정본명: {newtitle}\n이명: "{oldtitle}"'
        t = t[:m.start()] + rep + t[m.end():]
    # H1 교체 (선두 이모지 보존) + 이명 블록쿼트
    hm = re.search(r'^#\s+([^\n]*)$', t, re.M)
    if hm:
        line = hm.group(1)
        em = re.match(r'^([^\w가-힣<>]*)', line)
        prefix = (em.group(1).strip() + ' ') if em and em.group(1).strip() else ''
        newh = f'# {prefix}{newtitle}\n\n> 이명(異名): {oldtitle}'
        t = t[:hm.start()] + newh + t[hm.end():]
    io.open(oldp, 'w', encoding='utf-8', newline='').write(t)
    os.rename(oldp, os.path.join(os.path.dirname(oldp), new))

# 2) 리포 전역 인바운드 링크 재작성 (원문·URL인코딩 두 변형)
pairs = []
for old, new, *_ in renames:
    old = os.path.basename(old)
    pairs.append((old, new))
    qo, qn = urllib.parse.quote(old), urllib.parse.quote(new)
    if qo != old:
        pairs.append((qo, qn))
    so, sn = old.replace(' ', '%20'), new.replace(' ', '%20')
    if so != old:
        pairs.append((so, sn))
    def mixenc(s):
        return s.replace('%', '%25').replace(' ', '%20').replace('(', '%28').replace(')', '%29')
    mo, mn = mixenc(old), mixenc(new)
    if mo != old:
        pairs.append((mo, mn))

touched = 0
for p in glob.glob('docs/canon/**/*.md', recursive=True):
    t = io.open(p, encoding='utf-8', errors='ignore').read()
    nt = t
    for o, n in pairs:
        if o in nt:
            nt = nt.replace(o, n)
    if nt != t:
        io.open(p, 'w', encoding='utf-8', newline='').write(nt)
        touched += 1

print(f'[APPLIED] 개명 {len(renames)}건 / 링크 갱신 파일 {touched}')
