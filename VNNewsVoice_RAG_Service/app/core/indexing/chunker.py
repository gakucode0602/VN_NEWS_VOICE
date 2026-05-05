import uuid
from typing import Any, Dict, List, Tuple

from underthesea import sent_tokenize

from app.models.domain.article import Article, DocumentChunk


class Chunker:
    def __init__(
        self,
        chunk_size: int = 600,
        overlap_size: int = 120,
        parent_chunk_size: int = 400,
        children_chunk_size: int = 50,
    ) -> None:
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.parent_chunk_size = parent_chunk_size
        self.children_chunk_size = children_chunk_size

    def chunk(self, article: Article) -> List[DocumentChunk]:
        result = []

        sentences = sent_tokenize(article.content)
        metadata = self._build_metadata(article)

        current_sentence = []
        current_len = 0
        chunk_idx = 0

        first_chunk_content = f"{article.title}\n\n"

        for sent in sentences:
            sent_len = len(sent.split())

            if current_len + sent_len > self.parent_chunk_size and current_sentence:
                content = " ".join(current_sentence)

                if chunk_idx == 0 and article.title:
                    content = first_chunk_content + content

                result.append(
                    DocumentChunk(
                        chunk_id=str(uuid.uuid4()),
                        article_id=article.article_id,
                        content=content,
                        chunk_index=chunk_idx,
                        metadata=metadata,
                    )
                )

                chunk_idx += 1

                overlap_sentences = []
                overlap_len = 0

                for s in reversed(current_sentence):
                    overlap_sentences.insert(0, s)
                    overlap_len += len(s.split())
                    if overlap_len >= self.overlap_size:
                        break

                current_sentence = overlap_sentences
                current_len = overlap_len

            current_sentence.append(sent)
            current_len += sent_len

        if current_sentence:
            content = " ".join(current_sentence)

            if chunk_idx == 0 and article.title:
                content = first_chunk_content + content

            result.append(
                DocumentChunk(
                    chunk_id=str(uuid.uuid4()),
                    article_id=article.article_id,
                    content=content,
                    chunk_index=chunk_idx,
                    metadata=metadata,
                )
            )

        return result

    def _build_metadata(self, article: Article) -> Dict[str, Any]:
        result_dict = {}

        if article.title:
            result_dict["title"] = article.title
        if article.published_at:
            result_dict["published_at"] = article.published_at.isoformat()
        if article.source:
            result_dict["source"] = article.source
        if article.url:
            result_dict["url"] = article.url
        if article.topic:
            result_dict["topic"] = article.topic

        return result_dict

    def chunk_hierarchical(
        self, article: Article
    ) -> Tuple[List[DocumentChunk], List[DocumentChunk]]:
        children = []

        # Can we reuse this ????
        parents = self.chunk(article)
        base_metadata = self._build_metadata(article)

        for idx, big_text in enumerate(parents, start=1):
            parent_content = big_text.content
            parent_id = big_text.chunk_id

            small_texts = self._split_text(parent_content, self.children_chunk_size)

            for c_idx, small_text in enumerate(small_texts, start=1):
                # Generate a valid UUID for Qdrant using uuid5
                child_id = str(uuid.uuid5(uuid.NAMESPACE_OID, f"{parent_id}_c_{c_idx}"))

                # Merge base metadata with parent_id so Qdrant has URL and Title
                child_metadata = base_metadata.copy()
                child_metadata["parent_id"] = parent_id

                children.append(
                    DocumentChunk(
                        chunk_id=child_id,
                        article_id=article.article_id,
                        content=small_text,
                        chunk_index=c_idx,
                        metadata=child_metadata,
                        parent_id=parent_id,
                    )
                )

        return parents, children

    def _split_text(self, content: str, size: int) -> List[str]:
        results = []
        sentences = sent_tokenize(content)
        current_sentence = []
        current_len = 0

        for sent in sentences:
            sent_len = len(sent.split())
            if current_len + sent_len > size and current_sentence:
                joined_content = " ".join(current_sentence)
                results.append(joined_content)

                overlap_sentences = []
                overlap_len = 0
                for s in reversed(current_sentence):
                    overlap_sentences.insert(0, s)
                    overlap_len += len(s.split())
                    if overlap_len >= size:
                        break

                current_sentence = overlap_sentences
                current_len = overlap_len

            current_sentence.append(sent)
            current_len += sent_len

        if current_sentence:
            joined_content = " ".join(current_sentence)
            # Prevent re-adding the exact same tail if loop ended right after split
            if not results or results[-1] != joined_content:
                results.append(joined_content)

        return results
