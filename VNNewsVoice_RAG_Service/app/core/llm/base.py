"""Base LLM interface for text generation."""

from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Optional, Type, Any

from pydantic import BaseModel


class BaseLLM(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        stop_sequences: Optional[List[str]] = None,
        **kwargs,
    ) -> str:
        """
        Generate text completion for a given prompt.

        Args:
            prompt: Input text prompt
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
            stop_sequences: List of sequences that stop generation
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text response
        """
        pass

    @abstractmethod
    def generate_with_context(
        self,
        query: str,
        context: List[str],
        max_tokens: int = 512,
        temperature: float = 0.7,
        **kwargs,
    ) -> str:
        """
        Generate response using retrieved context.

        Args:
            query: User's question
            context: List of relevant text chunks
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional parameters

        Returns:
            Generated answer incorporating context
        """
        pass

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        max_tokens: int = 512,
        temperature: float = 0.7,
        stop_sequences: Optional[List[str]] = None,
        **kwargs,
    ) -> AsyncGenerator[str, None]:
        """
        Generate text completion for a given prompt support streaming.

        Args:
            prompt: Input text prompt
            max_tokens: Maximum number of tokens to generate
            temperature: Sampling temperature (0.0 = deterministic, 1.0 = creative)
            stop_sequences: List of sequences that stop generation
            **kwargs: Additional provider-specific parameters

        Returns:
            Generated text response with streaming
        """
        yield ""
        raise NotImplementedError

    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if LLM service is available.

        Returns:
            True if service is ready, False otherwise
        """
        pass

    @abstractmethod
    def generate_structured(
        self, prompt: str, schema: Type[BaseModel], **kwargs
    ) -> BaseModel:
        """
        Parsed to JSON structured

        Returns:
            Basemodel for the object
        """
        pass

    @abstractmethod
    def get_langchain_model(self, **kwargs) -> Any:
        """
        Get the compatible LangChain Chat Model for LangGraph.

        Returns:
            BaseChatModel instance (e.g. ChatGoogleGenerativeAI, ChatOllama)
        """
        pass
