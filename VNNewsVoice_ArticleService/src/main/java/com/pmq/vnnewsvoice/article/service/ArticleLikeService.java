package com.pmq.vnnewsvoice.article.service;

import com.pmq.vnnewsvoice.article.pojo.ArticleLike;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

public interface ArticleLikeService {
  ArticleLike addArticleLike(ArticleLike articleLike);

  List<ArticleLike> getArticleLikesByArticleId(UUID articleId);

  List<ArticleLike> getArticleLikesByUserId(Long userId);

  boolean deleteArticleLike(Long id);

  long countArticleLikesByArticleId(UUID articleId);

  long countArticleLikeByUserId(Long userId);

  List<ArticleLike> getArticlesLikeByUserId(Long userId, Map<String, String> params);

  Optional<ArticleLike> getArticleLikeByUserIdAndArticleId(Long userId, UUID articleId);

  boolean deleteArticleLikesByUserId(Long userId);

  boolean deleteArticleLikesByUserIdAndArticleId(Long userId, UUID articleId);
}
