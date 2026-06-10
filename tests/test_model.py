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
