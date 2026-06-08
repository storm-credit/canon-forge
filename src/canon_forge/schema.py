from dataclasses import asdict
from pathlib import Path
from functools import lru_cache
import json
from jsonschema import Draft7Validator

@lru_cache(maxsize=None)
def _load(schemas_dir: str, category: str):
    p = Path(schemas_dir) / f"{category}.schema.json"
    if not p.exists():
        return None
    return Draft7Validator(json.loads(p.read_text(encoding="utf-8")))

def validate_node(node, schemas_dir: str) -> list:
    v = _load(schemas_dir, node.category)
    if v is None:
        return []  # no schema for this category yet → not an error
    out = []
    for e in v.iter_errors(asdict(node)):
        path = "/".join(str(p) for p in e.absolute_path)
        out.append(f"{path}: {e.message}" if path else e.message)
    return out
