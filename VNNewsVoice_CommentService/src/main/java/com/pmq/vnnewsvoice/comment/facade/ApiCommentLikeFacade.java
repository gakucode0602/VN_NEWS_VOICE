package com.pmq.vnnewsvoice.comment.facade;

import com.pmq.vnnewsvoice.comment.dto.ApiResult;
import com.pmq.vnnewsvoice.comment.dto.CommentLikeDto;
import com.pmq.vnnewsvoice.comment.pojo.CustomUserDetails;

public interface ApiCommentLikeFacade {

  ApiResult<CommentLikeDto> toggleLike(Long commentId, CustomUserDetails principal);

  ApiResult<CommentLikeDto> isLikedByCurrentUser(Long commentId, CustomUserDetails principal);
}
