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
