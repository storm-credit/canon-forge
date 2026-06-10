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
