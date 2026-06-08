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
