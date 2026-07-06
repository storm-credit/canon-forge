# -*- coding: utf-8 -*-
import io, json, re, sys
sp=r'C:/Users/STORMC~1/AppData/Local/Temp/claude/C--Users-Storm-Credit-Desktop-Novel-theforgottensummoner-new/6eaaa199-6789-409a-ba10-de82822ae096/scratchpad/'
n=int(sys.argv[1])  # 배치 번호 (1부터)
thin=json.load(open(sp+'exist_thin.json',encoding='utf-8'))
E=json.load(open(sp+'e_prompt.json',encoding='utf-8'))
batch=thin[(n-1)*46:n*46]
t=io.open(sp+'e1_wf.js',encoding='utf-8',newline='').read()
t=t.replace("name: 'exist-boost-e1'","name: 'exist-boost-e%d'"%n)
t=t.replace('보강 E1 46명','보강 E%d %d명'%(n,len(batch)))
t=re.sub(r'const targets = \[.*?\]\n', lambda m: 'const targets = '+json.dumps(batch, ensure_ascii=False)+'\n', t, count=1, flags=re.S)
io.open(sp+'e%d_wf.js'%n,'w',encoding='utf-8',newline='').write(t)
print('e%d_wf.js'%n, len(batch))
