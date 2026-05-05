package com.pmq.vnnewsvoice.comment.service.impl;

import com.pmq.vnnewsvoice.comment.pojo.Comment;
import com.pmq.vnnewsvoice.comment.repository.CommentRepository;
import com.pmq.vnnewsvoice.comment.repository.RepositoryPageable;
import com.pmq.vnnewsvoice.comment.service.CommentService;
import java.util.Date;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Sort;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.util.StringUtils;

@Service
@RequiredArgsConstructor
public class CommentServiceImpl implements CommentService {

  private final CommentRepository commentRepository;

  @Override
  @Transactional
  public Comment addComment(Comment comment) {
    if (comment == null) {
      throw new IllegalArgumentException("Comment cannot be null");
    }
    if (comment.getCreatedAt() == null) {
      comment.setCreatedAt(new Date());
    }
    return commentRepository.save(comment);
  }

  @Override
  public Optional<Comment> getCommentById(Long id) {
    if (id == null || id <= 0) return Optional.empty();
    return commentRepository.findById(id);
  }

  @Override
  public List<Comment> getTopLevelCommentsByArticleId(
      String articleId, Map<String, String> params) {
    if (!StringUtils.hasText(articleId)) return List.of();
    Sort sort = Sort.by(Sort.Direction.DESC, "createdAt");
    return RepositoryPageable.fromParams(params, 10, sort)
        .map(pageable -> commentRepository.findTopLevelByArticleId(articleId, pageable))
        .orElse(commentRepository.findTopLevelByArticleId(articleId, sort));
  }

  @Override
  public long countCommentsByArticleId(String articleId) {
    if (!StringUtils.hasText(articleId)) return 0;
    return commentRepository.countActiveByArticleId(articleId);
  }

  @Override
  public long countTopLevelCommentsByArticleId(String articleId) {
    if (!StringUtils.hasText(articleId)) return 0;
    return commentRepository.countTopLevelByArticleId(articleId);
  }

  @Override
  public List<Comment> getRepliesByParentId(Long parentId) {
    if (parentId == null || parentId <= 0) return List.of();
    return commentRepository
        .findByCommentReply_IdAndDeletedAtIsNullAndHiddenByArticleFalseAndHiddenByUserFalse(
            parentId, Sort.by(Sort.Direction.ASC, "createdAt"));
  }

  @Override
  public List<Comment> getCommentsByUserId(Long userId, Map<String, String> params) {
    if (userId == null || userId <= 0) return List.of();
    Sort sort = Sort.by(Sort.Direction.DESC, "createdAt");
    return RepositoryPageable.fromParams(params, 10, sort)
        .map(
            pageable ->
                commentRepository.findByUserIdAndDeletedAtIsNullAndHiddenByArticleFalse(
                    userId, pageable))
        .orElse(
            commentRepository.findByUserIdAndDeletedAtIsNullAndHiddenByArticleFalse(userId, sort));
  }

  @Override
  public long countCommentsByUserId(Long userId) {
    if (userId == null || userId <= 0) return 0;
    return commentRepository.countByUserIdAndDeletedAtIsNullAndHiddenByArticleFalse(userId);
  }

  @Override
  @Transactional
  public int hideCommentsByArticleId(String articleId) {
    if (!StringUtils.hasText(articleId)) return 0;
    return commentRepository.hideByArticleId(articleId);
  }

  @Override
  @Transactional
  public int restoreCommentsByArticleId(String articleId) {
    if (!StringUtils.hasText(articleId)) return 0;
    return commentRepository.restoreByArticleId(articleId);
  }

  @Override
  @Transactional
  public int hardDeleteCommentsByArticleId(String articleId) {
    if (!StringUtils.hasText(articleId)) return 0;
    return commentRepository.hardDeleteByArticleId(articleId);
  }

  @Override
  @Transactional
  public int hideCommentsByUserId(Long userId) {
    if (userId == null || userId <= 0) return 0;
    return commentRepository.hideByUserId(userId);
  }

  @Override
  @Transactional
  public int restoreCommentsByUserId(Long userId) {
    if (userId == null || userId <= 0) return 0;
    return commentRepository.restoreByUserId(userId);
  }

  @Override
  @Transactional
  public boolean softDeleteComment(Long id) {
    return commentRepository
        .findById(id)
        .map(
            comment -> {
              comment.setDeletedAt(new Date());
              commentRepository.save(comment);
              return true;
            })
        .orElse(false);
  }
}
