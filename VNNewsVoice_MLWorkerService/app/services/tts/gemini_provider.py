import logging
import wave
from pathlib import Path
from typing import Optional

from google import genai
from google.genai import types

from app.core.config import settings
from app.services.tts.base_provider import TTSProvider

logger = logging.getLogger(__name__)


class GeminiTTSProvider(TTSProvider):
    """Gemini implementation for text-to-speech generation."""

    provider_name = "gemini"

    @staticmethod
    def _preview_text(text: str, max_chars: int = 220) -> str:
        normalized = " ".join((text or "").split())
        if len(normalized) <= max_chars:
            return normalized
        return f"{normalized[:max_chars]}..."

    @staticmethod
    def _pcm_to_wav(
        pcm_data: bytes,
        channels: int = 1,
        sample_rate: int = 24000,
        sample_width: int = 2,
    ) -> bytes:
        """Convert raw PCM data returned by Gemini to WAV format."""
        import io

        wav_buffer = io.BytesIO()

        with wave.open(wav_buffer, "wb") as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(pcm_data)

        wav_buffer.seek(0)
        wav_data = wav_buffer.getvalue()

        logger.debug("PCM to WAV conversion")
        logger.debug("Input PCM: %s bytes", len(pcm_data))
        logger.debug("Output WAV: %s bytes", len(wav_data))
        logger.debug("WAV header: %s", wav_data[:12])

        return wav_data

    def generate_tts(self, text: str, voice_name: str = "Zephyr") -> Optional[bytes]:
        try:
            env_path = Path(__file__).resolve().parents[3] / ".env"
            if env_path.exists():
                from dotenv import load_dotenv

                load_dotenv(env_path, override=True)

            api_key = settings.GOOGLE_AI_API_KEY
            if not api_key:
                raise ValueError(
                    "API key for Google AI is not set in environment variables"
                )

            client = genai.Client(api_key=api_key)
            content = f"""Read aloud in a clear, calm, and professional tone,
                        suitable for news reading. Maintain a steady pace with
                        natural pauses at punctuation. Keep the delivery neutral
                        and objective: {text}"""

            logger.info("Generating Gemini TTS for %s characters...", len(text))
            logger.info(
                "Gemini TTS input preview=%r",
                self._preview_text(text),
            )

            response = client.models.generate_content(
                model="gemini-2.5-flash-preview-tts",
                contents=content,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=types.SpeechConfig(
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name=voice_name,
                            )
                        )
                    ),
                ),
            )

            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]

                if candidate.content and candidate.content.parts:
                    part = candidate.content.parts[0]

                    if hasattr(part, "inline_data") and part.inline_data:
                        pcm_data = part.inline_data.data
                        logger.debug("Raw PCM data: %s bytes", len(pcm_data))

                        if isinstance(pcm_data, bytes):
                            return self._pcm_to_wav(pcm_data)

                        logger.warning("Unexpected data type: %s", type(pcm_data))
                        return None

            logger.warning("No audio data found")
            return None

        except Exception:
            logger.exception("Gemini TTS provider error")
            return None
