import logging
from typing import Dict, Optional, Type

from app.core.config import settings
from app.services.tts.base_provider import TTSProvider
from app.services.tts.gemini_provider import GeminiTTSProvider

logger = logging.getLogger(__name__)


class TTSProviderFactory:
    """Factory/registry for selecting TTS provider implementations."""

    _providers: Dict[str, Type[TTSProvider]] = {
        "gemini": GeminiTTSProvider,
    }

    @classmethod
    def register_provider(
        cls, provider_name: str, provider_cls: Type[TTSProvider]
    ) -> None:
        """Register a custom provider class for future extension."""
        key = (provider_name or "").strip().lower()
        if not key:
            raise ValueError("provider_name must not be empty")
        cls._providers[key] = provider_cls

    @classmethod
    def create_provider(cls, provider_name: Optional[str] = None) -> TTSProvider:
        configured = provider_name or settings.TTS_PROVIDER
        key = (configured or "gemini").strip().lower()

        provider_cls = cls._providers.get(key)
        if provider_cls is None:
            logger.warning(
                "Unknown TTS provider '%s', fallback to 'gemini'",
                key,
            )
            provider_cls = cls._providers["gemini"]
            key = "gemini"

        provider = provider_cls()
        logger.info("Using TTS provider: %s", key)
        return provider
