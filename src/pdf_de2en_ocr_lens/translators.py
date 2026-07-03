from __future__ import annotations

import os
from dataclasses import dataclass

import requests


class TranslationError(RuntimeError):
    """Raised when a translation provider fails."""


class Translator:
    name = "base"

    def translate(self, text: str) -> str:
        raise NotImplementedError

    def translate_many(self, texts: list[str]) -> list[str]:
        return [self.translate(text) for text in texts]


class PassthroughTranslator(Translator):
    name = "passthrough"

    def translate(self, text: str) -> str:
        return text


class DemoDictionaryTranslator(Translator):
    """Tiny deterministic translator for demos/tests when no API key is available."""

    name = "demo"

    dictionary = {
        "deutsch": "German",
        "englisch": "English",
        "spannung": "voltage",
        "strom": "current",
        "leistung": "power",
        "netzwerk": "network",
        "sicherheit": "security",
        "entwicklung": "development",
        "validierung": "validation",
        "eingang": "input",
        "ausgang": "output",
        "messung": "measurement",
        "steuerung": "control",
    }

    def translate(self, text: str) -> str:
        words = []
        for word in text.split():
            stripped = word.strip(".,;:!?()[]{}")
            translated = self.dictionary.get(stripped.lower())
            words.append(word.replace(stripped, translated) if translated else word)
        return " ".join(words)


@dataclass
class DeepLTranslator(Translator):
    api_key: str
    endpoint: str = "https://api-free.deepl.com/v2/translate"
    source_lang: str = "DE"
    target_lang: str = "EN"

    name = "deepl"

    def translate_many(self, texts: list[str]) -> list[str]:
        if not texts:
            return []
        response = requests.post(
            self.endpoint,
            data={
                "auth_key": self.api_key,
                "text": texts,
                "source_lang": self.source_lang,
                "target_lang": self.target_lang,
            },
            timeout=30,
        )
        if response.status_code >= 400:
            raise TranslationError(f"DeepL returned HTTP {response.status_code}: {response.text[:300]}")
        payload = response.json()
        return [item["text"] for item in payload.get("translations", [])]

    def translate(self, text: str) -> str:
        return self.translate_many([text])[0]


class ArgosTranslator(Translator):
    name = "argos"

    def __init__(self, source_lang: str = "de", target_lang: str = "en") -> None:
        try:
            from argostranslate import translate
        except ImportError as exc:  # pragma: no cover - optional dependency
            raise TranslationError("Install Argos support with `pip install .[argos]`.") from exc
        self._translate = translate
        self.source_lang = source_lang
        self.target_lang = target_lang

    def translate(self, text: str) -> str:
        return self._translate.translate(text, self.source_lang, self.target_lang)


def build_translator(name: str) -> Translator:
    normalized = name.lower()
    if normalized == "passthrough":
        return PassthroughTranslator()
    if normalized == "demo":
        return DemoDictionaryTranslator()
    if normalized == "deepl":
        api_key = os.environ.get("DEEPL_API_KEY")
        if not api_key:
            raise TranslationError("Set DEEPL_API_KEY to use the DeepL translator.")
        return DeepLTranslator(api_key=api_key)
    if normalized == "argos":
        return ArgosTranslator()
    raise TranslationError(f"Unknown translator: {name}")
