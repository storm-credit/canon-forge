# -*- coding: utf-8 -*-
"""탈무협 정밀 스캐너 — 아스트라리스=순수 판타지 원칙(2026-07-06 작가 판정).
무협 체계 어휘 실사용을 오탐 필터와 함께 검출. 사용: python tools/pipeline/wuxia_scan.py"""
import glob, io, re
KW=['기공','무공','내공','단전','무림','도인','협객','비급','혈도','점혈','장풍','강호']
FALSE=re.compile(r'(좀비급|헤비급|S비급|구강호|순도인|인도인|주도인|과도인|정도인|지도인|유도인|설계도인|하수도인|보도인|단전투|차단전|단전시|단전이 아|기공사|기공학|기공식|공기공|분기공|대기공|기공포|고기공|장풍\(長風\)|성좌 혈도|성좌혈도|유혈도|빛무림)')
OK=('크로니클-로드맵','잊히지 않는 단심','세계의-헌법','감시자','_작업','_인수인계','_동명판정','_collisions','_전수분석','_progress','_종족혈통','_정본명','_커버리지','_PLAN','_구조설계','_phase3','_백과수렴')
n=0
for p in glob.glob('docs/canon/**/*.md', recursive=True):
    if any(k in p for k in OK): continue
    t=io.open(p,encoding='utf-8',errors='ignore').read()
    for kw in KW:
        for m in re.finditer(kw, t):
            seg=t[max(0,m.start()-12):m.end()+12]
            if FALSE.search(seg): continue
            n+=1
            print(kw,'::',p.split('canon')[-1][-55:],'::',t[max(0,m.start()-35):m.end()+35].replace('\n',' ')[:90])
print('의심 잔존:', n)
