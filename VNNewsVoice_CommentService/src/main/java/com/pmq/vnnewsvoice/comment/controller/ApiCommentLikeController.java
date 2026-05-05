package com.pmq.vnnewsvoice.comment.controller;

import com.pmq.vnnewsvoice.comment.dto.ApiResponse;
import com.pmq.vnnewsvoice.comment.dto.ApiResult;
import com.pmq.vnnewsvoice.comment.dto.CommentLikeDto;
import com.pmq.vnnewsvoice.comment.facade.ApiCommentLikeFacade;
import com.pmq.vnnewsvoice.comment.pojo.CustomUserDetails;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/secure/comments")
public class ApiCommentLikeController {

  private final ApiCommentLikeFacade apiCommentLikeFacade;

  /**
   * Toggle like on a comment. If already liked → unlike. If not liked → like. Idempotent from UX
   * perspective.
   */
  @PostMapping("/{commentId}/like")
  @PreAuthorize("hasRole('READER')")
  public ResponseEntity<ApiResponse<CommentLikeDto>> toggleLike(
      @PathVariable Long commentId, @AuthenticationPrincipal CustomUserDetails principal) {
    return buildResponse(apiCommentLikeFacade.toggleLike(commentId, principal));
  }

  /** Check whether the current user has liked a specific comment. */
  @GetMapping("/{commentId}/is-liked")
  @PreAuthorize("hasRole('READER')")
  public ResponseEntity<ApiResponse<CommentLikeDto>> isLiked(
      @PathVariable Long commentId, @AuthenticationPrincipal CustomUserDetails principal) {
    return buildResponse(apiCommentLikeFacade.isLikedByCurrentUser(commentId, principal));
  }

  private <T> ResponseEntity<ApiResponse<T>> buildResponse(ApiResult<T> result) {
    return ResponseEntity.status(result.getStatus())
        .body(
            ApiResponse.<T>builder()
                .success(result.isSuccess())
                .code(result.getStatus().value())
                .message(result.getMessage())
                .result(result.getResult())
                .build());
  }
}
