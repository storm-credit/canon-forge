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
