# -*- coding: utf-8 -*-
"""신규 딥 아이템 파일의 상대링크를 실제 대상으로 해석해 올바른 상대경로로 재작성. dry 기본, --apply."""
import glob, io, os, re, sys, urllib.parse
ROOT = r"C:/Users/Storm Credit/Desktop/Novel/theforgottensummoner_new"
CANON = ROOT + "/docs/canon"
APPLY = '--apply' in sys.argv

def apnorm(s):
    # 아포스트로피 정규화: curly(U+2019)·prime 등 → straight '
    return s.replace('’', "'").replace('ʼ', "'").replace('‘', "'").replace('`', "'")

# basename → [절대경로...] 전체 인덱스 (아포스트로피 정규화 키 포함)
idx = {}
for p in glob.glob(CANON + "/**/*.md", recursive=True):
    b = os.path.basename(p)
    pp = p.replace(os.sep, '/')
    idx.setdefault(b, []).append(pp)
    nb = apnorm(b)
    if nb != b:
        idx.setdefault(nb, []).append(pp)

newfiles = [l.strip() for l in io.open(r"C:/Users/STORMC~1/AppData/Local/Temp/claude/C--Users-Storm-Credit-Desktop-Novel-theforgottensummoner-new/6eaaa199-6789-409a-ba10-de82822ae096/scratchpad/new74.txt", encoding='utf-8') if l.strip()]

linkre = re.compile(r'\]\(([^)]+\.md)\)')
fixed = 0; flagged = []; fileshit = 0
for rel in newfiles:
    p = ROOT + "/" + rel
    if not os.path.exists(p):
        p = rel  # already relative to root cwd
    if not os.path.exists(p): continue
    t = io.open(p, encoding='utf-8', errors='ignore').read()
    d = os.path.dirname(os.path.abspath(p))
    changed = False
    def repl(m):
        global fixed, changed
        url = m.group(1)
        dec = urllib.parse.unquote(url)
        base = os.path.basename(dec)
        # 이미 올바르게 해석되면 스킵
        cur = os.path.normpath(os.path.join(d, dec))
        if os.path.exists(cur):
            return m.group(0)
        cands = idx.get(base, []) or idx.get(apnorm(base), [])
        if len(cands) == 1:
            tgt = cands[0]
            newrel = os.path.relpath(tgt, d).replace(os.sep, '/')
            enc = newrel.replace(' ', '%20').replace('(', '%28').replace(')', '%29')
            fixed += 1; changed = True
            return '](' + enc + ')'
        else:
            flagged.append((os.path.basename(p), base, len(cands)))
            return m.group(0)
    nt = linkre.sub(repl, t)
    if nt != t:
        fileshit += 1
        if APPLY:
            io.open(p, 'w', encoding='utf-8', newline='').write(nt)

print("링크 수정: %d건 / %d파일 / 미해결 %d" % (fixed, fileshit, len(flagged)))
for b, base, n in flagged[:30]:
    print("  [미해결 %d후보] %s -> %s" % (n, b[:34], base[:44]))
print("[APPLIED]" if APPLY else "[DRY-RUN]")
