#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""원본 ↔ 캐논 항목 단위 전수 대조 ([C] Hanesis 검수 정식 도구).

작업프롬프트 [C] 정의 구현: 원본 각 파일에서 헤더·표 굵은항목·고유명사를
추출해 캐논 산출물 전체에 그 항목이 실제로 존재하는지 1:1 확인한다.
줄수 기반 축약점검(scripts/축약점검.py)을 보완하는 '항목 단위' 게이트.

노이즈 제외: 보일러플레이트 콜아웃(에픽 섭리·우주적 십자가), 에반 개입 헤더,
원본 위키링크 경로(01-XX 백과 참조), 영문 괄호주석, 선두 번호접두사.

사용법:
  python3 scripts/원본대조.py <원본_세력_폴더> <캐논_세력_폴더> <캐논_개요.md>
종료코드: 진짜 누락 1건 이상이면 1 (CI 게이트용).
"""
import os, re, sys

def strip_fm(t):
    if t.startswith("---"):
        m = re.match(r"^---\s*\n.*?\n---\s*\n", t, re.DOTALL)
        if m: return t[m.end():]
    return t

def normalize(s):
    s = re.sub(r'\[\[[^\]|]+\|([^\]]+)\]\]', r'\1', s)
    s = re.sub(r'\[\[([^\]]+)\]\]', lambda m: m.group(1).split('/')[-1].split('|')[-1], s)
    s = re.sub(r'\(([A-Za-z][^)]*)\)', '', s)
    s = re.sub(r'^\s*\d+[-.]\s*', '', s)
    s = re.sub(r'#[^\s#]+', '', s)
    return re.sub(r'[\s.]+', '', s)

def is_noise(s):
    for k in ('01-15. 인물','01-20. 직업','01-31. 마법','01-14. 영웅','01-34','01-32',
              '에픽 섭리','우주적 십자가','관련 문서','관련 및 서사'):
        if k in s: return True
    return '에반' in s and '개입' in s

def items(body):
    for h in re.findall(r'^#{2,}\s+(.+)$', body, re.M): yield ('H', h.strip())
    for b in re.findall(r'\*\*([^*]+)\*\*', body): yield ('B', b.strip())

def main():
    src_root, canon_folder, canon_overview = sys.argv[1], sys.argv[2], sys.argv[3]
    blob = [open(canon_overview,encoding='utf-8').read()]
    for r,d,fs in os.walk(canon_folder):
        for f in fs:
            if f.endswith('.md'): blob.append(open(os.path.join(r,f),encoding='utf-8').read())
    canon_norm = normalize(strip_fm("\n".join(blob)))

    th=tb=0; miss=[]
    for r,d,fs in os.walk(src_root):
        for f in sorted(fs):
            if not f.endswith('.md'): continue
            # 색인·관계도 파일(00.목록·0.관계도)은 변환에서 제외됨 → 대조 대상도 제외
            if re.match(r'^0+[-.]', f) or f.startswith('0.'): continue
            if '등가교환' in f: continue  # 폐기된 Hanesis 레이어 (변환서 EXCLUDE)
            for typ, it in items(strip_fm(open(os.path.join(r,f),encoding='utf-8').read())):
                if not it or is_noise(it): continue
                if typ=='B' and (len(it)<2 or len(it)>40): continue
                if typ=='H': th+=1
                else: tb+=1
                n = normalize(it)
                if len(n)<2: continue
                if n not in canon_norm: miss.append((f,typ,it))
    print(f"[{os.path.basename(canon_folder)}] 헤더 {th} + 굵은명사 {tb} = {th+tb}개 대조 → 진짜 누락 {len(miss)}개")
    for f,typ,it in miss[:80]: print(f"  ❌({typ}) [{f[:32]}] {it}")
    return 1 if miss else 0

if __name__ == "__main__":
    sys.exit(main())
