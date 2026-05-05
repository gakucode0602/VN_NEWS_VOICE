package com.pmq.vnnewsvoice.article.repository;

import com.pmq.vnnewsvoice.article.enums.ArticleStatus;
import com.pmq.vnnewsvoice.article.pojo.ArticleLike;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

/**
 * ArticleLike repository for ArticleService. Note: readerId stores UserInfo.id (from JWT claims),
 * not Reader.id from auth_db.
 */
public interface ArticleLikeRepository extends JpaRepository<ArticleLike, Long> {

  List<ArticleLike> findByArticleId_Id(UUID articleId);

  List<ArticleLike> findByReaderId(Long readerId);

  long countByArticleId_Id(UUID articleId);

  long countByReaderId(Long readerId);

  List<ArticleLike> findByReaderIdAndArticleId_IsActiveTrueAndArticleId_Status(
      Long readerId, ArticleStatus status);

  List<ArticleLike> findByReaderIdAndArticleId_IsActiveTrueAndArticleId_Status(
      Long readerId, ArticleStatus status, Pageable pageable);

  Optional<ArticleLike> findByReaderIdAndArticleId_IdAndArticleId_IsActiveTrueAndArticleId_Status(
      Long readerId, UUID articleId, ArticleStatus status);

  long deleteByReaderId(Long readerId);

  long deleteByReaderIdAndArticleId_Id(Long readerId, UUID articleId);
}
