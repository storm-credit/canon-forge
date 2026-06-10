import re, hashlib
from .model import Node, Edge
from .wikilinks import parse_wikilinks

_ALIASES = re.compile(r"aliases:\s*\[([^\]]*)\]")
_H1 = re.compile(r"^#\s+(.+)$", re.MULTILINE)
_RANK = re.compile(r"랭크:\s*(\S+)")

def _slug(category: str, name: str) -> str:
    h = hashlib.sha1(name.encode("utf-8")).hexdigest()[:8]
    return f"{category}:{h}"

def extract_file(rel_path: str, text: str, category: str, llm) -> tuple:
    name_m = _H1.search(text)
    canonical = name_m.group(1).strip() if name_m else rel_path.rsplit("/", 1)[-1][:-3]
    aliases = []
    am = _ALIASES.search(text)
    if am:
        aliases = [a.strip() for a in am.group(1).split(",") if a.strip()]
    node = Node(_slug(category, canonical), category, canonical, aliases, {}, [rel_path])
    rm = _RANK.search(text)
    if rm:
        node.attrs["rank"] = rm.group(1)
    # LLM step: facts/cost (cached by content hash)
    key = hashlib.sha256((category + "::" + text).encode("utf-8")).hexdigest()[:16]
    llm_data = llm.extract_json(key, _prompt(category, text))
    if "cost" in llm_data:
        node.attrs["cost"] = llm_data["cost"]
    edges = [Edge(node.id, t, "links-to", {}, rel_path) for t in parse_wikilinks(text)]
    return [node], edges

def _prompt(category: str, text: str) -> str:
    return (
        f"You extract canon facts from a Korean fantasy worldbuilding markdown file "
        f"(category: {category}). Return ONLY a JSON object. If the entity pays a cost "
        f"(등가교환/대가: lifespan/sanity/memory/body), include "
        f'"cost": {{"type": "...", "amount": "..."}}. Otherwise omit it.\n\n'
        f"FILE:\n{text}"
    )
