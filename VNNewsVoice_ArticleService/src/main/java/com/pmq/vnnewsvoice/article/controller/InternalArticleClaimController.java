package com.pmq.vnnewsvoice.article.controller;

import com.pmq.vnnewsvoice.article.dto.ApiResponse;
import com.pmq.vnnewsvoice.article.dto.ArticleClaimRequest;
import com.pmq.vnnewsvoice.article.dto.ArticleClaimResponse;
import com.pmq.vnnewsvoice.article.service.ArticleClaimService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/internal/articles")
public class InternalArticleClaimController {
  private final ArticleClaimService articleClaimService;

  @PostMapping("/claim")
  public ResponseEntity<ApiResponse<ArticleClaimResponse>> claimArticle(
      @Valid @RequestBody ArticleClaimRequest request) {
    ArticleClaimResponse result = articleClaimService.claim(request);
    return ResponseEntity.ok(
        ApiResponse.<ArticleClaimResponse>builder()
            .success(true)
            .code(HttpStatus.OK.value())
            .result(result)
            .build());
  }
}
