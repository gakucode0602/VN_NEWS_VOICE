package com.pmq.vnnewsvoice.comment.service.impl;

import com.pmq.vnnewsvoice.comment.dto.CommentLikeDto;
import com.pmq.vnnewsvoice.comment.pojo.Comment;
import com.pmq.vnnewsvoice.comment.pojo.CommentLike;
import com.pmq.vnnewsvoice.comment.repository.CommentLikeRepository;
import com.pmq.vnnewsvoice.comment.service.CommentLikeService;
import java.util.Date;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
public class CommentLikeServiceImpl implements CommentLikeService {

  private final CommentLikeRepository commentLikeRepository;

  @Override
  @Transactional
  public CommentLikeDto toggleLike(Long commentId, Long userId) {
    Optional<CommentLike> existing =
        commentLikeRepository.findByCommentIdAndUserId(commentId, userId);

    boolean isLiked;
    if (existing.isPresent()) {
      // Already liked → unlike
      commentLikeRepository.delete(existing.get());
      isLiked = false;
    } else {
      // Not liked yet → like
      CommentLike like = new CommentLike();
      Comment comment = new Comment(commentId);
      like.setComment(comment);
      like.setUserId(userId);
      like.setCreatedAt(new Date());
      commentLikeRepository.save(like);
      isLiked = true;
    }

    long likeCount = commentLikeRepository.countByCommentId(commentId);
    return new CommentLikeDto(commentId, isLiked, likeCount);
  }

  @Override
  public boolean isLikedByUser(Long commentId, Long userId) {
    return commentLikeRepository.existsByCommentIdAndUserId(commentId, userId);
  }

  @Override
  public long countLikesByCommentId(Long commentId) {
    return commentLikeRepository.countByCommentId(commentId);
  }
}
