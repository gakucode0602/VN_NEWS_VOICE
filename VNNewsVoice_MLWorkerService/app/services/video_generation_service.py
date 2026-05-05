"""
app/services/video_generation_service.py

Generates short news-clip videos using Google Veo API and uploads to Cloudinary.

Flow:
  1. Build a journalistic prompt from article title + summary
  2. Optionally download top_image_url → pass as starting frame (image-to-video)
  3. Submit generate_videos() job → poll until done (max 6 min)
  4. Download MP4 to temp file → upload to Cloudinary resource_type="video"
  5. Return Cloudinary secure_url
"""

import logging
import os
import tempfile
import time
import urllib.request
from typing import Optional

import cloudinary
import cloudinary.uploader

from app.core.config import settings

logger = logging.getLogger(__name__)


class VideoGenerationService:
    # Style presets: each value is a prompt prefix injected before the content.
    # Style is controlled entirely via prompt text — Veo has no dedicated style param.
    # Presets are tuned for a Vietnamese news platform (B-roll / broadcast use-case).
    STYLE_PRESETS: dict[str, str] = {
        # --- News-first presets (recommended for VNNewsVoice) ---
        "news": (
            "Cinematic documentary B-roll, professional broadcast quality, "
            "realistic, steady camera, neutral lighting, highly detailed, "
            "journalistic tone, 16:9 widescreen."
        ),
        "documentary": (
            "Documentary film style, natural lighting, handheld camera movement, "
            "authentic footage, observational style, muted color grade, "
            "professional broadcast quality."
        ),
        "tech": (
            "Abstract motion graphics, 3D broadcast news design, corporate style, "
            "glowing network lines, cinematic, professional tech concept visualization, "
            "smooth animation, dark background."
        ),
        "explainer": (
            "Minimalist flat vector illustration style, smooth animation, "
            "corporate colors, clean and professional, informative explainer style, "
            "soft lighting, simple backgrounds."
        ),
        "cinematic": (
            "Hollywood cinematic style, dramatic lighting, shallow depth of field, "
            "epic scale, anamorphic lens flare, film grain, widescreen."
        ),
        "drone": (
            "Aerial drone footage, bird's eye view, sweeping landscape shots, "
            "smooth pull-back camera move, golden hour lighting."
        ),
        # --- Non-news styles (kept for flexibility) ---
        "animation": (
            "2D cartoon animation style, vibrant colors, smooth fluent motion, "
            "anime-inspired illustration, clean line art, flat design."
        ),
        "3d": (
            "Photorealistic 3D CGI rendered animation, depth of field, "
            "studio lighting, high-poly models, cinematic 3D render."
        ),
    }

    @staticmethod
    def _build_prompt(
        title: str,
        summary: Optional[str] = None,
        video_style: Optional[str] = None,
    ) -> str:
        context = summary.strip() if summary else title.strip()
        style_key = (video_style or "news").lower().strip()
        style_text = VideoGenerationService.STYLE_PRESETS.get(
            style_key,
            VideoGenerationService.STYLE_PRESETS["news"],  # fallback
        )
        return f"{style_text} Visual content about: {context}."

    @staticmethod
    def _download_image_bytes(image_url: str) -> Optional[bytes]:
        try:
            req = urllib.request.Request(
                image_url,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.read()
        except Exception:
            logger.exception("Failed to download top image: %s", image_url)
            return None

    @staticmethod
    def _detect_mime_type(url: str) -> str:
        url_lower = url.lower().split("?")[0]
        if url_lower.endswith(".png"):
            return "image/png"
        if url_lower.endswith(".webp"):
            return "image/webp"
        if url_lower.endswith(".gif"):
            return "image/gif"
        return "image/jpeg"

    @staticmethod
    def generate_and_upload(
        article_id: str,
        title: str,
        top_image_url: Optional[str] = None,
        summary: Optional[str] = None,
        model: Optional[str] = None,
        duration_seconds: Optional[int] = None,
        video_style: Optional[str] = None,
    ) -> Optional[dict]:
        """
        Blocking: Run via asyncio.to_thread() from the ops endpoint.

        Returns a dict on success, None on failure.
        """
        try:
            from google import genai
            from google.genai import types

            api_key = settings.GOOGLE_AI_API_KEY_VEO or settings.GOOGLE_AI_API_KEY
            if not api_key:
                raise ValueError(
                    "Neither GOOGLE_AI_API_KEY_VEO nor GOOGLE_AI_API_KEY is configured"
                )

            client = genai.Client(api_key=api_key)
            veo_model = model or settings.VEO_MODEL
            dur = duration_seconds or settings.VEO_DURATION_SECONDS
            # veo-3.0-generate-preview / veo-3.1: valid durations are 4, 6, 8
            # veo-2.0-generate-001: valid durations are 5, 6, 8 (requires GCP billing)
            if dur not in (4, 5, 6, 8):
                logger.warning("Invalid duration_seconds=%d, falling back to 8", dur)
                dur = 8

            prompt = VideoGenerationService._build_prompt(title, summary, video_style)
            style_used = (video_style or "news").lower().strip()
            if style_used not in VideoGenerationService.STYLE_PRESETS:
                logger.warning(
                    "Unknown video_style=%r, falling back to 'news'", video_style
                )
                style_used = "news"

            logger.info(
                "Veo job starting | article=%s model=%s duration=%ds style=%s",
                article_id,
                veo_model,
                dur,
                style_used,
            )
            logger.info("Prompt: %r", prompt)

            gen_kwargs: dict = dict(
                model=veo_model,
                prompt=prompt,
                config=types.GenerateVideosConfig(
                    aspect_ratio="16:9",
                    duration_seconds=dur,
                    number_of_videos=1,
                ),
            )

            # --- Image-to-video if top_image_url available ---
            if top_image_url:
                img_bytes = VideoGenerationService._download_image_bytes(top_image_url)
                if img_bytes:
                    mime_type = VideoGenerationService._detect_mime_type(top_image_url)
                    gen_kwargs["image"] = types.Image(
                        image_bytes=img_bytes, mime_type=mime_type
                    )
                    logger.info(
                        "Image-to-video: %s (%s, %d bytes)",
                        top_image_url,
                        mime_type,
                        len(img_bytes),
                    )
                else:
                    logger.warning(
                        "Could not download top image — falling back to text-to-video"
                    )

            # --- Submit job ---
            operation = client.models.generate_videos(**gen_kwargs)
            logger.info("Veo job submitted, starting poll loop...")

            # --- Poll (max 6 min = 36 × 10s) ---
            max_polls = 36
            polls = 0
            while not operation.done and polls < max_polls:
                time.sleep(10)
                operation = client.operations.get(operation)
                polls += 1
                logger.info("Poll %d/%d | done=%s", polls, max_polls, operation.done)

            if not operation.done:
                raise TimeoutError("Veo generation timed out after 6 minutes")

            if not operation.response or not operation.response.generated_videos:
                raise ValueError(
                    "Veo response contained no generated_videos — "
                    "possibly blocked by safety filters"
                )

            # --- Download to temp file ---
            generated_video = operation.response.generated_videos[0]
            client.files.download(file=generated_video.video)

            tmp_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp:
                    tmp_path = tmp.name
                generated_video.video.save(tmp_path)

                file_size = os.path.getsize(tmp_path)
                logger.info("Video saved locally: %s (%d bytes)", tmp_path, file_size)

                # --- Upload to Cloudinary ---
                cloudinary.config(
                    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
                    api_key=settings.CLOUDINARY_API_KEY,
                    api_secret=settings.CLOUDINARY_API_SECRET,
                )

                public_id = f"vnnews/videos/{article_id}"
                upload_result = cloudinary.uploader.upload(
                    tmp_path,
                    public_id=public_id,
                    resource_type="video",
                    overwrite=True,
                )

                video_url = upload_result["secure_url"]
                logger.info("Cloudinary upload success: %s", video_url)

                return {
                    "status": "success",
                    "video_url": video_url,
                    "public_id": upload_result["public_id"],
                    "article_id": article_id,
                    "model": veo_model,
                    "duration_seconds": dur,
                    "video_style": style_used,
                    "polls": polls,
                    "file_size_bytes": file_size,
                    "used_image_input": "image" in gen_kwargs,
                }

            finally:
                if tmp_path and os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    logger.debug("Temp file cleaned up: %s", tmp_path)

        except Exception:
            logger.exception("Video generation failed for article=%s", article_id)
            return None
