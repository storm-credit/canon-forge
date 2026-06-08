from canon_forge.model import Node
from canon_forge.schema import validate_node

def test_valid_item():
    n = Node("item:p", "item", "펜던트", [], {"tier": "신화적유물"}, ["x.md"])
    assert validate_node(n, "schemas") == []

def test_invalid_item_tier():
    n = Node("item:p", "item", "펜던트", [], {"tier": "전설급오타"}, ["x.md"])
    errs = validate_node(n, "schemas")
    assert errs and any("tier" in e for e in errs)
