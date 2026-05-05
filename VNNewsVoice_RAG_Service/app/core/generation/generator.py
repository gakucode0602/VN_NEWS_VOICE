"""Answer generator using LLM."""

import asyncio
import logging
from typing import AsyncGenerator, List

from app.core.llm.base import BaseLLM
from app.models.domain.retrieval import RetrievalResult

logger = logging.getLogger(__name__)


class Generator:
    """Generator for synthesizing answers from retrieved context."""

    # Default prompt template for Vietnamese news chatbot
    DEFAULT_PROMPT_TEMPLATE = """Bạn là trợ lý AI chuyên phân tích tin tức tiếng Việt. Nhiệm vụ của bạn là trả lời câu hỏi dựa trên các bài báo được cung cấp.

Ngữ cảnh từ các bài báo:
{context}

Câu hỏi: {query}

Hướng dẫn:
- Trả lời đầy đủ, chi tiết và rõ ràng dựa trên thông tin trong ngữ cảnh
- Giải thích bối cảnh và các chi tiết quan trọng liên quan đến câu hỏi
- Trả lời bằng tiếng Việt
- TUYỆT ĐỐI KHÔNG liệt kê "Nguồn tham khảo", link URL, hay các mã UUID ở cuối bài. Hệ thống sẽ tự động ghép nguồn vào UI.
- Chỉ xuất ra nội dung câu trả lời tự nhiên.

Trả lời:"""

    def __init__(self, llm: BaseLLM):
        """
        Initialize generator.

        Args:
            llm: Language model for generation
        """
        self.llm = llm

    def generate(
        self,
        query: str,
        retrieval_results: List[RetrievalResult],
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate answer from query and retrieved context.

        Hints:
        - Extract text content from retrieval_results: [r.chunk.content for r in retrieval_results]
        - Format context chunks with numbering: "1. {chunk1}\n2. {chunk2}..."
        - Use self.DEFAULT_PROMPT_TEMPLATE.format(context=..., query=...)
        - Call self.llm.generate() with the prompt
        - Add logging before and after generation
        - Handle empty retrieval_results case
        """
        try:
            prompt = self._build_prompt(
                retrieval_results=retrieval_results, query=query
            )
            logger.info(f"Generating response for {query[:100]}...")
            response = self.llm.generate(
                prompt=prompt, max_tokens=max_tokens, temperature=temperature
            )
            logger.info(f"Generated response with length: {len(response)} characters")
            return response

        except Exception as e:
            logger.error(f"Error when generate content: {e}")
            raise

    def generate_with_sources(
        self,
        query: str,
        retrieval_results: List[RetrievalResult],
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> tuple[str, List[RetrievalResult]]:
        """
        Generate answer and return with source results.

        Args:
            query: User question
            retrieval_results: Retrieved context chunks
            max_tokens: Max tokens for generation
            temperature: Sampling temperature

        Returns:
            Tuple of (generated_answer, retrieval_results)
        """
        answer = self.generate(query, retrieval_results, max_tokens, temperature)
        return answer, retrieval_results

    async def generate_stream(
        self,
        query: str,
        retrieval_results: List[RetrievalResult],
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> AsyncGenerator[str, None]:
        """
        Generate answer and return with source results.

        Args:
            query: User question
            retrieval_results: Retrieved context chunks
            max_tokens: Max tokens for generation
            temperature: Sampling temperature

        Returns:
            Async generator for streaming
        """
        try:
            prompt = self._build_prompt(
                retrieval_results=retrieval_results, query=query
            )
            logger.info(f"Generating response for {query[:100]}...")
            # stream() is an async generator - iterate directly, no 'await' needed
            async for chunk in self.llm.stream(
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
            ):
                if chunk:
                    yield chunk
                    await asyncio.sleep(0)

        except Exception as e:
            logger.error(f"Error when generating {e}")
            yield f"\n[Error]: {str(e)}\n"

    def _build_prompt(
        self, retrieval_results: List[RetrievalResult], query: str
    ) -> str:
        context_list = None
        context_result = None
        logger.info(
            f"Generating response with length of context list : {len(retrieval_results)}"
        )
        if len(retrieval_results) > 0:
            context_list = [
                f"{i}. {r.chunk.content}"
                for i, r in enumerate(retrieval_results, start=1)
            ]
            context_result = "\n---\n".join(context_list)
        else:
            context_result = "Không có bài báo nào được tìm thấy."

        return self.DEFAULT_PROMPT_TEMPLATE.format(context=context_result, query=query)
