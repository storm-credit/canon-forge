from pathlib import Path
import json

class AnthropicRaw:
    """Real Claude client. Imported lazily so tests need no API key."""
    def __init__(self, api_key=None, max_tokens=16384):
        import anthropic
        self._c = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        self._max_tokens = max_tokens

    def complete(self, model: str, prompt: str) -> str:
        import anthropic
        msg = self._c.messages.create(
            model=model, max_tokens=self._max_tokens,
            messages=[{"role": "user", "content": prompt}])
        # Fable 5 may refuse (HTTP 200, stop_reason="refusal", empty content)
        if msg.stop_reason == "refusal":
            raise anthropic.BadRequestError(  # type: ignore[attr-defined]
                message=f"model refused: {getattr(msg, 'stop_details', '')}",
                response=None, body=None)  # type: ignore[arg-type]
        # thinking blocks have type="thinking"; filter to text only
        return "".join(b.text for b in msg.content if b.type == "text")

class GeminiRaw:
    """Vertex AI backend via the reusable gemini-client module (create_client).
    Sets env, delegates, forces JSON output. Injectable client for tests."""
    def __init__(self, sa_key_file=None, project=None, location="us-central1", client=None):
        self._client = client  # injectable for tests (no network/creds needed)
        if self._client is None:
            import os, json
            os.environ["GEMINI_BACKEND"] = "vertex_ai"
            if location:
                os.environ.setdefault("VERTEX_LOCATION", location)
            if sa_key_file:
                os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = sa_key_file
                if not project:
                    with open(sa_key_file, encoding="utf-8") as f:
                        project = json.load(f).get("project_id", "")
            if project:
                os.environ["VERTEX_PROJECT"] = project
            from gemini_client import create_client
            self._client = create_client()

    def complete(self, model: str, prompt: str) -> str:
        config = None
        try:  # build JSON-forcing config only if the SDK is importable (real runs)
            from google.genai import types
            config = types.GenerateContentConfig(response_mime_type="application/json")
        except Exception:
            config = None
        resp = self._client.models.generate_content(model=model, contents=prompt, config=config)
        return (resp.text or "").strip()


def make_raw(cfg):
    """Build the raw LLM client selected by cfg.provider."""
    if cfg.provider == "vertex":
        return GeminiRaw(sa_key_file=cfg.vertex_sa_key or None,
                         project=cfg.vertex_project or None,
                         location=cfg.vertex_location)
    if cfg.provider == "anthropic":
        return AnthropicRaw(max_tokens=cfg.llm_max_tokens)
    raise ValueError(f"unknown provider: {cfg.provider!r}")


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
