#!/bin/bash
# SessionStart 훅 — 캐논화 프로젝트
#  ① MkDocs 빌드 의존성 설치 (웹 세션에서 mkdocs build 검증 가능하게)
#  ② 원본 커버리지 현황을 세션 시작 시 자동 출력 ("지금 어디" 까먹음 방지)
set -euo pipefail

PROJ="${CLAUDE_PROJECT_DIR:-$(pwd)}"

# ── ① 의존성 설치 (멱등; 출력 숨김) ──
pip install --quiet mkdocs-material mkdocs-roamlinks-plugin >/dev/null 2>&1 || true

# ── ② 진행 현황 출력 (SessionStart stdout → 세션 컨텍스트로 주입) ──
COV="$PROJ/docs/canon/_커버리지.md"
echo "════════════════════════════════════════════════════"
echo " THE FORGOTTEN SUMMONER 캐논화 — 세션 시작 브리핑"
echo "════════════════════════════════════════════════════"
if [ -f "$COV" ]; then
  todo=$(grep -c '| ⬜ |' "$COV" 2>/dev/null || echo 0)
  done=$(grep -c '| ✅ |' "$COV" 2>/dev/null || echo 0)
  prog=$(grep '세력 진척' "$COV" 2>/dev/null | head -1 | sed 's/\*\*//g' || true)
  echo " 진행 정본: docs/canon/_커버리지.md"
  echo " 완료(✅): ${done}  ·  미완(⬜): ${todo}"
  [ -n "$prog" ] && echo " ${prog}"
else
  echo " ⚠️ _커버리지.md 없음 — 진행 추적 정본 누락 상태"
fi
echo "----------------------------------------------------"
echo " 시작 전 필독:"
echo "   1) docs/canon/_작업프롬프트.md   (원칙·불변식·4단계)"
echo "   2) docs/canon/_커버리지.md       (원본 소비 추적 — 정본)"
echo " 다음 작업 규칙:"
echo "   · _커버리지.md에서 ⬜ 항목 1개 선택"
echo "   · 해당 원본 폴더를 '전수' 통합 (줄이지 말 것, 보일러플레이트만 제거)"
echo "   · 완료 시 그 행을 ✅로, 캐논 산출물 경로 기입"
echo "   · 'Phase 완료'는 그 Phase 모든 행이 ✅일 때만 선언"
echo "════════════════════════════════════════════════════"
