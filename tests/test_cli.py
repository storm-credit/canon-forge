from canon_forge.cli import main

def test_cli_run_prints_report(fixtures_dir, tmp_path, capsys, monkeypatch):
    cfgfile = tmp_path / "config.yaml"
    cfgfile.write_text(
        f'source_root: "{(fixtures_dir / "vault").as_posix()}"\n'
        f'slice_glob: "**/*.md"\n'
        f'out_dir: "{(tmp_path / "out").as_posix()}"\n'
        f'memory_dir: "{(tmp_path / ".memory").as_posix()}"\n'
        f'schemas_dir: "schemas"\nllm_model: "m"\n',
        encoding="utf-8")
    rc = main(["run", "--config", str(cfgfile), "--fake-llm"])
    out = capsys.readouterr().out
    assert rc == 0
    assert "open_issues" in out and "converged" in out
