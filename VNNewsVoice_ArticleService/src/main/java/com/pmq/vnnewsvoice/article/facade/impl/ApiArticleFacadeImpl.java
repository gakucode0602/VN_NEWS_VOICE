package com.pmq.vnnewsvoice.article.facade.impl;

import com.pmq.vnnewsvoice.article.dto.ArticleBlockResponse;
import com.pmq.vnnewsvoice.article.dto.ArticleDetailResponse;
import com.pmq.vnnewsvoice.article.dto.ArticleListRequest;
import com.pmq.vnnewsvoice.article.dto.ArticleListResponse;
import com.pmq.vnnewsvoice.article.dto.ArticleResponse;
import com.pmq.vnnewsvoice.article.dto.RelatedArticlesResponse;
import com.pmq.vnnewsvoice.article.facade.ApiArticleFacade;
import com.pmq.vnnewsvoice.article.helpers.PaginationHelper;
import com.pmq.vnnewsvoice.article.mapper.ApiArticleBlockMapper;
import com.pmq.vnnewsvoice.article.mapper.ApiArticleMapper;
import com.pmq.vnnewsvoice.article.pojo.Article;
import com.pmq.vnnewsvoice.article.pojo.ArticleBlock;
import com.pmq.vnnewsvoice.article.pojo.Category;
import com.pmq.vnnewsvoice.article.service.ArticleBlockService;
import com.pmq.vnnewsvoice.article.service.ArticleService;
import com.pmq.vnnewsvoice.article.utils.Pagination;
import java.time.Instant;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class ApiArticleFacadeImpl implements ApiArticleFacade {
  private static final int DEFAULT_PAGE_SIZE = 10;

  private final ArticleService articleService;
  private final ArticleBlockService articleBlockService;
  private final ApiArticleMapper apiArticleMapper;
  private final ApiArticleBlockMapper apiArticleBlockMapper;
  private final PaginationHelper paginationHelper;

  @Override
  public ArticleListResponse listArticles(ArticleListRequest request) {
    Map<String, String> filters = buildFilters(request);

    String keyword = filters.remove("keyword");
    if (keyword != null) {
      int page = Integer.parseInt(filters.getOrDefault("page", "1"));
      List<Article> articles = articleService.searchByKeyword(keyword, page, DEFAULT_PAGE_SIZE);
      long total = articleService.countByKeyword(keyword);
      Pagination pagination = paginationHelper.createPagination(filters, total, DEFAULT_PAGE_SIZE);
      List<ArticleResponse> articleResponses =
          articles.stream().map(apiArticleMapper::toResponse).toList();
      return new ArticleListResponse(articleResponses, pagination);
    }

    List<Article> articles = articleService.getArticles(filters);
    long totalArticles = articleService.countSearchArticles(filters);
    Pagination pagination =
        paginationHelper.createPagination(filters, totalArticles, DEFAULT_PAGE_SIZE);

    List<ArticleResponse> articleResponses =
        articles.stream().map(apiArticleMapper::toResponse).toList();

    return new ArticleListResponse(articleResponses, pagination);
  }

  @Override
  public Optional<ArticleDetailResponse> getArticleDetail(UUID id) {
    Optional<Article> articleOptional = articleService.getPublishedArticleById(id);
    if (articleOptional.isEmpty()) {
      return Optional.empty();
    }

    Article article = articleOptional.get();
    ArticleResponse articleResponse = apiArticleMapper.toResponse(article);
    List<ArticleBlock> articleBlocks =
        articleBlockService.getArticleBlocksByArticleId(article.getId());
    List<ArticleBlockResponse> articleBlockResponses =
        articleBlocks.stream().map(apiArticleBlockMapper::toResponse).toList();

    return Optional.of(new ArticleDetailResponse(articleResponse, articleBlockResponses));
  }

  @Override
  public Optional<RelatedArticlesResponse> getRelatedArticles(UUID id, int limit) {
    Optional<Article> articleOptional = articleService.getPublishedArticleById(id);
    if (articleOptional.isEmpty()) {
      return Optional.empty();
    }

    Article article = articleOptional.get();
    Category category = article.getCategoryId();
    if (category == null) {
      return Optional.of(new RelatedArticlesResponse(List.of()));
    }

    Map<String, String> filters = new HashMap<>();
    filters.put("categoryId", category.getId().toString());
    filters.put("status", "PUBLISHED");
    filters.put("isActive", "true");

    List<ArticleResponse> relatedArticles =
        articleService.getArticles(filters).stream()
            .filter(related -> !related.getId().equals(article.getId()))
            .limit(limit)
            .map(apiArticleMapper::toResponse)
            .toList();

    return Optional.of(new RelatedArticlesResponse(relatedArticles));
  }

  @Override
  public List<ArticleDetailResponse> exportArticles(Instant since, int page, int size) {
    Map<String, String> filters = new HashMap<>();
    filters.put("status", "PUBLISHED");
    filters.put("isActive", "true");
    filters.put("page", String.valueOf(page));
    filters.put("pageSize", String.valueOf(size));
    if (since != null) {
      filters.put("createdAfter", since.toString());
    }

    List<Article> articles = articleService.getArticles(filters);

    return articles.stream()
        .map(
            article -> {
              ArticleResponse resp = apiArticleMapper.toResponse(article);
              List<ArticleBlock> blocks =
                  articleBlockService.getArticleBlocksByArticleId(article.getId());
              List<ArticleBlockResponse> blockResponses =
                  blocks.stream().map(apiArticleBlockMapper::toResponse).toList();
              return new ArticleDetailResponse(resp, blockResponses);
            })
        .toList();
  }

  private Map<String, String> buildFilters(ArticleListRequest request) {
    Map<String, String> filters = new HashMap<>();

    if (request == null) {
      filters.put("status", "PUBLISHED");
      filters.put("isActive", "true");
      return filters;
    }

    if (hasText(request.getName())) {
      filters.put("keyword", request.getName());
    }

    if (request.getCategoryId() != null) {
      filters.put("categoryId", request.getCategoryId().toString());
    }

    if (request.getGeneratorId() != null) {
      filters.put("generatorId", request.getGeneratorId().toString());
    }

    if (request.getPage() != null) {
      filters.put("page", request.getPage().toString());
    }

    if (hasText(request.getFromDate()) && hasText(request.getToDate())) {
      filters.put("fromDate", request.getFromDate());
      filters.put("toDate", request.getToDate());
    } else if (request.getPublishedDates() != null && request.getPublishedDates() > 0) {
      filters.put("publishedDates", request.getPublishedDates().toString());
    }

    filters.put("status", "PUBLISHED");
    filters.put("isActive", "true");
    return filters;
  }

  private boolean hasText(String value) {
    return value != null && !value.trim().isEmpty();
  }
}
