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
