from pathlib import Path
import json

class AnthropicRaw:
    """Real Claude client. Imported lazily so tests need no API key."""
    def __init__(self, api_key=None):
        import anthropic
        self._c = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
    def complete(self, model: str, prompt: str) -> str:
        msg = self._c.messages.create(
            model=model, max_tokens=4096,
            messages=[{"role": "user", "content": prompt}])
        return "".join(b.text for b in msg.content if b.type == "text")

class LLMClient:
    def __init__(self, model: str, cache_dir, raw=None):
        self.model = model
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.raw = raw  # inject real AnthropicRaw in production; fake in tests

    def extract_json(self, cache_key: str, prompt: str) -> dict:
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            return json.loads(cache_file.read_text(encoding="utf-8"))
        text = self.raw.complete(self.model, prompt)
        data = json.loads(text)
        cache_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        return data
