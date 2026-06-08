from dataclasses import dataclass
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

def load_config(path: Path) -> Config:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return Config(**data)
