from pathlib import Path
from canon_forge.config import load_config

def test_load_config(tmp_path):
    (tmp_path / "config.yaml").write_text(
        'source_root: "S"\nslice_glob: "*.md"\nout_dir: "out"\n'
        'memory_dir: ".memory"\nschemas_dir: "schemas"\nllm_model: "m"\n',
        encoding="utf-8",
    )
    cfg = load_config(tmp_path / "config.yaml")
    assert cfg.source_root == "S"
    assert cfg.slice_glob == "*.md"
    assert cfg.out_dir == "out"
    assert cfg.llm_model == "m"
