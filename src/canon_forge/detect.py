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
