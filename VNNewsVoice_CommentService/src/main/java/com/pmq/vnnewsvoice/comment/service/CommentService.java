package com.pmq.vnnewsvoice.comment.service;

import com.pmq.vnnewsvoice.comment.pojo.Comment;
import java.util.List;
import java.util.Map;
import java.util.Optional;

public interface CommentService {

  Comment addComment(Comment comment);

  Optional<Comment> getCommentById(Long id);

  List<Comment> getTopLevelCommentsByArticleId(String articleId, Map<String, String> params);

  long countCommentsByArticleId(String articleId);

  long countTopLevelCommentsByArticleId(String articleId);

  List<Comment> getRepliesByParentId(Long parentId);

  List<Comment> getCommentsByUserId(Long userId, Map<String, String> params);

  long countCommentsByUserId(Long userId);

  int hideCommentsByArticleId(String articleId);

  int restoreCommentsByArticleId(String articleId);

  int hardDeleteCommentsByArticleId(String articleId);

  int hideCommentsByUserId(Long userId);

  int restoreCommentsByUserId(Long userId);

  /**
   * Soft-delete: set deletedAt = now(). Only the comment owner should call this.
   *
   * @return true if the comment existed and was deleted, false if not found
   */
  boolean softDeleteComment(Long id);
}
