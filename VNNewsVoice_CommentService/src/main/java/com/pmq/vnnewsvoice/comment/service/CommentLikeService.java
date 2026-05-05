package com.pmq.vnnewsvoice.comment.service;

import com.pmq.vnnewsvoice.comment.dto.CommentLikeDto;

public interface CommentLikeService {

  /**
   * Toggle like on a comment. If user already liked → unlike (delete). If not → like (insert).
   *
   * @return CommentLikeDto with updated isLiked state and likeCount
   */
  CommentLikeDto toggleLike(Long commentId, Long userId);

  boolean isLikedByUser(Long commentId, Long userId);

  long countLikesByCommentId(Long commentId);
}
