package com.pmq.vnnewsvoice.article.service;

import com.pmq.vnnewsvoice.article.pojo.Article;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

public interface ArticleService {
  Article addArticle(Article article);

  Optional<Article> getArticleById(UUID id);

  Optional<Article> getPublishedArticleById(UUID id);

  List<Article> getArticlesByCategoryId(Long categoryId);

  List<Article> searchArticles(Map<String, String> filters, Map<String, String> params);

  List<Article> getArticles(Map<String, String> params);

  List<Article> getAllArticlesUnpaged(Map<String, String> filters);

  Article updateArticle(Article article);

  boolean deleteArticle(UUID id);

  long countArticles();

  long countSearchArticles(Map<String, String> filters);

  List<Article> searchByKeyword(String keyword, int page, int pageSize);

  long countByKeyword(String keyword);

  boolean isArticleValid(Article article);
}
