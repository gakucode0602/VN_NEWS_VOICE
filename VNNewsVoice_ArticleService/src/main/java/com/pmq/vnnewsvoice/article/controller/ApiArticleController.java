package com.pmq.vnnewsvoice.article.controller;

import com.pmq.vnnewsvoice.article.dto.ApiResponse;
import com.pmq.vnnewsvoice.article.dto.ArticleDetailResponse;
import com.pmq.vnnewsvoice.article.dto.ArticleListRequest;
import com.pmq.vnnewsvoice.article.dto.ArticleListResponse;
import com.pmq.vnnewsvoice.article.dto.RelatedArticlesResponse;
import com.pmq.vnnewsvoice.article.facade.ApiArticleFacade;
import java.time.Instant;
import java.time.LocalDate;
import java.time.ZoneOffset;
import java.util.List;
import java.util.Optional;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.ModelAttribute;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api")
public class ApiArticleController {
  private final ApiArticleFacade apiArticleFacade;

  @GetMapping("/articles")
  public ResponseEntity<ApiResponse<ArticleListResponse>> getArticleList(
      @ModelAttribute ArticleListRequest request) {
    ArticleListResponse result = apiArticleFacade.listArticles(request);
    return ResponseEntity.ok(
        ApiResponse.<ArticleListResponse>builder()
            .success(true)
            .code(HttpStatus.OK.value())
            .result(result)
            .build());
  }

  @GetMapping("/articles/{id}")
  public ResponseEntity<ApiResponse<ArticleDetailResponse>> getArticleDetail(
      @PathVariable UUID id) {
    Optional<ArticleDetailResponse> response = apiArticleFacade.getArticleDetail(id);
    return response
        .map(
            detail ->
                ResponseEntity.ok(
                    ApiResponse.<ArticleDetailResponse>builder()
                        .success(true)
                        .code(HttpStatus.OK.value())
                        .result(detail)
                        .build()))
        .orElseGet(
            () ->
                ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(
                        ApiResponse.<ArticleDetailResponse>builder()
                            .success(false)
                            .code(HttpStatus.NOT_FOUND.value())
                            .message("Không tìm thấy bài viết")
                            .build()));
  }

  @GetMapping("/articles/{id}/related")
  public ResponseEntity<ApiResponse<RelatedArticlesResponse>> getRelatedArticles(
      @PathVariable UUID id, @RequestParam(value = "limit", defaultValue = "10") int limit) {
    Optional<RelatedArticlesResponse> response = apiArticleFacade.getRelatedArticles(id, limit);
    return response
        .map(
            related ->
                ResponseEntity.ok(
                    ApiResponse.<RelatedArticlesResponse>builder()
                        .success(true)
                        .code(HttpStatus.OK.value())
                        .result(related)
                        .build()))
        .orElseGet(
            () ->
                ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(
                        ApiResponse.<RelatedArticlesResponse>builder()
                            .success(false)
                            .code(HttpStatus.NOT_FOUND.value())
                            .message("Không tìm thấy bài viết")
                            .build()));
  }

  /**
   * Export bài PUBLISHED theo page để RAG Service reindex vào Qdrant.
   *
   * <p>RAG gọi lặp cho đến khi result rỗng.
   *
   * <p>Hỗ trợ 2 format cho since: {@code yyyy-MM-dd} hoặc {@code yyyy-MM-ddTHH:mm:ssZ}
   */
  @GetMapping("/articles/export")
  public ResponseEntity<ApiResponse<List<ArticleDetailResponse>>> exportArticles(
      @RequestParam(required = false) String since,
      @RequestParam(defaultValue = "1") int page,
      @RequestParam(defaultValue = "200") int size) {
    Instant sinceInstant = parseSince(since);
    List<ArticleDetailResponse> articles =
        apiArticleFacade.exportArticles(sinceInstant, page, size);
    return ResponseEntity.ok(
        ApiResponse.<List<ArticleDetailResponse>>builder()
            .success(true)
            .code(HttpStatus.OK.value())
            .message(
                "Exported " + articles.size() + " articles (page=" + page + ", size=" + size + ")")
            .result(articles)
            .build());
  }

  private Instant parseSince(String since) {
    if (since == null || since.isBlank()) return null;
    try {
      if (since.length() == 10) {
        return LocalDate.parse(since).atStartOfDay(ZoneOffset.UTC).toInstant();
      }
      return Instant.parse(since);
    } catch (Exception e) {
      throw new IllegalArgumentException(
          "Invalid 'since' format. Use 'yyyy-MM-dd' or ISO-8601 (e.g. '2026-01-26T00:00:00Z')");
    }
  }
}
