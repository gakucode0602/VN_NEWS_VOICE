package com.pmq.vnnewsvoice.article.controller;

import com.pmq.vnnewsvoice.article.dto.ApiResponse;
import com.pmq.vnnewsvoice.article.dto.ApiResult;
import com.pmq.vnnewsvoice.article.dto.ArticleLikeCountResponse;
import com.pmq.vnnewsvoice.article.dto.ArticleLikeListResponse;
import com.pmq.vnnewsvoice.article.dto.ArticleLikeStatusResponse;
import com.pmq.vnnewsvoice.article.facade.ApiArticleLikeFacade;
import com.pmq.vnnewsvoice.article.pojo.CustomUserDetails;
import java.util.Map;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api")
public class ApiArticleLikeController {
  private final ApiArticleLikeFacade apiArticleLikeFacade;

  @GetMapping("/secure/articles/{id}/is-liked")
  @PreAuthorize("hasRole('READER')")
  public ResponseEntity<ApiResponse<ArticleLikeStatusResponse>> getIsLikedArticle(
      @PathVariable UUID id, @AuthenticationPrincipal CustomUserDetails principal) {
    ApiResult<ArticleLikeStatusResponse> result =
        apiArticleLikeFacade.getIsLikedArticle(id, principal);
    return buildResponse(result);
  }

  @GetMapping("/articles/{id}/article-like")
  public ResponseEntity<ApiResponse<ArticleLikeCountResponse>> getNumberOfArticleLike(
      @PathVariable UUID id) {
    ApiResult<ArticleLikeCountResponse> result = apiArticleLikeFacade.getNumberOfArticleLike(id);
    return buildResponse(result);
  }

  @GetMapping("/secure/article-likes")
  @PreAuthorize("hasRole('READER')")
  public ResponseEntity<ApiResponse<ArticleLikeListResponse>> getPersonalArticleLikes(
      @AuthenticationPrincipal CustomUserDetails principal,
      @RequestParam Map<String, String> params) {
    ApiResult<ArticleLikeListResponse> result =
        apiArticleLikeFacade.getPersonalArticleLikes(principal, params);
    return buildResponse(result);
  }

  @PostMapping("/secure/articles/{id}/add-article-like")
  @PreAuthorize("hasRole('READER')")
  public ResponseEntity<ApiResponse<Void>> addArticleLike(
      @PathVariable("id") UUID id, @AuthenticationPrincipal CustomUserDetails principal) {
    ApiResult<Void> result = apiArticleLikeFacade.addArticleLike(id, principal);
    return buildResponse(result);
  }

  @DeleteMapping("/secure/articles/{id}/delete-article-like")
  @PreAuthorize("hasRole('READER')")
  public ResponseEntity<ApiResponse<Void>> deleteArticleLike(
      @PathVariable("id") UUID id, @AuthenticationPrincipal CustomUserDetails principal) {
    ApiResult<Void> result = apiArticleLikeFacade.deleteArticleLike(id, principal);
    return buildResponse(result);
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
