package com.pmq.vnnewsvoice.comment.repository;

import com.pmq.vnnewsvoice.comment.pojo.CommentLike;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

@Repository
public interface CommentLikeRepository extends JpaRepository<CommentLike, Long> {

  Optional<CommentLike> findByCommentIdAndUserId(Long commentId, Long userId);

  boolean existsByCommentIdAndUserId(Long commentId, Long userId);

  long countByCommentId(Long commentId);

  void deleteByCommentIdAndUserId(Long commentId, Long userId);
}
