import json
from canon_forge.config import Config
from canon_forge.pipeline import run

class FakeLLM:
    def extract_json(self, cache_key, prompt):
        return {}

def test_pipeline_end_to_end(fixtures_dir, tmp_path):
    cfg = Config(
        source_root=str(fixtures_dir / "vault"),
        slice_glob="**/*.md",
        out_dir=str(tmp_path / "out"),
        memory_dir=str(tmp_path / ".memory"),
        schemas_dir="schemas",
        llm_model="m",
    )
    result = run(cfg, llm=FakeLLM())
    # manifest written for 4 files
    manifest = json.loads((tmp_path / "out" / "manifest.json").read_text(encoding="utf-8"))
    assert len(manifest) == 4
    # graph + collisions + canon produced
    assert (tmp_path / "out" / "graph" / "nodes.json").exists()
    assert (tmp_path / "out" / "collisions.md").exists()
    assert (tmp_path / "out" / "canon").exists()
    # fixture has Skadi listed in hero AND faction archive with different rank -> at least 1 issue
    assert result["open_issues"] >= 1
    assert result["files_extracted"] == 4
    assert result["converged"] is False  # because open issues > 0
