package com.pmq.vnnewsvoice.comment.facade.impl;

import com.pmq.vnnewsvoice.comment.dto.ApiResult;
import com.pmq.vnnewsvoice.comment.dto.CommentLikeDto;
import com.pmq.vnnewsvoice.comment.facade.ApiCommentLikeFacade;
import com.pmq.vnnewsvoice.comment.pojo.CustomUserDetails;
import com.pmq.vnnewsvoice.comment.service.CommentLikeService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class ApiCommentLikeFacadeImpl implements ApiCommentLikeFacade {

  private final CommentLikeService commentLikeService;

  @Override
  public ApiResult<CommentLikeDto> toggleLike(Long commentId, CustomUserDetails principal) {
    if (commentId == null || commentId <= 0) {
      return ApiResult.failure(HttpStatus.BAD_REQUEST, "Comment ID không hợp lệ");
    }
    CommentLikeDto result = commentLikeService.toggleLike(commentId, principal.getUserId());
    return ApiResult.success(HttpStatus.OK, result);
  }

  @Override
  public ApiResult<CommentLikeDto> isLikedByCurrentUser(
      Long commentId, CustomUserDetails principal) {
    if (commentId == null || commentId <= 0) {
      return ApiResult.failure(HttpStatus.BAD_REQUEST, "Comment ID không hợp lệ");
    }
    boolean isLiked = commentLikeService.isLikedByUser(commentId, principal.getUserId());
    long likeCount = commentLikeService.countLikesByCommentId(commentId);
    return ApiResult.success(HttpStatus.OK, new CommentLikeDto(commentId, isLiked, likeCount));
  }
}
