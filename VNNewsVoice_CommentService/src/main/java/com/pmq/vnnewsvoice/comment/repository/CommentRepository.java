package com.pmq.vnnewsvoice.comment.repository;

import com.pmq.vnnewsvoice.comment.pojo.Comment;
import java.util.List;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

@Repository
public interface CommentRepository extends JpaRepository<Comment, Long> {

  // Active comments for an article (soft delete aware)
  @Query(
      "SELECT c FROM Comment c WHERE c.articleId = :articleId AND c.deletedAt IS NULL AND c.hiddenByArticle = false AND c.hiddenByUser = false AND c.commentReply IS NULL ORDER BY c.createdAt DESC")
  List<Comment> findTopLevelByArticleId(@Param("articleId") String articleId, Sort sort);

  @Query(
      "SELECT c FROM Comment c WHERE c.articleId = :articleId AND c.deletedAt IS NULL AND c.hiddenByArticle = false AND c.hiddenByUser = false AND c.commentReply IS NULL")
  List<Comment> findTopLevelByArticleId(@Param("articleId") String articleId, Pageable pageable);

  @Query(
      "SELECT COUNT(c) FROM Comment c WHERE c.articleId = :articleId AND c.deletedAt IS NULL AND c.hiddenByArticle = false AND c.hiddenByUser = false AND c.commentReply IS NULL")
  long countTopLevelByArticleId(@Param("articleId") String articleId);

  @Query(
      "SELECT COUNT(c) FROM Comment c WHERE c.articleId = :articleId AND c.deletedAt IS NULL AND c.hiddenByArticle = false AND c.hiddenByUser = false")
  long countActiveByArticleId(@Param("articleId") String articleId);

  // Comments by a specific user (active only)
  List<Comment> findByUserIdAndDeletedAtIsNullAndHiddenByArticleFalse(Long userId, Sort sort);

  List<Comment> findByUserIdAndDeletedAtIsNullAndHiddenByArticleFalse(
      Long userId, Pageable pageable);

  long countByUserIdAndDeletedAtIsNullAndHiddenByArticleFalse(Long userId);

  // Replies to a parent comment (active only) — explicit path traversal: commentReply.id
  List<Comment> findByCommentReply_IdAndDeletedAtIsNullAndHiddenByArticleFalseAndHiddenByUserFalse(
      Long parentId, Sort sort);

  @Modifying
  @Query(
      "UPDATE Comment c SET c.hiddenByArticle = true WHERE c.articleId = :articleId AND c.hiddenByArticle = false")
  int hideByArticleId(@Param("articleId") String articleId);

  @Modifying
  @Query(
      "UPDATE Comment c SET c.hiddenByArticle = false WHERE c.articleId = :articleId AND c.hiddenByArticle = true")
  int restoreByArticleId(@Param("articleId") String articleId);

  @Modifying
  @Query(
      "UPDATE Comment c SET c.hiddenByUser = true WHERE c.userId = :userId AND c.hiddenByUser = false AND c.deletedAt IS NULL")
  int hideByUserId(@Param("userId") Long userId);

  @Modifying
  @Query(
      "UPDATE Comment c SET c.hiddenByUser = false WHERE c.userId = :userId AND c.hiddenByUser = true")
  int restoreByUserId(@Param("userId") Long userId);

  @Modifying
  @Query("DELETE FROM Comment c WHERE c.articleId = :articleId")
  int hardDeleteByArticleId(@Param("articleId") String articleId);
}
