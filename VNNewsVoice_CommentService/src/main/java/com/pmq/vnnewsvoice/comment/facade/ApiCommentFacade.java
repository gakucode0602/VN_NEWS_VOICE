package com.pmq.vnnewsvoice.comment.facade;

import com.pmq.vnnewsvoice.comment.dto.ApiResult;
import com.pmq.vnnewsvoice.comment.dto.CommentDto;
import com.pmq.vnnewsvoice.comment.dto.CommentListResponse;
import com.pmq.vnnewsvoice.comment.dto.CommentRequest;
import com.pmq.vnnewsvoice.comment.pojo.CustomUserDetails;
import java.util.Map;

public interface ApiCommentFacade {

  ApiResult<CommentListResponse> getCommentsByArticleId(
      String articleId, Map<String, String> params);

  ApiResult<CommentDto> getCommentById(Long id);

  ApiResult<CommentListResponse> getCommentsByCurrentUser(
      Map<String, String> params, CustomUserDetails principal);

  ApiResult<CommentDto> createComment(
      CommentRequest request, String articleId, CustomUserDetails principal);

  ApiResult<Void> deleteComment(Long commentId, CustomUserDetails principal);
}
