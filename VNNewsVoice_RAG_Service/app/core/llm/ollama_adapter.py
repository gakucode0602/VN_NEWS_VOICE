"""Ollama LLM adapter implementation."""

import asyncio
import logging
from typing import AsyncGenerator, List, Optional, Type

import ollama
from openai import BaseModel

from app.core.llm.base import BaseLLM

logger = logging.getLogger(__name__)


class OllamaAdapter(BaseLLM):
    """Adapter for Ollama local LLM service."""

    def __init__(
        self, model_name: str = "llama2", host: str = "http://localhost:11434"
    ):
        """
        Initialize Ollama adapter.

        Args:
            model_name: Name of the Ollama model to use
            host: Ollama server URL
        """
        logger.info("Initialize Ollama adapter")
        self.model_name = model_name
        self.host = host
        self.client = ollama.Client(host=host)
        logger.info("Successfully load ollama")

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        stop_sequences: Optional[List[str]] = None,
        **kwargs,
    ) -> str:
        """
        Generate completion using Ollama.

        Args:
            prompt: Input text prompt
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0-1.0)
            stop_sequences: Optional list of stop sequences
            **kwargs: Additional parameters

        Returns:
            Generated text response

        Raises:
            RuntimeError: If Ollama service fails to generate response
        """
        try:
            options = {"temperature": temperature, "num_predict": max_tokens}
            if stop_sequences is not None:
                options["stop"] = stop_sequences
            result = self.client.generate(
                model=self.model_name, prompt=prompt, options=options
            )
            return result.response
        except Exception as e:
            logger.error(f"Error when generate response: {e}")
            raise RuntimeError(f"Ollama generation failed: {e}") from e

    def generate_with_context(
        self,
        query: str,
        context: List[str],
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs,
    ) -> str:
        return self.generate(
            prompt=query, max_tokens=max_tokens, temperature=temperature
        )

    def is_available(self) -> bool:
        try:
            self.client.list()
            return True
        except Exception as e:
            logger.error(f"Error when loading Ollama: {e}")
            return False

    async def stream(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        stop_sequences: Optional[List[str]] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """Stream tokens from Ollama using AsyncClient."""
        try:
            options = {"temperature": temperature, "num_predict": max_tokens}
            if stop_sequences is not None:
                options["stop"] = stop_sequences

            async_client = ollama.AsyncClient(host=self.host)
            async for chunk in await async_client.generate(
                model=self.model_name,
                prompt=prompt,
                options=options,
                stream=True,
            ):
                if chunk.response:
                    yield chunk.response
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
                config["num_predict"] = kwargs["max_tokens"]

            if "stop_sequences" in kwargs:
                config["stop"] = kwargs["stop_sequences"]

            result = self.client.generate(
                model=self.model_name,
                prompt=prompt,
                format=schema.model_json_schema(),
                options=config,
            )
            response = schema.model_validate_json(result.response)
            return response

        except Exception as e:
            logger.error(f"Error when generate response: {e}")
            raise RuntimeError(f"Ollama generation failed: {e}") from e

    def get_langchain_model(self, **kwargs):
        """Get the compatible LangChain model for LangGraph execution."""
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=self.model_name,
            base_url=self.host,
            temperature=kwargs.get("temperature", 0.0),
        )
