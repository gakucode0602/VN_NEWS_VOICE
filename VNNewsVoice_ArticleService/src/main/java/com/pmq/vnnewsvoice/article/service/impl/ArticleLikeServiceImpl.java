package com.pmq.vnnewsvoice.article.service.impl;

import com.pmq.vnnewsvoice.article.enums.ArticleStatus;
import com.pmq.vnnewsvoice.article.pojo.ArticleLike;
import com.pmq.vnnewsvoice.article.repository.ArticleLikeRepository;
import com.pmq.vnnewsvoice.article.repository.RepositoryPageable;
import com.pmq.vnnewsvoice.article.service.ArticleLikeService;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class ArticleLikeServiceImpl implements ArticleLikeService {
  private final ArticleLikeRepository articleLikeRepository;

  @Override
  @Transactional
  public ArticleLike addArticleLike(ArticleLike articleLike) {
    if (articleLike == null
        || articleLike.getArticleId() == null
        || articleLike.getReaderId() == null) {
      throw new IllegalArgumentException("Invalid article like data");
    }
    return articleLikeRepository.save(articleLike);
  }

  @Override
  @Transactional(readOnly = true)
  public List<ArticleLike> getArticleLikesByArticleId(UUID articleId) {
    if (articleId == null) {
      return List.of();
    }
    return articleLikeRepository.findByArticleId_Id(articleId);
  }

  @Override
  @Transactional(readOnly = true)
  public List<ArticleLike> getArticleLikesByUserId(Long userId) {
    if (userId == null) {
      return List.of();
    }
    return articleLikeRepository.findByReaderId(userId);
  }

  @Override
  @Transactional
  public boolean deleteArticleLike(Long id) {
    if (id == null || !articleLikeRepository.existsById(id)) {
      return false;
    }
    articleLikeRepository.deleteById(id);
    return true;
  }

  @Override
  @Transactional(readOnly = true)
  public long countArticleLikesByArticleId(UUID articleId) {
    if (articleId == null) {
      return 0;
    }
    return articleLikeRepository.countByArticleId_Id(articleId);
  }

  @Override
  @Transactional(readOnly = true)
  public long countArticleLikeByUserId(Long userId) {
    if (userId == null || userId <= 0) {
      return 0;
    }
    return articleLikeRepository.countByReaderId(userId);
  }

  @Override
  @Transactional(readOnly = true)
  public List<ArticleLike> getArticlesLikeByUserId(Long userId, Map<String, String> params) {
    if (userId == null || userId <= 0) {
      return List.of();
    }
    if (params == null || params.isEmpty()) {
      return articleLikeRepository.findByReaderIdAndArticleId_IsActiveTrueAndArticleId_Status(
          userId, ArticleStatus.PUBLISHED);
    }
    return RepositoryPageable.fromParams(params, 10, Sort.unsorted())
        .map(
            pageable ->
                articleLikeRepository.findByReaderIdAndArticleId_IsActiveTrueAndArticleId_Status(
                    userId, ArticleStatus.PUBLISHED, pageable))
        .orElse(
            articleLikeRepository.findByReaderIdAndArticleId_IsActiveTrueAndArticleId_Status(
                userId, ArticleStatus.PUBLISHED));
  }

  @Override
  @Transactional(readOnly = true)
  public Optional<ArticleLike> getArticleLikeByUserIdAndArticleId(Long userId, UUID articleId) {
    if (userId == null || userId <= 0 || articleId == null) {
      return Optional.empty();
    }
    return articleLikeRepository
        .findByReaderIdAndArticleId_IdAndArticleId_IsActiveTrueAndArticleId_Status(
            userId, articleId, ArticleStatus.PUBLISHED);
  }

  @Override
  @Transactional
  public boolean deleteArticleLikesByUserId(Long userId) {
    if (userId == null || userId <= 0) {
      return false;
    }
    long deletedCount = articleLikeRepository.deleteByReaderId(userId);
    return deletedCount > 0;
  }

  @Override
  @Transactional
  public boolean deleteArticleLikesByUserIdAndArticleId(Long userId, UUID articleId) {
    if (userId == null || userId <= 0 || articleId == null) {
      return false;
    }
    long deletedCount = articleLikeRepository.deleteByReaderIdAndArticleId_Id(userId, articleId);
    return deletedCount > 0;
  }
}
