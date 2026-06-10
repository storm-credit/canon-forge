import argparse, json
from .config import load_config
from .pipeline import run

class _FakeLLM:
    def extract_json(self, cache_key, prompt):
        return {}

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="canon-forge")
    sub = parser.add_subparsers(dest="cmd", required=True)
    runp = sub.add_parser("run")
    runp.add_argument("--config", default="config.yaml")
    runp.add_argument("--fake-llm", action="store_true", help="skip API; for dry runs/tests")
    args = parser.parse_args(argv)
    if args.cmd == "run":
        cfg = load_config(args.config)
        report = run(cfg, llm=_FakeLLM() if args.fake_llm else None)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    return 1
