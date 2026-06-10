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
