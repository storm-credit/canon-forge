# Canon-Forge Engine — Vertical Slice Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the canon-forge consolidation engine end-to-end (inventory → extract → detect → emit → convergence) and prove it converges on a controlled slice, with world-specific invariant checks.

**Architecture:** Deterministic Python pipeline. Mechanical parts (file scan, `[[wikilink]]` parsing, graph build, invariant checks, markdown emit) are pure Python; only fact/cost extraction calls the Claude API, cached to disk by content hash. The knowledge graph is plain JSON (nodes.json + edges.json) — git-friendly, no DB. Unit tests run on synthetic fixtures with the LLM mocked (fast, deterministic); one final integration task runs the real Claude API against the real mini-slice `00. 세계의 틀`.

**Tech Stack:** Python 3.14, pytest 9, `anthropic` SDK 0.84, `jsonschema`, `pyyaml`, `networkx`. Storage: JSON files. Spec: `docs/superpowers/specs/2026-06-08-canon-consolidation-engine-design.md`.

**Scope note:** This plan delivers the engine + Phase-0 schemas for the 3 core categories (hero/item/faction, derived from real vault templates already sampled during brainstorming) + 3 world invariants (item-unique-ownership, identity-multi-presence, cost↔rank). Out of scope (→ later scale-up plans): remaining category schemas via fresh file sampling, cost-monotonic-across-acts invariant, payoff/복선 tracking, full-Astralis scale run, novel-canon-mcp query interface.

---

## File Structure

```
canon-forge/
  pyproject.toml                      # deps + pytest config
  config.yaml                         # source path (read-only), output paths, slice glob
  src/canon_forge/
    __init__.py
    config.py                         # load + validate config.yaml
    wikilinks.py                      # parse [[link]] / [[link|display]]
    inventory.py                      # ① scan dir → manifest entries (path, sha256, category)
    model.py                          # Node, Edge dataclasses + graph load/save (JSON)
    schema.py                         # load per-category JSON Schema, validate nodes
    llm.py                            # Claude wrapper + disk cache (injectable client)
    extract.py                        # ② mechanical + LLM → nodes/edges
    invariants.py                     # world-specific checks → Issue list
    detect.py                         # ③ alias collisions + orphans + invariants → collisions.md
    emit.py                           # ⑤ graph → canon markdown
    pipeline.py                       # orchestrate ①–⑤ + convergence
    cli.py                            # `python -m canon_forge run`
  schemas/                            # Phase-0 output (committed)
    hero.schema.json
    item.schema.json
    faction.schema.json
  tests/
    fixtures/vault/                   # synthetic mini-vault (intentional collisions/costs/husk)
    conftest.py
    test_wikilinks.py test_inventory.py test_model.py test_schema.py
    test_llm.py test_extract.py test_invariants.py test_detect.py
    test_emit.py test_pipeline.py
```

**Core types (defined in Task 3, used everywhere — keep names stable):**
- `Node(id: str, category: str, canonical_name: str, aliases: list[str], attrs: dict, source_files: list[str])`
- `Edge(src: str, dst: str, type: str, attrs: dict, source_file: str)` — `dst` may be an unresolved wikilink target name until resolution.
- `Issue(kind: str, severity: str, message: str, refs: list[str], sources: list[str])`

---

## Task 1: Project skeleton

**Files:**
- Create: `pyproject.toml`, `config.yaml`, `src/canon_forge/__init__.py`, `tests/conftest.py`, `.gitignore`

- [ ] **Step 1: Create `pyproject.toml`**

```toml
[project]
name = "canon-forge"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["anthropic>=0.84", "jsonschema>=4", "pyyaml>=6", "networkx>=3"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]

[tool.setuptools.packages.find]
where = ["src"]
```

- [ ] **Step 2: Create `.gitignore`**

```gitignore
__pycache__/
*.pyc
.memory/
out/
.venv/
```

- [ ] **Step 3: Create `config.yaml`** (real source path is read-only; slice points at the mini-slice for integration)

```yaml
source_root: "C:/ProjectS/loremaker/safe_vault/THE FORGOTTEN SUMMONER"
slice_glob: "00. 세계의 틀/**/*.md"
out_dir: "out"
memory_dir: ".memory"
schemas_dir: "schemas"
llm_model: "claude-sonnet-4-5"
```

- [ ] **Step 4: Create `src/canon_forge/__init__.py`**

```python
__version__ = "0.1.0"
```

- [ ] **Step 5: Create `tests/conftest.py`** (makes fixtures path importable)

```python
from pathlib import Path
import pytest

@pytest.fixture
def fixtures_dir():
    return Path(__file__).parent / "fixtures"
```

- [ ] **Step 6: Verify install + collection**

Run: `python -m pip install -e . && python -m pytest -q`
Expected: installs; pytest reports "no tests ran" (exit 5) — acceptable, no tests yet.

- [ ] **Step 7: Commit**

```bash
git add -A && git commit -m "chore: project skeleton (pyproject, config, gitignore)"
```

---

## Task 2: Config loader

**Files:**
- Create: `src/canon_forge/config.py`, `tests/test_config.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_config.py
from pathlib import Path
from canon_forge.config import load_config

def test_load_config(tmp_path):
    (tmp_path / "config.yaml").write_text(
        'source_root: "S"\nslice_glob: "*.md"\nout_dir: "out"\n'
        'memory_dir: ".memory"\nschemas_dir: "schemas"\nllm_model: "m"\n',
        encoding="utf-8",
    )
    cfg = load_config(tmp_path / "config.yaml")
    assert cfg.source_root == "S"
    assert cfg.slice_glob == "*.md"
    assert cfg.out_dir == "out"
    assert cfg.llm_model == "m"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_config.py -q`
Expected: FAIL — `ModuleNotFoundError: canon_forge.config`

- [ ] **Step 3: Write minimal implementation**

```python
# src/canon_forge/config.py
from dataclasses import dataclass
from pathlib import Path
import yaml

@dataclass
class Config:
    source_root: str
    slice_glob: str
    out_dir: str
    memory_dir: str
    schemas_dir: str
    llm_model: str

def load_config(path: Path) -> Config:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return Config(**data)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_config.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: config loader"
```

---

## Task 3: Core model (Node, Edge, Issue) + graph JSON IO

**Files:**
- Create: `src/canon_forge/model.py`, `tests/test_model.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_model.py
from canon_forge.model import Node, Edge, Issue, save_graph, load_graph

def test_node_roundtrip(tmp_path):
    nodes = {"hero:evan": Node("hero:evan", "hero", "에반", ["Evan"], {"rank": "SSS"}, ["a.md"])}
    edges = [Edge("hero:evan", "item:pendant", "wields", {}, "a.md")]
    save_graph(tmp_path, nodes, edges)
    n2, e2 = load_graph(tmp_path)
    assert n2["hero:evan"].canonical_name == "에반"
    assert n2["hero:evan"].aliases == ["Evan"]
    assert e2[0].type == "wields"
    assert e2[0].dst == "item:pendant"

def test_issue_fields():
    i = Issue("collision", "high", "dup name", ["hero:a", "hero:b"], ["a.md", "b.md"])
    assert i.kind == "collision" and i.severity == "high"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_model.py -q`
Expected: FAIL — `ModuleNotFoundError: canon_forge.model`

- [ ] **Step 3: Write minimal implementation**

```python
# src/canon_forge/model.py
from dataclasses import dataclass, field, asdict
from pathlib import Path
import json

@dataclass
class Node:
    id: str
    category: str
    canonical_name: str
    aliases: list = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    source_files: list = field(default_factory=list)

@dataclass
class Edge:
    src: str
    dst: str
    type: str
    attrs: dict = field(default_factory=dict)
    source_file: str = ""

@dataclass
class Issue:
    kind: str          # collision | orphan | invariant
    severity: str      # high | medium | low
    message: str
    refs: list = field(default_factory=list)
    sources: list = field(default_factory=list)

def save_graph(out_graph_dir, nodes: dict, edges: list):
    d = Path(out_graph_dir); d.mkdir(parents=True, exist_ok=True)
    (d / "nodes.json").write_text(
        json.dumps([asdict(n) for n in nodes.values()], ensure_ascii=False, indent=2),
        encoding="utf-8")
    (d / "edges.json").write_text(
        json.dumps([asdict(e) for e in edges], ensure_ascii=False, indent=2),
        encoding="utf-8")

def load_graph(out_graph_dir):
    d = Path(out_graph_dir)
    nodes = {n["id"]: Node(**n) for n in json.loads((d / "nodes.json").read_text(encoding="utf-8"))}
    edges = [Edge(**e) for e in json.loads((d / "edges.json").read_text(encoding="utf-8"))]
    return nodes, edges
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_model.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: core model (Node/Edge/Issue) + graph JSON io"
```

---

## Task 4: Wikilink parser

**Files:**
- Create: `src/canon_forge/wikilinks.py`, `tests/test_wikilinks.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_wikilinks.py
from canon_forge.wikilinks import parse_wikilinks

def test_parse_plain_and_display():
    text = "에반은 [[적열의 심장 펜던트]]와 [[01-8. 세력|프로스트본 연합]]을 가졌다."
    assert parse_wikilinks(text) == ["적열의 심장 펜던트", "01-8. 세력"]

def test_dedup_and_empty():
    assert parse_wikilinks("[[A]] [[A]]") == ["A"]
    assert parse_wikilinks("no links") == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_wikilinks.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/canon_forge/wikilinks.py
import re

_LINK = re.compile(r"\[\[([^\]]+?)\]\]")

def parse_wikilinks(text: str) -> list:
    out = []
    for raw in _LINK.findall(text):
        target = raw.split("|", 1)[0].strip()
        if target and target not in out:
            out.append(target)
    return out
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_wikilinks.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: wikilink parser"
```

---

## Task 5: Inventory scanner (①)

**Files:**
- Create: `src/canon_forge/inventory.py`, `tests/test_inventory.py`, `tests/fixtures/vault/...`

- [ ] **Step 1: Create synthetic fixture vault**

Create these files (content is minimal; structure drives category detection):

`tests/fixtures/vault/01. 아스트라리스 크로니클/01-14. 영웅 백과/01-14-1. 성장 영웅/스카디.md`:
```markdown
---
aliases: [Skadi, 스카디]
---
# 스카디 아이스블러드 (Skadi Iceblood)
랭크: SSS
소속: [[프로스트본 연합]]
무기: [[적열의 심장 펜던트]]
```

`tests/fixtures/vault/01. 아스트라리스 크로니클/01-8. 세력 아카이브/프로스트본 연합/15. 주요인물/스카디.md`:
```markdown
# 스카디 아이스블러드
랭크: SS
소속: [[프로스트본 연합]]
```

`tests/fixtures/vault/01. 아스트라리스 크로니클/01-19. 아이템 도감/적열의 심장 펜던트.md`:
```markdown
---
aliases: [Pendant of the Red-Heat Heart]
---
# 적열의 심장 펜던트
등급: 신화적유물
소지: [[스카디 아이스블러드]]
```

`tests/fixtures/vault/00. 세계의 틀/00-2. 세계의 작동 원리.md`:
```markdown
# 세계의 작동 원리
모든 마법은 시전자의 수명을 대가로 한다.
```

- [ ] **Step 2: Write the failing test**

```python
# tests/test_inventory.py
from canon_forge.inventory import scan, category_from_path

def test_category_from_path():
    assert category_from_path("01. 아스트라리스 크로니클/01-14. 영웅 백과/x.md") == "hero"
    assert category_from_path("01. 아스트라리스 크로니클/01-19. 아이템 도감/y.md") == "item"
    assert category_from_path("01. 아스트라리스 크로니클/01-8. 세력 아카이브/z.md") == "faction"
    assert category_from_path("00. 세계의 틀/00-2.md") == "rule"
    assert category_from_path("misc/other.md") == "unknown"

def test_scan(fixtures_dir):
    entries = scan(fixtures_dir / "vault")
    assert len(entries) == 4
    cats = sorted(e["category"] for e in entries)
    assert cats == ["faction", "hero", "item", "rule"]
    for e in entries:
        assert len(e["sha256"]) == 64 and e["path"]
```

- [ ] **Step 3: Run test to verify it fails**

Run: `python -m pytest tests/test_inventory.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 4: Write minimal implementation**

```python
# src/canon_forge/inventory.py
from pathlib import Path
import hashlib

_RULES = [
    ("01-14", "hero"),
    ("01-19", "item"),
    ("01-8", "faction"),
    ("00. 세계의 틀", "rule"),
]

def category_from_path(rel_path: str) -> str:
    p = rel_path.replace("\\", "/")
    for needle, cat in _RULES:
        if needle in p:
            return cat
    return "unknown"

def scan(root) -> list:
    root = Path(root)
    entries = []
    for f in sorted(root.rglob("*.md")):
        rel = f.relative_to(root).as_posix()
        entries.append({
            "path": rel,
            "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
            "category": category_from_path(rel),
        })
    return entries
```

- [ ] **Step 5: Run test to verify it passes**

Run: `python -m pytest tests/test_inventory.py -q`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat: inventory scanner + synthetic fixture vault"
```

---

## Task 6: Phase-0 category schemas + validator

**Files:**
- Create: `schemas/hero.schema.json`, `schemas/item.schema.json`, `schemas/faction.schema.json`, `src/canon_forge/schema.py`, `tests/test_schema.py`

- [ ] **Step 1: Create `schemas/item.schema.json`** (derived from real vault item model — ownership/set/tier)

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "item",
  "type": "object",
  "required": ["id", "category", "canonical_name"],
  "properties": {
    "id": {"type": "string"},
    "category": {"const": "item"},
    "canonical_name": {"type": "string"},
    "aliases": {"type": "array", "items": {"type": "string"}},
    "attrs": {
      "type": "object",
      "properties": {
        "tier": {"enum": ["신화적유물", "전설", "유물", "일반"]},
        "type": {"type": "string"}
      }
    }
  }
}
```

- [ ] **Step 2: Create `schemas/hero.schema.json`**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "hero",
  "type": "object",
  "required": ["id", "category", "canonical_name"],
  "properties": {
    "id": {"type": "string"},
    "category": {"const": "hero"},
    "canonical_name": {"type": "string"},
    "aliases": {"type": "array", "items": {"type": "string"}},
    "attrs": {
      "type": "object",
      "properties": {
        "rank": {"type": "string"},
        "identity_of": {"type": "string"}
      }
    }
  }
}
```

- [ ] **Step 3: Create `schemas/faction.schema.json`**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "faction",
  "type": "object",
  "required": ["id", "category", "canonical_name"],
  "properties": {
    "id": {"type": "string"},
    "category": {"const": "faction"},
    "canonical_name": {"type": "string"},
    "aliases": {"type": "array", "items": {"type": "string"}},
    "attrs": {
      "type": "object",
      "properties": {"power_type": {"type": "string"}}
    }
  }
}
```

- [ ] **Step 4: Write the failing test**

```python
# tests/test_schema.py
from canon_forge.model import Node
from canon_forge.schema import validate_node

def test_valid_item():
    n = Node("item:p", "item", "펜던트", [], {"tier": "신화적유물"}, ["x.md"])
    assert validate_node(n, "schemas") == []

def test_invalid_item_tier():
    n = Node("item:p", "item", "펜던트", [], {"tier": "전설급오타"}, ["x.md"])
    errs = validate_node(n, "schemas")
    assert errs and any("tier" in e for e in errs)
```

- [ ] **Step 5: Run test to verify it fails**

Run: `python -m pytest tests/test_schema.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 6: Write minimal implementation**

```python
# src/canon_forge/schema.py
from dataclasses import asdict
from pathlib import Path
from functools import lru_cache
import json
from jsonschema import Draft7Validator

@lru_cache(maxsize=None)
def _load(schemas_dir: str, category: str):
    p = Path(schemas_dir) / f"{category}.schema.json"
    if not p.exists():
        return None
    return Draft7Validator(json.loads(p.read_text(encoding="utf-8")))

def validate_node(node, schemas_dir: str) -> list:
    v = _load(schemas_dir, node.category)
    if v is None:
        return []  # no schema for this category yet → not an error
    return [e.message for e in v.iter_errors(asdict(node))]
```

- [ ] **Step 7: Run test to verify it passes**

Run: `python -m pytest tests/test_schema.py -q`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add -A && git commit -m "feat: Phase-0 category schemas (hero/item/faction) + validator"
```

---

## Task 7: LLM wrapper with disk cache

**Files:**
- Create: `src/canon_forge/llm.py`, `tests/test_llm.py`

- [ ] **Step 1: Write the failing test** (fake client → no network; verify cache hit)

```python
# tests/test_llm.py
from canon_forge.llm import LLMClient

class FakeRaw:
    def __init__(self): self.calls = 0
    def complete(self, model, prompt):
        self.calls += 1
        return '{"ok": true}'

def test_cache_avoids_second_call(tmp_path):
    raw = FakeRaw()
    c = LLMClient(model="m", cache_dir=tmp_path, raw=raw)
    a = c.extract_json("hash1", "prompt text")
    b = c.extract_json("hash1", "prompt text")
    assert a == {"ok": True} == b
    assert raw.calls == 1  # second call served from disk cache
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_llm.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/canon_forge/llm.py
from pathlib import Path
import json

class AnthropicRaw:
    """Real Claude client. Imported lazily so tests need no API key."""
    def __init__(self, api_key=None):
        import anthropic
        self._c = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
    def complete(self, model: str, prompt: str) -> str:
        msg = self._c.messages.create(
            model=model, max_tokens=4096,
            messages=[{"role": "user", "content": prompt}])
        return "".join(b.text for b in msg.content if b.type == "text")

class LLMClient:
    def __init__(self, model: str, cache_dir, raw=None):
        self.model = model
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.raw = raw  # inject real AnthropicRaw in production; fake in tests

    def extract_json(self, cache_key: str, prompt: str) -> dict:
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            return json.loads(cache_file.read_text(encoding="utf-8"))
        text = self.raw.complete(self.model, prompt)
        data = json.loads(text)
        cache_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return data
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_llm.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: LLM wrapper with disk cache (injectable client)"
```

---

## Task 8: Extraction (②) — mechanical + LLM

**Files:**
- Create: `src/canon_forge/extract.py`, `tests/test_extract.py`

- [ ] **Step 1: Write the failing test** (LLM faked; verify node id, aliases, wikilink edges, llm-supplied cost)

```python
# tests/test_extract.py
from canon_forge.extract import extract_file

class FakeLLM:
    def extract_json(self, cache_key, prompt):
        return {"cost": {"type": "lifespan", "amount": "수개월"}}

def test_extract_hero_node_and_edges():
    text = ("---\naliases: [Skadi, 스카디]\n---\n# 스카디 아이스블러드\n"
            "랭크: SSS\n소속: [[프로스트본 연합]]\n무기: [[적열의 심장 펜던트]]\n")
    nodes, edges = extract_file("01-14. 영웅 백과/스카디.md", text, "hero", FakeLLM())
    assert len(nodes) == 1
    n = nodes[0]
    assert n.category == "hero"
    assert n.canonical_name == "스카디 아이스블러드"
    assert "Skadi" in n.aliases and "스카디" in n.aliases
    assert n.attrs["rank"] == "SSS"
    assert n.attrs["cost"] == {"type": "lifespan", "amount": "수개월"}
    targets = sorted(e.dst for e in edges)
    assert targets == ["적열의 심장 펜던트", "프로스트본 연합"]
    assert all(e.src == n.id for e in edges)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_extract.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/canon_forge/extract.py
import re, hashlib
from .model import Node, Edge
from .wikilinks import parse_wikilinks

_ALIASES = re.compile(r"aliases:\s*\[([^\]]*)\]")
_H1 = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_RANK = re.compile(r"랭크:\s*(\S+)")

def _slug(category: str, name: str) -> str:
    h = hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]
    return f"{category}:{h}"

def extract_file(rel_path: str, text: str, category: str, llm) -> tuple:
    name_m = _H1.search(text)
    canonical = name_m.group(1).strip() if name_m else rel_path.rsplit("/", 1)[-1][:-3]
    # strip parenthetical English from canonical for the display name, keep full as alias
    aliases = []
    am = _ALIASES.search(text)
    if am:
        aliases = [a.strip() for a in am.group(1).split(",") if a.strip()]
    node = Node(_slug(category, canonical), category, canonical, aliases, {}, [rel_path])
    rm = _RANK.search(text)
    if rm:
        node.attrs["rank"] = rm.group(1)
    # LLM step: facts/cost (cached by content hash)
    key = hashlib.sha256((category + "::" + text).encode("utf-8")).hexdigest()[:16]
    llm_data = llm.extract_json(key, _prompt(category, text))
    if "cost" in llm_data:
        node.attrs["cost"] = llm_data["cost"]
    edges = [Edge(node.id, t, "links-to", {}, rel_path) for t in parse_wikilinks(text)]
    return [node], edges

def _prompt(category: str, text: str) -> str:
    return (
        f"You extract canon facts from a Korean fantasy worldbuilding markdown file "
        f"(category: {category}). Return ONLY a JSON object. If the entity pays a cost "
        f"(등가교환/대가: lifespan/sanity/memory/body), include "
        f'"cost": {{"type": "...", "amount": "..."}}. Otherwise omit it.\n\n'
        f"FILE:\n{text}"
    )
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_extract.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: extraction (mechanical template+wikilink + LLM cost/facts)"
```

---

## Task 9: World invariants (③ core)

**Files:**
- Create: `src/canon_forge/invariants.py`, `tests/test_invariants.py`

Implements three invariants from spec §8:
1. **item unique ownership** — a 신화적유물 owned by 2+ distinct owners simultaneously = contradiction.
2. **identity multi-presence** — a non-Evan character present in 2+ locations same act = contradiction; Evan husks (`attrs.identity_of == "에반"` or `is-husk-of` edge) are exempt.
3. **cost↔rank** — a rank-D entity carrying a lifespan cost = contradiction (cost must scale with rank).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_invariants.py
from canon_forge.model import Node, Edge
from canon_forge.invariants import check_item_unique_ownership, check_identity_multipresence, check_cost_rank

def _node(id, cat, name, attrs=None):
    return Node(id, cat, name, [], attrs or {}, ["x.md"])

def test_item_two_owners_is_contradiction():
    nodes = {
        "item:p": _node("item:p", "item", "펜던트", {"tier": "신화적유물"}),
        "hero:a": _node("hero:a", "hero", "A"), "hero:b": _node("hero:b", "hero", "B"),
    }
    edges = [Edge("hero:a", "item:p", "owns", {"state": "현소지"}, "a.md"),
             Edge("hero:b", "item:p", "owns", {"state": "현소지"}, "b.md")]
    issues = check_item_unique_ownership(nodes, edges)
    assert len(issues) == 1 and issues[0].kind == "invariant"

def test_evan_husk_multipresence_is_allowed():
    nodes = {
        "hero:evan": _node("hero:evan", "hero", "에반", {"identity_of": "에반"}),
        "hero:khalid": _node("hero:khalid", "hero", "칼리드"),
    }
    edges = [
        Edge("hero:evan", "loc:1", "present-at", {"act": "1"}, "a.md"),
        Edge("hero:evan", "loc:2", "present-at", {"act": "1"}, "b.md"),
        Edge("hero:khalid", "loc:1", "present-at", {"act": "1"}, "a.md"),
        Edge("hero:khalid", "loc:2", "present-at", {"act": "1"}, "b.md"),
    ]
    issues = check_identity_multipresence(nodes, edges)
    # evan exempt, khalid flagged
    assert len(issues) == 1 and "칼리드" in issues[0].message

def test_cost_rank_d_with_lifespan_is_contradiction():
    nodes = {"hero:d": _node("hero:d", "hero", "D급영웅", {"rank": "D", "cost": {"type": "lifespan"}})}
    issues = check_cost_rank(nodes)
    assert len(issues) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_invariants.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/canon_forge/invariants.py
from collections import defaultdict
from .model import Issue

def check_item_unique_ownership(nodes, edges):
    issues = []
    owners = defaultdict(set)
    for e in edges:
        if e.type == "owns" and e.attrs.get("state") == "현소지":
            owners[e.dst].add(e.src)
    for item_id, owner_ids in owners.items():
        item = nodes.get(item_id)
        if item and item.attrs.get("tier") == "신화적유물" and len(owner_ids) > 1:
            issues.append(Issue(
                "invariant", "high",
                f"신화적유물 '{item.canonical_name}'이 동시에 {len(owner_ids)}인 소지",
                [item_id, *sorted(owner_ids)],
                sorted({nodes[o].source_files[0] for o in owner_ids if o in nodes})))
    return issues

def _is_evan_avatar(node, edges):
    if node.attrs.get("identity_of") == "에반":
        return True
    return any(e.src == node.id and e.type == "is-husk-of" for e in edges)

def check_identity_multipresence(nodes, edges):
    issues = []
    presence = defaultdict(lambda: defaultdict(set))  # char -> act -> locations
    for e in edges:
        if e.type == "present-at":
            presence[e.src][e.attrs.get("act", "?")].add(e.dst)
    for char_id, by_act in presence.items():
        node = nodes.get(char_id)
        if node is None or _is_evan_avatar(node, edges):
            continue
        for act, locs in by_act.items():
            if len(locs) > 1:
                issues.append(Issue(
                    "invariant", "high",
                    f"'{node.canonical_name}'이 act {act}에 {len(locs)}곳 동시 존재(분신 아님)",
                    [char_id], node.source_files))
    return issues

def check_cost_rank(nodes):
    issues = []
    for nid, n in nodes.items():
        cost = n.attrs.get("cost")
        if n.attrs.get("rank") == "D" and isinstance(cost, dict) and cost.get("type") == "lifespan":
            issues.append(Issue(
                "invariant", "medium",
                f"'{n.canonical_name}'은 D급인데 수명 대가 보유(등급↔대가 불일치)",
                [nid], n.source_files))
    return issues

def run_all(nodes, edges):
    return (check_item_unique_ownership(nodes, edges)
            + check_identity_multipresence(nodes, edges)
            + check_cost_rank(nodes))
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_invariants.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: world invariants (item ownership, identity, cost-rank)"
```

---

## Task 10: Detection (③) — alias collisions + orphans + invariants → collisions.md

**Files:**
- Create: `src/canon_forge/detect.py`, `tests/test_detect.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_detect.py
from canon_forge.model import Node, Edge
from canon_forge.detect import detect_alias_collisions, detect_orphans, run_detection

def _n(id, cat, name, aliases=None):
    return Node(id, cat, name, aliases or [], {}, [f"{id}.md"])

def test_alias_collision_same_name_diff_category():
    nodes = {"hero:s": _n("hero:s", "hero", "스카디"),
             "spirit:s": _n("spirit:s", "spirit", "스카디")}
    issues = detect_alias_collisions(nodes)
    assert len(issues) == 1 and issues[0].kind == "collision"

def test_orphan_edge_to_missing_node():
    nodes = {"hero:a": _n("hero:a", "hero", "A")}
    edges = [Edge("hero:a", "프로스트본 연합", "links-to", {}, "a.md")]
    issues = detect_orphans(nodes, edges)
    assert len(issues) == 1 and issues[0].kind == "orphan"

def test_run_detection_writes_collisions_md(tmp_path):
    nodes = {"hero:s": _n("hero:s", "hero", "스카디"),
             "spirit:s": _n("spirit:s", "spirit", "스카디")}
    issues = run_detection(nodes, [], tmp_path)
    text = (tmp_path / "collisions.md").read_text(encoding="utf-8")
    assert "스카디" in text and "미해결" in text
    assert len(issues) == 1
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_detect.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/canon_forge/detect.py
from collections import defaultdict
from pathlib import Path
from .model import Issue
from .invariants import run_all as run_invariants

def detect_alias_collisions(nodes):
    """Same surface name across nodes with differing category = potential merge/collision."""
    issues = []
    by_name = defaultdict(list)
    for n in nodes.values():
        for key in {n.canonical_name, *n.aliases}:
            by_name[key].append(n)
    for name, group in by_name.items():
        cats = {n.category for n in group}
        if len(group) > 1 and len(cats) > 1:
            issues.append(Issue(
                "collision", "high",
                f"'{name}'이 서로 다른 카테고리 {sorted(cats)}로 중복",
                [n.id for n in group],
                sorted({n.source_files[0] for n in group})))
    return issues

def detect_orphans(nodes, edges):
    names = set(nodes)
    surface = {nm for n in nodes.values() for nm in {n.canonical_name, *n.aliases}}
    issues = []
    for e in edges:
        if e.dst not in names and e.dst not in surface:
            issues.append(Issue(
                "orphan", "medium",
                f"엣지 대상 '{e.dst}'이 정의되지 않음(link-rot/미정의)",
                [e.src, e.dst], [e.source_file]))
    return issues

def run_detection(nodes, edges, out_dir) -> list:
    issues = (detect_alias_collisions(nodes)
              + detect_orphans(nodes, edges)
              + run_invariants(nodes, edges))
    _write_collisions_md(issues, out_dir)
    return issues

def _write_collisions_md(issues, out_dir):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    lines = [f"# 미해결 열린 이슈: {len(issues)}", ""]
    for i in issues:
        lines.append(f"- **[{i.kind}/{i.severity}]** {i.message}  "
                     f"\n  refs: {', '.join(i.refs)}  \n  sources: {', '.join(i.sources)}")
    (out / "collisions.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_detect.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: detection (alias collisions + orphans + invariants) -> collisions.md"
```

---

## Task 11: Emit (⑤) — graph → canon markdown

**Files:**
- Create: `src/canon_forge/emit.py`, `tests/test_emit.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_emit.py
from canon_forge.model import Node, Edge
from canon_forge.emit import emit_canon

def test_emit_writes_one_md_per_node(tmp_path):
    nodes = {"hero:s": Node("hero:s", "hero", "스카디", ["Skadi"], {"rank": "SSS"}, ["a.md"])}
    edges = [Edge("hero:s", "item:p", "wields", {}, "a.md")]
    emit_canon(nodes, edges, tmp_path)
    f = tmp_path / "hero" / "스카디.md"
    assert f.exists()
    body = f.read_text(encoding="utf-8")
    assert "# 스카디" in body and "Skadi" in body and "rank" in body and "wields" in body
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_emit.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/canon_forge/emit.py
from collections import defaultdict
from pathlib import Path

def _safe(name: str) -> str:
    return "".join(c for c in name if c not in '\\/:*?"<>|').strip() or "untitled"

def emit_canon(nodes, edges, canon_dir):
    out = Path(canon_dir)
    out_edges = defaultdict(list)
    for e in edges:
        out_edges[e.src].append(e)
    for nid, n in nodes.items():
        d = out / n.category
        d.mkdir(parents=True, exist_ok=True)
        lines = [f"# {n.canonical_name}", ""]
        if n.aliases:
            lines.append(f"*별칭: {', '.join(n.aliases)}*\n")
        for k, v in n.attrs.items():
            lines.append(f"- **{k}**: {v}")
        rels = out_edges.get(nid, [])
        if rels:
            lines.append("\n## 관계")
            for e in rels:
                lines.append(f"- {e.type} → {e.dst}")
        lines.append(f"\n<!-- sources: {', '.join(n.source_files)} -->")
        (d / f"{_safe(n.canonical_name)}.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_emit.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: emit canon markdown from graph"
```

---

## Task 12: Pipeline orchestration + convergence

**Files:**
- Create: `src/canon_forge/pipeline.py`, `tests/test_pipeline.py`

- [ ] **Step 1: Write the failing test** (end-to-end on fixture vault, LLM faked)

```python
# tests/test_pipeline.py
import json
from canon_forge.config import Config
from canon_forge.pipeline import run

class FakeLLM:
    def extract_json(self, cache_key, prompt):
        return {}

def test_pipeline_end_to_end(fixtures_dir, tmp_path):
    cfg = Config(
        source_root=str(fixtures_dir / "vault"),
        slice_glob="**/*.md",
        out_dir=str(tmp_path / "out"),
        memory_dir=str(tmp_path / ".memory"),
        schemas_dir="schemas",
        llm_model="m",
    )
    result = run(cfg, llm=FakeLLM())
    # manifest written for 4 files
    manifest = json.loads((tmp_path / "out" / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest) == 4
    # graph + collisions + canon produced
    assert (tmp_path / "out" / "graph" / "nodes.json").exists()
    assert (tmp_path / "out" / "collisions.md").exists()
    assert (tmp_path / "out" / "canon").exists()
    # fixture has Skadi listed in hero AND faction archive with different rank -> at least 1 issue
    assert result["open_issues"] >= 1
    assert result["files_extracted"] == 4
    assert result["converged"] is False  # because open issues > 0
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_pipeline.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/canon_forge/pipeline.py
from pathlib import Path
import json
from .inventory import scan
from .extract import extract_file
from .model import save_graph
from .detect import run_detection
from .emit import emit_canon
from .llm import LLMClient, AnthropicRaw

def run(cfg, llm=None) -> dict:
    src = Path(cfg.source_root)
    out = Path(cfg.out_dir); out.mkdir(parents=True, exist_ok=True)
    if llm is None:
        llm = LLMClient(cfg.llm_model, Path(cfg.memory_dir) / "llm", raw=AnthropicRaw())

    # ① inventory
    entries = scan(src)
    (out / "manifest.json").write_text(
        json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")

    # ② extract
    nodes, edges = {}, []
    for e in entries:
        if e["category"] in ("hero", "item", "faction"):
            text = (src / e["path"]).read_text(encoding="utf-8")
            ns, es = extract_file(e["path"], text, e["category"], llm)
            for n in ns:
                nodes[n.id] = n
            edges.extend(es)
    save_graph(out / "graph", nodes, edges)

    # ③ detect
    issues = run_detection(nodes, edges, out)

    # ⑤ emit
    emit_canon(nodes, edges, out / "canon")

    return {
        "files_extracted": len(entries),
        "open_issues": len(issues),
        "converged": len(issues) == 0,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_pipeline.py -q`
Expected: PASS

- [ ] **Step 5: Run the full suite**

Run: `python -m pytest -q`
Expected: PASS (all tests across all modules)

- [ ] **Step 6: Commit**

```bash
git add -A && git commit -m "feat: pipeline orchestration + convergence report"
```

---

## Task 13: CLI entry point

**Files:**
- Create: `src/canon_forge/cli.py`, `src/canon_forge/__main__.py`, `tests/test_cli.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_cli.py
from canon_forge.cli import main

def test_cli_run_prints_report(fixtures_dir, tmp_path, capsys, monkeypatch):
    cfgfile = tmp_path / "config.yaml"
    cfgfile.write_text(
        f'source_root: "{(fixtures_dir / "vault").as_posix()}"\n'
        f'slice_glob: "**/*.md"\n'
        f'out_dir: "{(tmp_path / "out").as_posix()}"\n'
        f'memory_dir: "{(tmp_path / ".memory").as_posix()}"\n'
        f'schemas_dir: "schemas"\nllm_model: "m"\n',
        encoding="utf-8")
    rc = main(["run", "--config", str(cfgfile), "--fake-llm"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "open_issues" in out and "converged" in out
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cli.py -q`
Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Write minimal implementation**

```python
# src/canon_forge/cli.py
import argparse, json
from .config import load_config
from .pipeline import run

class _FakeLLM:
    def extract_json(self, cache_key, prompt):
        return {}

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="canon-forge")
    sub = parser.add_subparsers(dest="cmd", required=True)
    runp = sub.add_parser("run")
    runp.add_argument("--config", default="config.yaml")
    runp.add_argument("--fake-llm", action="store_true", help="skip API; for dry runs/tests")
    args = parser.parse_args(argv)
    if args.cmd == "run":
        cfg = load_config(args.config)
        report = run(cfg, llm=_FakeLLM() if args.fake_llm else None)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    return 1
```

```python
# src/canon_forge/__main__.py
import sys
from .cli import main
sys.exit(main())
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_cli.py -q`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add -A && git commit -m "feat: CLI entry point (run --config --fake-llm)"
```

---

## Task 14: Integration run on real mini-slice (verification)

**Files:**
- Modify: `config.yaml` (already points at real source + `00. 세계의 틀`)
- Create: `docs/INTEGRATION_NOTES.md`

This task uses the REAL Claude API against the REAL vault mini-slice. It is a verification task, not unit-tested. The `00. 세계의 틀` files are category `rule` (not hero/item/faction), so they will be inventoried but produce no extracted entity nodes yet — the purpose here is to confirm ①+③+⑤ run cleanly against real files end-to-end and the manifest/outputs are well-formed.

- [ ] **Step 1: Dry-run with fake LLM against the real mini-slice**

Run: `python -m canon_forge run --config config.yaml --fake-llm`
Expected: prints JSON report; `out/manifest.json` lists the real `00. 세계의 틀` files; `out/collisions.md` exists. Confirm no crash and paths resolve.

- [ ] **Step 2: Confirm the source vault was not modified**

Run: `cd "C:/ProjectS/loremaker/safe_vault" && git status --porcelain`
Expected: empty output (engine touched nothing in the source).

- [ ] **Step 3: Real API smoke test on ONE hero file** (temporarily widen the slice)

Edit `config.yaml`: set `slice_glob: "01. 아스트라리스 크로니클/01-14. 영웅 백과/01-14-1. 성장 영웅/**/스카디*.md"` (or any single existing hero file — confirm the path with a directory listing first).
Ensure `ANTHROPIC_API_KEY` is set in the environment.
Run: `python -m canon_forge run --config config.yaml`
Expected: report prints; `out/graph/nodes.json` contains ≥1 hero node with a `cost` attr populated by the real LLM; `.memory/llm/` contains a cache file. Re-running is instant (cache hit).

- [ ] **Step 4: Record findings**

Create `docs/INTEGRATION_NOTES.md` capturing: real file count in mini-slice, any extraction surprises, real-vault category-detection accuracy, LLM cost/latency for one file, and any schema mismatches found against real data (feeds the next scale-up plan's Phase-0 refinement).

- [ ] **Step 5: Reset `config.yaml` back to the safe mini-slice and commit**

```bash
git checkout config.yaml 2>/dev/null || true   # or manually restore slice_glob to "00. 세계의 틀/**/*.md"
git add -A && git commit -m "test: integration run on real mini-slice + notes"
```

---

## Self-Review

**Spec coverage:**
- §6 pipeline ①–⑤ → Tasks 5 (①), 8 (②), 9–10 (③), 11 (⑤), 12 (orchestration). ✅
- §7/§7.1 graph model + per-category schemas → Tasks 3 (model), 6 (schemas). ✅
- §8 invariants: item ownership, identity multi-presence, cost↔rank → Task 9. ✅ (cost-monotonic-across-acts + payoff/복선 explicitly deferred to scale-up — stated in Scope note, not silent.)
- §9 convergence → Task 12 (`converged` flag). ✅
- §11 outputs (manifest/graph/canon/collisions/.memory) → Tasks 12 (manifest/graph/canon/collisions), 7 (.memory llm cache). ✅
- §4 read-only source → Task 14 Step 2 verifies no source mutation. ✅
- §13 build order Phase 0 → mini-slice → Tasks 6 (schemas) + 14 (real mini-slice). Faction-subtree + full Astralis = next plans. ✅
- LLM caching/resume (Karpathy, anti-rework) → Task 7. ✅

**Placeholder scan:** No TBD/TODO. Every code step has complete runnable code. Deferred items are explicitly named in the Scope note, not hidden.

**Type consistency:** `Node`/`Edge`/`Issue` defined in Task 3 with field names (`id`, `category`, `canonical_name`, `aliases`, `attrs`, `source_files` / `src`, `dst`, `type`, `attrs`, `source_file` / `kind`, `severity`, `message`, `refs`, `sources`) used consistently in Tasks 8–12. `LLMClient.extract_json(cache_key, prompt)` signature (Task 7) matches all fake LLMs and the `extract_file(..., llm)` call (Task 8). `run(cfg, llm=None)` signature consistent across Tasks 12–13. `run_detection(nodes, edges, out_dir)` consistent Tasks 10, 12.

**Known follow-ups for scale-up plan:** node-id collisions from sha1(name) if two categories share a name (currently namespaced by category prefix, acceptable for v1); alias-driven entity *merging* (this plan only *detects* collisions, doesn't auto-merge); resolution loop (④) persistence of human decisions to `.memory`.
