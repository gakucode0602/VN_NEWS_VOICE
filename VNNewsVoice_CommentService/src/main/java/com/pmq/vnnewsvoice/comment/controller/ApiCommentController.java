package com.pmq.vnnewsvoice.comment.controller;

import com.pmq.vnnewsvoice.comment.dto.ApiResponse;
import com.pmq.vnnewsvoice.comment.dto.ApiResult;
import com.pmq.vnnewsvoice.comment.dto.CommentDto;
import com.pmq.vnnewsvoice.comment.dto.CommentListResponse;
import com.pmq.vnnewsvoice.comment.dto.CommentRequest;
import com.pmq.vnnewsvoice.comment.facade.ApiCommentFacade;
import com.pmq.vnnewsvoice.comment.pojo.CustomUserDetails;
import jakarta.validation.Valid;
import java.util.Map;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api")
public class ApiCommentController {

  private final ApiCommentFacade apiCommentFacade;

  // ─── Public endpoints ────────────────────────────────────────────────────────

  @GetMapping("/articles/{articleId}/comments")
  public ResponseEntity<ApiResponse<CommentListResponse>> getCommentsByArticle(
      @PathVariable String articleId, @RequestParam Map<String, String> params) {
    return buildResponse(apiCommentFacade.getCommentsByArticleId(articleId, params));
  }

  @GetMapping("/articles/{articleId}/comments/count")
  public ResponseEntity<ApiResponse<Long>> countCommentsByArticle(@PathVariable String articleId) {
    // Direct service call for a lightweight count endpoint
    ApiResult<CommentListResponse> result =
        apiCommentFacade.getCommentsByArticleId(articleId, null);
    long count =
        result.getResult() != null && result.getResult().getPagination() != null
            ? result.getResult().getPagination().getTotalItems()
            : 0L;
    return ResponseEntity.ok(
        ApiResponse.<Long>builder().success(true).code(200).result(count).build());
  }

  @GetMapping("/comments/{id}")
  public ResponseEntity<ApiResponse<CommentDto>> getCommentById(@PathVariable Long id) {
    return buildResponse(apiCommentFacade.getCommentById(id));
  }

  // ─── Secure endpoints — READER only ─────────────────────────────────────────

  @GetMapping("/secure/comments")
  @PreAuthorize("hasRole('READER')")
  public ResponseEntity<ApiResponse<CommentListResponse>> getMyComments(
      @RequestParam Map<String, String> params,
      @AuthenticationPrincipal CustomUserDetails principal) {
    return buildResponse(apiCommentFacade.getCommentsByCurrentUser(params, principal));
  }

  @PostMapping("/secure/articles/{articleId}/comments")
  @PreAuthorize("hasRole('READER')")
  public ResponseEntity<ApiResponse<CommentDto>> createComment(
      @PathVariable String articleId,
      @Valid @RequestBody CommentRequest request,
      @AuthenticationPrincipal CustomUserDetails principal) {
    return buildResponse(apiCommentFacade.createComment(request, articleId, principal));
  }

  @DeleteMapping("/secure/comments/{id}")
  @PreAuthorize("hasRole('READER')")
  public ResponseEntity<ApiResponse<Void>> deleteComment(
      @PathVariable Long id, @AuthenticationPrincipal CustomUserDetails principal) {
    return buildResponse(apiCommentFacade.deleteComment(id, principal));
  }

  // ─── Helper ──────────────────────────────────────────────────────────────────

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
