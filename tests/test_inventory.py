from canon_forge.inventory import scan, category_from_path

def test_category_from_path():
    assert category_from_path("01. 아스트라리스 크로니클/01-14. 영웅 백과/x.md") == "hero"
    assert category_from_path("01. 아스트라리스 크로니클/01-19. 아이템 도감/y.md") == "item"
    assert category_from_path("01. 아스트라리스 크로니클/01-8. 세력 아카이브/z.md") == "faction"
    assert category_from_path("00. 세계의 틀/00-2.md") == "rule"
    assert category_from_path("misc/other.md") == "unknown"

def test_scan(fixtures_dir):
    entries = scan(fixtures_dir / "vault")
    assert len(entries) == 4
    cats = sorted(e["category"] for e in entries)
    assert cats == ["faction", "hero", "item", "rule"]
    for e in entries:
        assert len(e["sha256"]) == 64 and e["path"]
