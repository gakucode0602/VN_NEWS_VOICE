import pytest

from app.services.tts.base_provider import TTSProvider
from app.services.tts.provider_factory import TTSProviderFactory


class DummyProvider(TTSProvider):
    provider_name = "dummy"

    def generate_tts(self, text: str, voice_name: str = "Zephyr") -> bytes:
        return f"{voice_name}:{text}".encode("utf-8")


@pytest.fixture(autouse=True)
def restore_provider_registry():
    original = dict(TTSProviderFactory._providers)
    yield
    TTSProviderFactory._providers = original


def test_register_and_create_custom_provider() -> None:
    TTSProviderFactory.register_provider("dummy", DummyProvider)

    provider = TTSProviderFactory.create_provider("dummy")
    assert isinstance(provider, DummyProvider)
    assert provider.generate_tts("xin chao", "Nova") == b"Nova:xin chao"


def test_register_provider_rejects_blank_name() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        TTSProviderFactory.register_provider("", DummyProvider)


def test_unknown_provider_falls_back_to_gemini() -> None:
    provider = TTSProviderFactory.create_provider("unknown-provider")
    assert provider.provider_name == "gemini"
