from dataclasses import dataclass, fields
from pathlib import Path
import yaml

@dataclass
class Config:
    source_root: str
    slice_glob: str
    out_dir: str
    memory_dir: str
    schemas_dir: str
    llm_model: str
    provider: str = "anthropic"          # "anthropic" | "vertex"
    llm_max_tokens: int = 16384          # output token budget; 16K fits most extractions
    vertex_sa_key: str = ""              # path to service-account JSON (project_id read from it)
    vertex_project: str = ""             # fallback if no SA key
    vertex_location: str = "us-central1"

def load_config(path: Path) -> Config:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    known = {f.name for f in fields(Config)}
    return Config(**{k: v for k, v in data.items() if k in known})
