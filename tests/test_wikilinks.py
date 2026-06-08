from canon_forge.wikilinks import parse_wikilinks

def test_parse_plain_and_display():
    text = "에반은 [[적열의 심장 펜던트]]와 [[01-8. 세력|프로스트본 연합]]을 가졌다."
    assert parse_wikilinks(text) == ["적열의 심장 펜던트", "01-8. 세력"]

def test_dedup_and_empty():
    assert parse_wikilinks("[[A]] [[A]]") == ["A"]
    assert parse_wikilinks("no links") == []
