from abc import ABC, abstractmethod
from typing import Optional


class TTSProvider(ABC):
    """Abstract base class for TTS providers."""

    provider_name: str = "base"

    @abstractmethod
    def generate_tts(self, text: str, voice_name: str = "Zephyr") -> Optional[bytes]:
        """Generate speech audio bytes for the provided input text."""
