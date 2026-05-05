import asyncio
import logging
from typing import AsyncGenerator, List, Optional, Type

from openai import BaseModel, OpenAI
import openai

from app.core.llm.base import BaseLLM

logger = logging.getLogger(__name__)


class NvidiaAdapter(BaseLLM):
    def __init__(self, api_key: str, base_url: str, model_name: str) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.model_name = model_name
        self.client = OpenAI(base_url=base_url, api_key=api_key)

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        stop_sequences: Optional[List[str]] = None,
        **kwargs,
    ) -> str:
        """
        Generate text using Nvidia NIM API (OpenAI-compatible).

        Args:
            prompt: Input text prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            stop_sequences: Optional stop sequences
            **kwargs: Additional params (top_p, top_k_sampling, etc.)

        Returns:
            Generated text response
        """
        try:
            # Build API config
            config = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            # Add optional parameters
            if stop_sequences:
                config["stop"] = stop_sequences

            if "top_p" in kwargs:
                config["top_p"] = kwargs["top_p"]

            # Nvidia NIM uses OpenAI-compatible chat API
            result = self.client.chat.completions.create(**config)

            # Extract text from response
            return result.choices[0].message.content or ""

        except Exception as e:
            logger.error(f"Error when generating response from Nvidia NIM: {e}")
            raise RuntimeError(f"Nvidia generation failed: {e}") from e

    def generate_with_context(
        self,
        query: str,
        context: List[str],
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs,
    ) -> str:
        return self.generate(
            prompt=query, max_tokens=max_tokens, temperature=temperature, **kwargs
        )

    def is_available(self) -> bool:
        return True

    async def stream(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        stop_sequences: Optional[List[str]] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """
        Generate text using Nvidia NIM API (OpenAI-compatible) support streaming response.

        Args:
            prompt: Input text prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            stop_sequences: Optional stop sequences
            **kwargs: Additional params (top_p, top_k_sampling, etc.)

        Returns:
            Generated text response with streaming
        """
        try:
            # Build API config
            config = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": temperature,
            }

            # Add optional parameters
            if stop_sequences:
                config["stop"] = stop_sequences

            if "top_p" in kwargs:
                config["top_p"] = kwargs["top_p"]

            async_client = openai.AsyncOpenAI(
                base_url=self.base_url,
                api_key=self.api_key,
                timeout=None,
            )
            async for chunk in await async_client.chat.completions.create(
                stream=True, **config
            ):
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                    await asyncio.sleep(0)

        except Exception as e:
            logger.error(f"Error during streaming: {e}")
            yield f"\n[Error] {str(e)}\n"

    def generate_structured(
        self, prompt: str, schema: Type[BaseModel], **kwargs
    ) -> BaseModel:
        try:
            config = dict()

            if "temperatures" in kwargs:
                config["temperatures"] = kwargs["temperatures"]

            if "max_tokens" in kwargs:
                config["max_output_tokens"] = kwargs["max_tokens"]

            # Add optional parameters
            if "top_p" in kwargs:
                config["top_p"] = kwargs["top_p"]
            if (
                "top_k_sampling" in kwargs
            ):  # Renamed to avoid conflict with retrieval top_k
                config["top_k"] = kwargs["top_k_sampling"]
            if "stop_sequences" in kwargs:
                config["stop_sequences"] = kwargs["stop_sequences"]

            result = self.client.chat.completions.parse(
                **config, response_format=schema
            )

            response = result.choices[0].message

            return response

        except Exception as e:
            logger.error(f"Error when generating response from Nvidia NIM: {e}")
            raise RuntimeError(f"Nvidia generation failed: {e}") from e
