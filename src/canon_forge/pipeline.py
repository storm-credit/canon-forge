from pathlib import Path
import json
from .inventory import scan
from .extract import extract_file
from .model import save_graph
from .detect import run_detection
from .emit import emit_canon
from .llm import LLMClient, AnthropicRaw

def run(cfg, llm=None) -> dict:
    src = Path(cfg.source_root)
    out = Path(cfg.out_dir); out.mkdir(parents=True, exist_ok=True)
    if llm is None:
        llm = LLMClient(cfg.llm_model, Path(cfg.memory_dir) / "llm", raw=AnthropicRaw())

    # ① inventory
    entries = scan(src)
    (out / "manifest.json").write_text(
        json.dumps(entries, ensure_ascii=False, indent=2), encoding="utf-8")

    # ② extract
    nodes, edges = {}, []
    for e in entries:
        if e["category"] in ("hero", "item", "faction"):
            text = (src / e["path"]).read_text(encoding="utf-8")
            ns, es = extract_file(e["path"], text, e["category"], llm)
            for n in ns:
                nodes[n.id] = n
            edges.extend(es)
    save_graph(out / "graph", nodes, edges)

    # ③ detect
    issues = run_detection(nodes, edges, out)

    # ⑤ emit
    emit_canon(nodes, edges, out / "canon")

    return {
        "files_extracted": len(entries),
        "open_issues": len(issues),
        "converged": len(issues) == 0,
    }
