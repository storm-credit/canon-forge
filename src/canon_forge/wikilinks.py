import re

_LINK = re.compile(r"\[\[([^\]]+?)\]\]")

def parse_wikilinks(text: str) -> list:
    out = []
    for raw in _LINK.findall(text):
        target = raw.split("|", 1)[0].strip()
        if target and target not in out:
            out.append(target)
    return out
