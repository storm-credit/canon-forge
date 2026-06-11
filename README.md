# canon-forge

`THE FORGOTTEN SUMMONER` 세계관 볼트(원본 ~37MB, ~4041 md)를 **깨끗하고 일관되며 질의 가능한 캐논**으로 정리(consolidate)하는 Python 엔진.

> ⚠️ **확장(expansion)이 아니라 정리(consolidation)다.** 목표는 *작아지고, 모순이 0으로 수렴하고, 끝이 있는* 캐논. 크기를 키우는 게 아니다. (이전 3개월 "확장 트레드밀" 실패에서 방향 전환한 결과 — 자세한 배경은 스펙 참고.)

## 무엇을 하나

```
[원본 볼트 · 읽기전용]
   │
 ① 인벤토리   → 전 파일 스캔(경로·해시·카테고리)
 ② 추출       → 위키링크 [[..]] 기계 파싱 + LLM(사실·대가) 추출, 해시 캐싱
 ③ 검출       → 모순 · 고아 · 이름증식 · 세계 불변식 위반  →  collisions.md
 ④ 해소       → (스케일업 예정)
 ⑤ emit       → 정리·보강된 캐논 마크다운
```

**산출물은 5개로 제한**(반-의식 원칙): `out/manifest.json`, `out/graph/`, `out/canon/`, `out/collisions.md`, `.memory/`.
**수렴 정의:** 추출완료 ∧ 모순0 ∧ 개연성구멍0 ∧ 고아0. (실측: 전체 Astralis = **17,364 열린 이슈**.)

세계 고유 불변식: 대가(등가교환) 단조누적 / 등급↔대가 정합 / 에반 분신(무의식 껍데기) 다중존재 허용·그 외 모순 / 신화 유물 단일소유.

## 실행

```bash
pip install -e .
# 비용 0 드라이런 (LLM 호출 안 함):
python -m canon_forge run --config config.yaml --fake-llm
# 실제 추출 (Vertex AI):
python -m canon_forge run --config config.yaml
```

`config.yaml`:
- `source_root` — 원본 볼트(읽기전용)
- `slice_glob` — 처리 범위. **비용/스코프를 이걸로 제한**(예: `"00. 세계의 틀/**/*.md"`)
- `provider` — `vertex`(기본) | `anthropic`
- LLM = **Vertex AI**, [`gemini-client`](../gemini-client-module) 모듈의 `create_client` 위임. SA키: `vertex_sa_key` 경로(레포에 키 자체는 없음).

## 테스트

```bash
python -m pytest -q        # 23 passing
```
단위 테스트는 합성 픽스처(`tests/fixtures/`) + LLM 목 → 네트워크/키 불필요·결정적.

## 상태 (2026-06-08)

✅ 수직 슬라이스 완료: 엔진 ①~③·⑤ + Vertex provider, 23 테스트 green.

**남은 일 (스케일업):**
1. 실API 스모크 — `seasonXI/vertex-sa-key.json`로 hero 1개 실추출 (계획 Task 14 step3)
2. 다중출처 인물 dedup (영웅백과 vs 세력 아카이브 = #1 난제) → 전체 Astralis
3. ④ 해소 루프 영속, 복선/payoff 추적, 나머지 카테고리 스키마 도출

## 문서

- 설계 스펙: [`docs/superpowers/specs/2026-06-08-canon-consolidation-engine-design.md`](docs/superpowers/specs/2026-06-08-canon-consolidation-engine-design.md)
- 구현 계획: [`docs/superpowers/plans/2026-06-08-canon-forge-engine-vertical-slice.md`](docs/superpowers/plans/2026-06-08-canon-forge-engine-vertical-slice.md)

## 다운스트림

정리된 캐논은 **openending**(독자 선택형 분기 리더 — 읽는 사람마다 다른 결말)의 토대가 된다. 본 레포 범위 아님.
