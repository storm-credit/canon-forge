from canon_forge.llm import LLMClient

class FakeRaw:
    def __init__(self): self.calls = 0
    def complete(self, model, prompt):
        self.calls += 1
        return '{"ok": true}'

def test_cache_avoids_second_call(tmp_path):
    raw = FakeRaw()
    c = LLMClient(model="m", cache_dir=tmp_path, raw=raw)
    a = c.extract_json("hash1", "prompt text")
    b = c.extract_json("hash1", "prompt text")
    assert a == {"ok": True} == b
    assert raw.calls == 1  # second call served from disk cache


def test_geminiraw_complete_with_injected_client():
    from canon_forge.llm import GeminiRaw
    class _Resp: text = '{"cost": {"type": "lifespan"}}'
    class _Models:
        def __init__(self): self.calls = []
        def generate_content(self, model, contents, config=None):
            self.calls.append((model, contents)); return _Resp()
    class _Client:
        def __init__(self): self.models = _Models()
    fake = _Client()
    raw = GeminiRaw(client=fake)
    out = raw.complete("gemini-2.5-flash", "extract this")
    assert out == '{"cost": {"type": "lifespan"}}'
    assert fake.models.calls == [("gemini-2.5-flash", "extract this")]


def test_make_raw_unknown_provider_raises():
    from canon_forge.llm import make_raw
    from canon_forge.config import Config
    cfg = Config("s", "*", "o", "m", "schemas", "model", provider="nope")
    try:
        make_raw(cfg)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "nope" in str(e)
