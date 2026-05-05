import asyncio
import logging
from typing import AsyncGenerator, List, Optional, Type

from pydantic import BaseModel

from google import genai

from app.core.llm.base import BaseLLM

logger = logging.getLogger(__name__)


class GeminiAdapter(BaseLLM):
    """Adapter for Google Gemini API service."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "gemini-2.5-flash-lite",
    ):
        """
        Initialize Gemini adapter.

        Args:
            api_key: Google AI API key
            model_name: Gemini model name (e.g., gemini-1.5-flash, gemini-2.0-flash-exp)
        """
        logger.info(f"Initialize Gemini API with model: {model_name}")
        self.model_name = model_name
        self.api_key = api_key
        self.client = genai.Client(api_key=api_key)
        logger.info("Successfully initialized Gemini API client")

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,  # FIXED: Added max_tokens parameter to match BaseLLM
        temperature: float = 0.7,
        stop_sequences: Optional[List[str]] = None,  # FIXED: Added stop_sequences
        **kwargs,
    ) -> str:
        """
        Generate completion using Gemini API.

        Args:
            prompt: Input text prompt
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0-2.0)
            stop_sequences: Optional list of stop sequences
            **kwargs: Additional parameters (top_p, top_k_sampling, etc.)

        Returns:
            Generated text response

        Raises:
            RuntimeError: If Gemini API fails
        """
        try:
            # Build generation config
            config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,  # Gemini uses max_output_tokens
            }

            # Add optional parameters
            if "top_p" in kwargs:
                config["top_p"] = kwargs["top_p"]
            if (
                "top_k_sampling" in kwargs
            ):  # Renamed to avoid conflict with retrieval top_k
                config["top_k"] = kwargs["top_k_sampling"]
            if stop_sequences:
                config["stop_sequences"] = stop_sequences

            # Call Gemini API
            result = self.client.models.generate_content(
                model=self.model_name, contents=prompt, config=config
            )

            return result.text if result.text else ""

        except Exception as e:
            logger.error(f"Error when generating response from Gemini: {e}")
            raise RuntimeError(f"Gemini generation failed: {e}") from e

    def generate_with_context(
        self,
        query: str,
        context: List[str],
        max_tokens: int = 512,  # FIXED: Added max_tokens parameter
        temperature: float = 0.7,
        **kwargs,
    ) -> str:
        """
        Generate RAG response with context.

        Note: Context formatting is handled by Generator class,
        so we just pass the query through.
        """
        return self.generate(
            prompt=query, max_tokens=max_tokens, temperature=temperature, **kwargs
        )

    def is_available(self) -> bool:
        """Check if Gemini API is accessible."""
        return True

    async def stream(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        stop_sequences: Optional[List[str]] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Stream tokens from Gemini API.

        Note: google-genai generate_content_stream() is sync,
        so we run it in a thread and yield chunks.
        """
        try:
            config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
            if "top_p" in kwargs:
                config["top_p"] = kwargs["top_p"]
            if "top_k_sampling" in kwargs:
                config["top_k"] = kwargs["top_k_sampling"]
            if stop_sequences:
                config["stop_sequences"] = stop_sequences

            # generate_content_stream() is sync → run in thread
            import queue
            import threading

            q: queue.Queue = queue.Queue()
            SENTINEL = object()

            def _run():
                try:
                    for chunk in self.client.models.generate_content_stream(
                        model=self.model_name, contents=prompt, config=config
                    ):
                        if chunk.text:
                            q.put(chunk.text)
                except Exception as e:
                    q.put(e)
                finally:
                    q.put(SENTINEL)

            thread = threading.Thread(target=_run, daemon=True)
            thread.start()

            while True:
                item = await asyncio.to_thread(q.get)
                if item is SENTINEL:
                    break
                if isinstance(item, Exception):
                    raise item
                yield item
                await asyncio.sleep(0)

        except Exception as e:
            logger.error(f"Error while streaming response: {e}")
            yield f"\n[Error] {str(e)}\n"

    def generate_structured(
        self,
        prompt: str,
        schema: Type[BaseModel],
        **kwargs,
    ) -> BaseModel:
        """
        Generate structured output using Gemini API.

        Args:
            prompt: Input text prompt
            schema: Pydantic model class to enforce output structure
            **kwargs: Additional parameters

        Returns:
            Parsed Pydantic model instance
        """
        try:
            config = {
                "temperature": kwargs.get(
                    "temperature", 0.0
                ),  # Default 0.0 for deterministic structured output
                "response_mime_type": "application/json",
                "response_schema": schema,
            }

            result = self.client.models.generate_content(
                model=self.model_name, contents=prompt, config=config
            )

            if not result.text:
                raise ValueError("Empty response from Gemini")

            return schema.model_validate_json(result.text)

        except Exception as e:
            logger.error(f"Error when generating structured response from Gemini: {e}")
            raise RuntimeError(f"Gemini structured generation failed: {e}") from e

    def get_langchain_model(self, **kwargs):
        """Get the compatible LangChain model for LangGraph execution."""
        from langchain_google_genai import ChatGoogleGenerativeAI
        from app.config.settings import get_settings

        settings = get_settings()

        return ChatGoogleGenerativeAI(
            model=self.model_name,
            temperature=kwargs.get("temperature", 0.0),
            api_key=settings.gemini_api_key,
        )
