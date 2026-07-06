# -*- coding: utf-8 -*-
"""배치 후처리: 링크 깊이 보정 + 유니크 basename 힐 + (Heroic) 등급 정규화"""
import glob, io, os, re, urllib.parse
from collections import defaultdict
idx=defaultdict(list)
for p in glob.glob('docs/canon/**/*.md', recursive=True):
    idx[os.path.basename(p)].append(p.replace(os.sep,'/'))
lr=re.compile(r'\]\(([^)]+\.md)\)')
fixed=0; unres=[]
for p in glob.glob('docs/canon/**/*.md', recursive=True):
    t=io.open(p,encoding='utf-8',errors='ignore').read()
    d=os.path.dirname(p); nt=t
    for m in lr.finditer(t):
        u=m.group(1)
        if u.startswith('http'): continue
        uq=urllib.parse.unquote(u)
        if os.path.exists(os.path.normpath(os.path.join(d,uq))): continue
        done=False
        for cand in ['../'+uq, uq[3:] if uq.startswith('../') else None, '../../'+uq]:
            if cand and os.path.exists(os.path.normpath(os.path.join(d,cand))):
                enc=cand.replace(' ','%20').replace('(','%28').replace(')','%29') if '%' in u else cand
                nt=nt.replace('('+u+')','('+enc+')'); fixed+=1; done=True; break
        if not done:
            base=os.path.basename(uq); cands=idx.get(base,[])
            if len(cands)==1:
                rel=os.path.relpath(cands[0], d.replace(os.sep,'/')).replace(os.sep,'/')
                enc=rel.replace(' ','%20').replace('(','%28').replace(')','%29') if '%' in u else rel
                nt=nt.replace('('+u+')','('+enc+')'); fixed+=1
            else: unres.append((p.split('canon')[-1][:55], base[:40], len(cands)))
    nt2=nt.replace('영웅급 (Heroic)','영웅급 (Hero)').replace('유니크 (Unique)','영웅급 (Hero)').replace('에픽 (Epic)','영웅급 (Hero)').replace('레전더리 (Legendary)','전설급 (Legendary)')
    if nt2!=t: io.open(p,'w',encoding='utf-8',newline='').write(nt2)
print('링크 보정', fixed, '/ 미해결', len(unres))
for x in unres[:8]: print('  ', x)
