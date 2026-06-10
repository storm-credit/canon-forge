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
