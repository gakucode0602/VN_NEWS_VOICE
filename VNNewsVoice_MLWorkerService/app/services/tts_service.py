from datetime import datetime
import time
from typing import Optional
import logging
import os
import wave
from pathlib import Path

import cloudinary
import cloudinary.uploader

from app.services.aws_storage_service import S3StorageService
from app.services.tts.provider_factory import TTSProviderFactory

logger = logging.getLogger(__name__)


class ArticleTTSService:
    @staticmethod
    def _preview_text(text: str, max_chars: int = 220) -> str:
        """Create a compact single-line preview for logs."""
        normalized = " ".join((text or "").split())
        if len(normalized) <= max_chars:
            return normalized
        return f"{normalized[:max_chars]}..."

    @staticmethod
    def _save_wave_file(
        filename: str,
        pcm_data: bytes,
        channels: int = 1,
        rate: int = 24000,
        sample_width: int = 2,
    ):
        with wave.open(filename, "wb") as wf:
            wf.setnchannels(channels)
            wf.setsampwidth(sample_width)
            wf.setframerate(rate)
            wf.writeframes(pcm_data)

    @staticmethod
    def test_tts_with_short_text(
        provider_name: Optional[str] = None,
    ) -> Optional[bytes]:
        short_text = "Day la ban tin thoi su. Xin chao quy vi va cac ban."
        return ArticleTTSService.generate_tts(short_text, "Zephyr", provider_name)

    @staticmethod
    def generate_tts(
        text: str,
        voice_name: str = "Zephyr",
        provider_name: Optional[str] = None,
    ) -> Optional[bytes]:
        try:
            provider = TTSProviderFactory.create_provider(provider_name)
            logger.info(
                "Generating TTS via provider=%s for %s characters...",
                provider.provider_name,
                len(text),
            )
            logger.info("TTS input preview=%r", ArticleTTSService._preview_text(text))
            return provider.generate_tts(text, voice_name)
        except Exception:
            logger.exception("TTS generation error")
            return None

    @staticmethod
    def generate_tts_with_upload(
        text: str,
        voice_name: str = "Zephyr",
        provider_name: Optional[str] = None,
    ) -> Optional[dict]:
        """Generate TTS and upload to AWS S3."""
        try:
            audio_data = ArticleTTSService.generate_tts(text, voice_name, provider_name)
            if not audio_data:
                return None

            s3_service = S3StorageService()
            timestamp = int(time.time())
            filename = f"tts_{timestamp}_{voice_name.lower()}.wav"

            upload_result = s3_service.upload_audio(audio_data, filename)
            logger.debug("Upload result: %s", upload_result)

            if not upload_result or upload_result.get("status") != "success":
                logger.warning("Upload failed")
                return None

            result = {
                "status": "success",
                "audio_url": upload_result["audio_url"],
                "audio_size": len(audio_data),
                "voice_name": voice_name,
                "text_length": len(text),
                "filename": filename,
                "upload_timestamp": upload_result.get(
                    "created_at", datetime.now().isoformat()
                ),
                "cloud_provider": "aws_s3",
                "public_id": filename,
            }

            return result

        except Exception:
            logger.exception("TTS upload error")
            return None

    @staticmethod
    def generate_tts_with_upload_cloudinary(
        text: str,
        voice_name: str = "Zephyr",
        provider_name: Optional[str] = None,
    ) -> Optional[dict]:
        try:
            env_path = Path(__file__).resolve().parents[2] / ".env"
            if env_path.exists():
                from dotenv import load_dotenv

                load_dotenv(env_path, override=True)

            cloudinary.config(
                cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
                api_key=os.getenv("CLOUDINARY_API_KEY"),
                api_secret=os.getenv("CLOUDINARY_API_SECRET"),
            )

            logger.info("Cloudinary config check:")
            logger.info("Cloud name: %s", os.getenv("CLOUDINARY_CLOUD_NAME", "Not set"))
            logger.info(
                "API key: %s", "Set" if os.getenv("CLOUDINARY_API_KEY") else "Not set"
            )
            logger.info(
                "API secret: %s",
                "Set" if os.getenv("CLOUDINARY_API_SECRET") else "Not set",
            )

            audio_data = ArticleTTSService.generate_tts(text, voice_name, provider_name)
            if not audio_data:
                return None

            timestamp = int(time.time())
            filename = f"tts_{timestamp}_{voice_name.lower()}"
            folder = "vnnews/audio"
            public_id = f"{folder}/{filename}"

            upload_result = cloudinary.uploader.upload(
                audio_data,
                public_id=public_id,
                resource_type="raw",
                folder=None,
                overwrite=True,
            )

            result = {
                "status": "success",
                "audio_url": upload_result["secure_url"],
                "public_id": upload_result["public_id"],
                "audio_size": len(audio_data),
                "voice_name": voice_name,
                "text_length": len(text),
                "filename": f"{filename}.wav",
                "upload_timestamp": datetime.now().isoformat(),
                "cloud_provider": "cloudinary",
            }

            logger.info("Upload success")
            logger.info("URL: %s", result["audio_url"])
            logger.info("Public ID: %s", result["public_id"])

            return result

        except Exception:
            logger.exception("TTS upload error")
            return None
