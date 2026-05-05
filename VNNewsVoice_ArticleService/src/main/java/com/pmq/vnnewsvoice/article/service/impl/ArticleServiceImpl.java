package com.pmq.vnnewsvoice.article.service.impl;

import com.pmq.vnnewsvoice.article.enums.ArticleStatus;
import com.pmq.vnnewsvoice.article.pojo.Article;
import com.pmq.vnnewsvoice.article.repository.ArticleRepository;
import com.pmq.vnnewsvoice.article.repository.RepositoryPageable;
import com.pmq.vnnewsvoice.article.repository.specification.ArticleSpecifications;
import com.pmq.vnnewsvoice.article.service.ArticleService;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.domain.Specification;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class ArticleServiceImpl implements ArticleService {
  private static final Sort DEFAULT_SORT =
      Sort.by(
          Sort.Order.desc("publishedDate"),
          Sort.Order.desc("createdAt"),
          Sort.Order.desc("updatedAt"));

  private static final Sort DELETED_SORT =
      Sort.by(
          Sort.Order.desc("deletedAt"), Sort.Order.desc("updatedAt"), Sort.Order.desc("createdAt"));

  private final ArticleRepository articleRepository;

  @Override
  @Transactional
  public Article addArticle(Article article) {
    if (!isArticleValid(article)) {
      throw new IllegalArgumentException("Invalid article data");
    }
    return articleRepository.save(article);
  }

  @Override
  @Transactional(readOnly = true)
  public Optional<Article> getArticleById(UUID id) {
    if (id == null) {
      return Optional.empty();
    }
    return articleRepository.findById(id);
  }

  @Override
  @Transactional(readOnly = true)
  public Optional<Article> getPublishedArticleById(UUID id) {
    if (id == null) {
      return Optional.empty();
    }
    return articleRepository.findByIdAndStatusAndIsActiveTrue(id, ArticleStatus.PUBLISHED);
  }

  @Override
  @Transactional(readOnly = true)
  public List<Article> getArticlesByCategoryId(Long categoryId) {
    if (categoryId == null) {
      return List.of();
    }
    return articleRepository.findByCategoryId_IdAndIsActiveTrueOrderByPublishedDateDesc(categoryId);
  }

  @Override
  @Transactional(readOnly = true)
  public List<Article> searchArticles(Map<String, String> filters, Map<String, String> params) {
    if (filters == null || filters.isEmpty()) {
      return getArticles(params);
    }
    Sort sort = resolveDefaultSort(filters);
    Specification<Article> spec = ArticleSpecifications.fromFilters(filters);
    return RepositoryPageable.fromParams(params, 10, sort)
        .map(pageable -> articleRepository.findAll(spec, pageable).getContent())
        .orElse(articleRepository.findAll(spec, sort));
  }

  @Override
  @Transactional(readOnly = true)
  public List<Article> getArticles(Map<String, String> params) {
    Sort sort = resolveDefaultSort(params);
    if (params == null || params.isEmpty()) {
      return articleRepository.findAll(sort);
    }
    Specification<Article> spec = ArticleSpecifications.fromFilters(params);
    return RepositoryPageable.fromParams(params, 10, sort)
        .map(pageable -> articleRepository.findAll(spec, pageable).getContent())
        .orElse(articleRepository.findAll(spec, sort));
  }

  @Override
  @Transactional(readOnly = true)
  public List<Article> getAllArticlesUnpaged(Map<String, String> filters) {
    Sort sort = resolveDefaultSort(filters);
    if (filters == null || filters.isEmpty()) {
      return articleRepository.findAll(sort);
    }
    Specification<Article> spec = ArticleSpecifications.fromFilters(filters);
    return articleRepository.findAll(spec, sort);
  }

  private Sort resolveDefaultSort(Map<String, String> filters) {
    if (filters == null) {
      return DEFAULT_SORT;
    }

    String status = filters.get("status");
    if (status == null || status.isBlank()) {
      return DEFAULT_SORT;
    }

    String normalizedStatus = status.trim().toUpperCase(Locale.ROOT);
    if ("DELETE".equals(normalizedStatus)) {
      normalizedStatus = "DELETED";
    }

    if ("DELETED".equals(normalizedStatus)) {
      return DELETED_SORT;
    }

    return DEFAULT_SORT;
  }

  @Override
  @Transactional
  public Article updateArticle(Article article) {
    if (article == null || article.getId() == null) {
      throw new IllegalArgumentException("Invalid article data");
    }
    if (!articleRepository.existsById(article.getId())) {
      throw new IllegalArgumentException("Article not found with id: " + article.getId());
    }
    return articleRepository.save(article);
  }

  @Override
  @Transactional
  public boolean deleteArticle(UUID id) {
    if (id == null) {
      return false;
    }
    if (!articleRepository.existsById(id)) {
      return false;
    }
    articleRepository.deleteById(id);
    return true;
  }

  @Override
  @Transactional(readOnly = true)
  public long countArticles() {
    return articleRepository.count();
  }

  @Override
  @Transactional(readOnly = true)
  public long countSearchArticles(Map<String, String> filters) {
    if (filters == null || filters.isEmpty()) {
      return articleRepository.count();
    }
    Specification<Article> spec = ArticleSpecifications.fromFilters(filters);
    return articleRepository.count(spec);
  }

  @Override
  @Transactional(readOnly = true)
  public List<Article> searchByKeyword(String keyword, int page, int pageSize) {
    int offset = (page - 1) * pageSize;
    return articleRepository.fullTextSearch(keyword, pageSize, offset);
  }

  @Override
  @Transactional(readOnly = true)
  public long countByKeyword(String keyword) {
    return articleRepository.countFullTextSearch(keyword);
  }

  @Override
  @Transactional(readOnly = true)
  public boolean isArticleValid(Article article) {
    if (article == null) {
      return false;
    }
    if (article.getCategoryId() == null || article.getCategoryId().getId() == null) {
      return false;
    }
    if (article.getOriginalUrl() == null || article.getOriginalUrl().isEmpty()) {
      return false;
    }
    if (article.getTitle() == null || article.getTitle().isEmpty()) {
      return false;
    }
    return true;
  }
}
