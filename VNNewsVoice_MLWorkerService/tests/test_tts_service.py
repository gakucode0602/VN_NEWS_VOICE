from app.services.tts.base_provider import TTSProvider
from app.services.tts_service import ArticleTTSService


class EchoProvider(TTSProvider):
    provider_name = "echo"

    def __init__(self) -> None:
        self.calls = []

    def generate_tts(self, text: str, voice_name: str = "Zephyr") -> bytes:
        self.calls.append((text, voice_name))
        return b"audio-bytes"


def test_preview_text_truncates_when_too_long() -> None:
    text = "xin " * 20
    preview = ArticleTTSService._preview_text(text, max_chars=16)

    assert preview.endswith("...")
    assert len(preview) == 19


def test_generate_tts_uses_provider_factory(monkeypatch) -> None:
    provider = EchoProvider()

    def fake_create_provider(provider_name=None):
        return provider

    monkeypatch.setattr(
        "app.services.tts_service.TTSProviderFactory.create_provider",
        fake_create_provider,
    )

    result = ArticleTTSService.generate_tts("hello world", voice_name="Nova")
    assert result == b"audio-bytes"
    assert provider.calls == [("hello world", "Nova")]


def test_generate_tts_returns_none_when_provider_creation_fails(monkeypatch) -> None:
    def raise_error(provider_name=None):
        raise RuntimeError("factory failed")

    monkeypatch.setattr(
        "app.services.tts_service.TTSProviderFactory.create_provider", raise_error
    )

    assert ArticleTTSService.generate_tts("hello") is None
