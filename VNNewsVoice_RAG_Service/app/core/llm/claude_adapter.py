import logging
from typing import Any, AsyncGenerator, List, Optional, Dict
from pydantic import BaseModel

from anthropic import Anthropic

from app.core.llm.base import BaseLLM

logger = logging.getLogger(__name__)


class ClaudeAdapter(BaseLLM):
    """Adapter for Anthropic Claude API service."""

    def __init__(
        self,
        api_key: str,
        model_name: str = "claude-haiku-4-20250514",
    ):
        """
        Initialize Claude adapter.

        Args:
            api_key: Anthropic API key
            model_name: Claude model name (e.g., claude-1, claude-2)
        """
        logger.info(f"Initialize Claude API with model: {model_name}")
        self.model_name = model_name
        self.api_key = api_key
        self.client = Anthropic(api_key=api_key)
        logger.info("Successfully initialized Claude API client")

    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,  # FIXED: Added max_tokens parameter to match BaseLLM
        temperature: float = 0.7,
        stop_sequences: Optional[List[str]] = None,  # FIXED: Added stop_sequences
        **kwargs,
    ) -> str:
        """
        Generate completion using Claude API.

        Args:
            prompt: Input text prompt
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0-2.0)
            stop_sequences: Optional list of stop sequences
            **kwargs: Additional parameters (top_p, top_k_sampling, etc.)

        Returns:
            Generated text response

        Raises:
            RuntimeError: If Claude API fails
        """
        messages = [
            {"role": "user", "content": prompt},
        ]

        api_kwargs = self._build_api_kwargs(
            temperature=temperature,
            stop_sequences=stop_sequences,
            **kwargs,
        )

        response = self.client.messages.create(
            model=self.model_name,
            max_tokens=max_tokens,
            messages=messages,
            **api_kwargs,
        )

        return response.content[0].text

    def generate_with_context(
        self, query, context, max_tokens=512, temperature=0.7, **kwargs
    ):
        return self.generate(
            prompt=query, max_tokens=max_tokens, temperature=temperature, **kwargs
        )

    def is_available(self) -> bool:
        try:
            self.client.models.list()
            return True
        except Exception as e:
            logger.error(f"Error when checking Claude API availability: {e}")
            return False

    async def stream(
        self, prompt, max_tokens=512, temperature=0.7, stop_sequences=None, **kwargs
    ) -> AsyncGenerator[str, None]:
        """
        Streaming generation using Claude API.

        Args:
            prompt: Input text prompt
            max_tokens: Maximum tokens to generate
        """

        messages = [
            {"role": "user", "content": prompt},
        ]

        api_kwargs = self._build_api_kwargs(
            temperature=temperature,
            stop_sequences=stop_sequences,
            **kwargs,
        )

        with self.client.messages.stream(
            model=self.model_name,
            max_tokens=max_tokens,
            messages=messages,
            **api_kwargs,
        ) as stream:
            for text_chunk in stream.text_stream:
                yield text_chunk

    def generate_structured(self, prompt, schema, **kwargs) -> BaseModel:
        """
        Generate structured response by parsing the text output into a Pydantic model.

        Args:
            prompt: Input text prompt
            schema: Pydantic model class to parse the response into
            **kwargs: Additional parameters for generation
        Returns:
            An instance of the provided Pydantic schema with the generated content
        """
        try:
            config = self._build_api_kwargs(**kwargs)
            response = self.client.messages.parse(
                model=self.model_name,
                max_tokens=512,
                messages=[{"role": "user", "content": prompt}],
                output_format=schema,
                **config,
            )

            return response.parsed_output

        except Exception as e:
            logger.error(f"Error during structured generation: {e}")
            raise RuntimeError(f"Claude structured generation failed: {e}") from e

    def get_langchain_model(self, **kwargs):
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=self.model_name,
            api_key=self.api_key,
            **kwargs,
        )

    def _build_api_kwargs(
        self,
        temperature: float | None = None,
        top_p: float | None = None,
        top_k: int | None = None,
        stop_sequences: list[str] | None = None,
        metadata: dict | None = None,
        service_tier: str | None = None,
        thinking: dict | None = None,
        **extra_kwargs: Any,
    ) -> Dict[str, Any]:
        if temperature is not None and top_p is not None:
            raise ValueError(
                "Không được dùng đồng thời 'temperature' và 'top_p'. Chọn một trong hai."
            )

        kwargs: dict[str, Any] = {}

        if temperature is not None:
            kwargs["temperature"] = temperature
        if top_p is not None:
            kwargs["top_p"] = top_p
        if top_k is not None:
            kwargs["top_k"] = top_k
        if stop_sequences is not None:
            kwargs["stop_sequences"] = stop_sequences
        if metadata is not None:
            kwargs["metadata"] = metadata
        if service_tier is not None:
            kwargs["service_tier"] = service_tier
        if thinking is not None:
            kwargs["thinking"] = thinking

        # Bất kỳ param nào khác được truyền vào qua **kwargs đều được forward
        kwargs.update(extra_kwargs)

        return kwargs
