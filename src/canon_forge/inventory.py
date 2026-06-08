from pathlib import Path
import hashlib

_RULES = [
    ("01-14", "hero"),
    ("01-19", "item"),
    ("01-8", "faction"),
    ("00. 세계의 틀", "rule"),
]

def category_from_path(rel_path: str) -> str:
    p = rel_path.replace("\\", "/")
    for needle, cat in _RULES:
        if needle in p:
            return cat
    return "unknown"

def scan(root) -> list:
    root = Path(root)
    entries = []
    for f in sorted(root.rglob("*.md")):
        rel = f.relative_to(root).as_posix()
        entries.append({
            "path": rel,
            "sha256": hashlib.sha256(f.read_bytes()).hexdigest(),
            "category": category_from_path(rel),
        })
    return entries
