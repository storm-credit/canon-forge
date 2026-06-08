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
