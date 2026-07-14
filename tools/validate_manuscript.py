# -*- coding: utf-8 -*-
"""원고 기계 게이트 (화 단위 1차 방어선, 2026-07-07)

사용: python tools/validate_manuscript.py [원고 폴더|파일]  (기본: 원고/)
검사: 분량 밴드 / 금지 어휘·시스템창 노출 / 클리프행어 휴리스틱 / 프론트매터 상태 / 무협·현대어 표본
통과 조건: 위반 0. 표본 패널(N화마다)과 별개의 상시 게이트.
"""
import glob, io, os, re, sys

TARGET = sys.argv[1] if len(sys.argv) > 1 else '원고'
MIN_CH, MAX_CH = 4600, 6800  # 공백 포함 자수 밴드 (웹소설 표준 규약, 초고 허용 폭)

# 산문 내 금지: 헌법 폐기 어휘 + 게임서사-경계(시스템창·수치 노출) + 무협 + 현대어 표본
BAN = ['우주적 십자가', '잔혹한 대가', '혹독한 대가', 'Epic Penalty', '코스믹 호러',
       '스탯창', '상태창', '시스템 메시지', '레벨업', '경험치를 획득', '스킬을 습득했습니다',
       '알림:', '[시스템]', '퀘스트가 발생', '공격력 +', '방어력 +',
       '기공', '무공', '단전', '무림', '비급', '내공',
       '오케이', 'OK.', '컴퓨터', '스마트', '메커니즘', '시스템적으로', '데이터베이스',
       '성불하', '승천하여 신이', 'Ascension',
       '방각', '방위', '티키타카',  # 시대착오 어휘 (작가 지적 2026-07-14)
       '마이너스', '트랩 브레이커', '퍼센트', '계산기', '볼펜', '노트', '리소스',
       '최적화', '분산 저장', '엔진', '킬로미터', '실시간', '전광판', '타이밍',
       '스카이라인', '카르텔', '캔버스', '데스크', '패턴', '페이지', '직업병', '코인']  # 어휘 전수 검수 승격 (2026-07-14)
NEG = ('아니', '없', '금지', '않')

CLIFF_TAILS = ('.', '?', '!', '—', '…', '"', '”', '’', "'")

def check(path):
    t = io.open(path, encoding='utf-8', errors='ignore').read()
    errs = []
    body = re.sub(r'^---.*?---\s*', '', t, flags=re.S)
    n = len(body)  # 공백 포함 (한국 웹소설 표준 규약)
    # 프론트매터
    if '작가 검토' not in t and '승인' not in t:
        errs.append('프론트매터에 검토 상태 없음')
    # 분량
    if not (MIN_CH <= n <= MAX_CH):
        errs.append(f'분량 이탈: {n}자 (밴드 {MIN_CH}~{MAX_CH})')
    # 금지어
    for b in BAN:
        for m in re.finditer('[^\n]*' + re.escape(b) + '[^\n]*', body):
            if any(x in m.group(0) for x in NEG):
                continue
            errs.append(f'금지 표현: {b} :: {m.group(0).strip()[:50]}')
            break
    # 한자 금지 (작가 판정 2026-07-08: 원고 산문에 한자 병기 금지)
    for m in re.finditer(r'.{0,20}[一-鿿]+.{0,20}', body):
        errs.append(f'한자 노출: …{m.group(0).strip()[:40]}…')
        break
    # 말버릇 과잉 (셈/값 메타포 — 판정 기준 2회, 기계 완충선 6회)
    tic = len(re.findall(r'셈이|셈을|셈은|셈법|값을 매|값이 매|값어치', body))
    if tic > 6:
        errs.append(f"말버릇 과잉: '셈/값' 계열 {tic}회 (완충선 6)")
    # 클리프행어 휴리스틱: 마지막 문단이 정적 서술로 닫히면 경고
    paras = [p.strip() for p in body.strip().split('\n') if p.strip()]
    if paras:
        last = paras[-1]
        static_end = last.endswith('었다.') or last.endswith('였다.') or last.endswith('있었다.')
        has_hook = ('?' in last or '—' in last or '…' in last
                    or any(k in last for k in ('그때', '순간', '하지만', '그러나', '눈앞', '뒤에서', '목소리')))
        if static_end and not has_hook:
            errs.append(f'클리프행어 의심 부재(휴리스틱): 말미 "{last[-40:]}"')
    return n, errs

files = []
if os.path.isfile(TARGET):
    files = [TARGET]
else:
    files = sorted(glob.glob(TARGET + '/**/*화.md', recursive=True))

fail = 0
for p in files:
    n, errs = check(p)
    tag = 'PASS' if not errs else 'FAIL'
    print(f'[{tag}] {os.path.basename(p)} ({n}자)')
    for e in errs:
        print('   -', e)
    fail += len(errs)

print()
print(f'원고 게이트 — {len(files)}화 검사, ' + ('전 항목 통과' if not fail else f'위반 {fail}건'))
sys.exit(1 if fail else 0)
