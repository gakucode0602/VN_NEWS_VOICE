package com.pmq.vnnewsvoice.article.facade;

import com.pmq.vnnewsvoice.article.dto.ArticleDetailResponse;
import com.pmq.vnnewsvoice.article.dto.ArticleListRequest;
import com.pmq.vnnewsvoice.article.dto.ArticleListResponse;
import com.pmq.vnnewsvoice.article.dto.RelatedArticlesResponse;
import java.time.Instant;
import java.util.List;
import java.util.Optional;
import java.util.UUID;

public interface ApiArticleFacade {
  ArticleListResponse listArticles(ArticleListRequest request);

  Optional<ArticleDetailResponse> getArticleDetail(UUID id);

  Optional<RelatedArticlesResponse> getRelatedArticles(UUID id, int limit);

  /**
   * Export bài PUBLISHED theo page để RAG reindex vào Qdrant. Paginated để tránh OOM.
   *
   * @param since null = full export; có giá trị = delta sync từ mốc đó
   * @param page 1-indexed
   * @param size số bài mỗi page (khuyến nghị 200)
   */
  List<ArticleDetailResponse> exportArticles(Instant since, int page, int size);
}
