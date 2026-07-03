from pdf_de2en_ocr_lens.translators import DemoDictionaryTranslator, PassthroughTranslator, build_translator


def test_passthrough_translator_returns_same_text():
    translator = PassthroughTranslator()
    assert translator.translate("Das ist ein Test.") == "Das ist ein Test."


def test_demo_translator_replaces_known_terms():
    translator = DemoDictionaryTranslator()
    assert translator.translate("Spannung und Strom") == "voltage und current"


def test_build_translator_demo():
    assert build_translator("demo").name == "demo"
