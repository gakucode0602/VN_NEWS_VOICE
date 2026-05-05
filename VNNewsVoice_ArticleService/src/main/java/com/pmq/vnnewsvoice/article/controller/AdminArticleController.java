package com.pmq.vnnewsvoice.article.controller;

import com.pmq.vnnewsvoice.article.dto.AdminArticleDetailResponse;
import com.pmq.vnnewsvoice.article.dto.AdminArticleListResponse;
import com.pmq.vnnewsvoice.article.dto.AdminArticleResponse;
import com.pmq.vnnewsvoice.article.dto.ApiResponse;
import com.pmq.vnnewsvoice.article.dto.ApiResult;
import com.pmq.vnnewsvoice.article.dto.ArticleChangeStatusRequest;
import com.pmq.vnnewsvoice.article.facade.AdminArticleFacade;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PatchMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/secure/admin")
@PreAuthorize("hasRole('ADMIN')")
public class AdminArticleController {

  private final AdminArticleFacade adminArticleFacade;

  /** GET /api/admin/articles?page=1&size=10&title=...&status=...&categoryId=... */
  @GetMapping("/articles")
  public ResponseEntity<ApiResponse<AdminArticleListResponse>> listArticles(
      @RequestParam Map<String, String> params) {
    AdminArticleListResponse result = adminArticleFacade.listArticles(params);
    return ResponseEntity.ok(ApiResponse.ok(result));
  }

  /** GET /api/admin/articles/{id} */
  @GetMapping("/articles/{id}")
  public ResponseEntity<ApiResponse<AdminArticleDetailResponse>> getArticleDetail(
      @PathVariable UUID id) {
    Optional<AdminArticleDetailResponse> result = adminArticleFacade.getArticleDetail(id);
    return result
        .map(detail -> ResponseEntity.ok(ApiResponse.ok(detail)))
        .orElse(ResponseEntity.notFound().build());
  }

  /** DELETE /api/admin/articles/{id} */
  @DeleteMapping("/articles/{id}")
  public ResponseEntity<ApiResponse<Void>> deleteArticle(@PathVariable UUID id) {
    ApiResult<Void> result = adminArticleFacade.deleteArticle(id);
    if (result.isSuccess()) {
      return ResponseEntity.ok(ApiResponse.ok(result.getMessage(), null));
    }
    return ResponseEntity.status(result.getStatus())
        .body(ApiResponse.error(result.getStatus().value(), result.getMessage()));
  }

  /** PUT /api/admin/articles/{id}/save-category */
  @PutMapping("/articles/{id}/save-category")
  public ResponseEntity<ApiResponse<AdminArticleResponse>> saveCategory(
      @PathVariable UUID id, @RequestParam Long categoryId) {
    ApiResult<AdminArticleResponse> result = adminArticleFacade.saveCategory(id, categoryId);
    if (result.isSuccess()) {
      return ResponseEntity.ok(ApiResponse.ok(result.getMessage(), result.getResult()));
    }
    return ResponseEntity.status(result.getStatus())
        .body(ApiResponse.error(result.getStatus().value(), result.getMessage()));
  }

  /** PUT /api/secure/admin/articles/{id}/change-status */
  @PutMapping("/articles/{id}/change-status")
  public ResponseEntity<ApiResponse<AdminArticleResponse>> changeStatus(
      @PathVariable UUID id, @RequestBody ArticleChangeStatusRequest request) {
    ApiResult<AdminArticleResponse> result =
        adminArticleFacade.changeStatus(id, request.getStatus());
    if (result.isSuccess()) {
      return ResponseEntity.ok(ApiResponse.ok(result.getMessage(), result.getResult()));
    }
    return ResponseEntity.status(result.getStatus())
        .body(ApiResponse.error(result.getStatus().value(), result.getMessage()));
  }

  /** PATCH /api/secure/admin/articles/{id}/video-url */
  @PatchMapping("/articles/{id}/video-url")
  public ResponseEntity<ApiResponse<AdminArticleResponse>> saveVideoUrl(
      @PathVariable UUID id, @RequestParam String videoUrl) {
    ApiResult<AdminArticleResponse> result = adminArticleFacade.saveVideoUrl(id, videoUrl);
    if (result.isSuccess()) {
      return ResponseEntity.ok(ApiResponse.ok(result.getMessage(), result.getResult()));
    }
    return ResponseEntity.status(result.getStatus())
        .body(ApiResponse.error(result.getStatus().value(), result.getMessage()));
  }

  /**
   * POST /api/secure/admin/articles/{id}/generate-video
   *
   * <p>Publishes a video generation task to queue {@code ml.video.tasks}. Returns 202 Accepted
   * immediately. MLWorkerService will call Veo API (1–3 min) and publish {@code video.generated}
   * event back; ArticleService listener will save {@code videoUrl} automatically.
   */
  @PostMapping("/articles/{id}/generate-video")
  public ResponseEntity<ApiResponse<Void>> generateVideo(
      @PathVariable UUID id,
      @RequestParam(required = false) String videoStyle,
      @RequestParam(required = false) Integer durationSeconds) {
    ApiResult<Void> result = adminArticleFacade.generateVideo(id, videoStyle, durationSeconds);
    if (result.isSuccess()) {
      return ResponseEntity.accepted().body(ApiResponse.ok(result.getMessage(), null));
    }
    return ResponseEntity.status(result.getStatus())
        .body(ApiResponse.error(result.getStatus().value(), result.getMessage()));
  }

  /**
   * DELETE /api/secure/admin/articles/{id}/video
   *
   * <p>Sets {@code isVideoAccepted = false}. The {@code videoUrl} and Cloudinary asset are retained
   * for potential future cleanup or re-generation.
   */
  @DeleteMapping("/articles/{id}/video")
  public ResponseEntity<ApiResponse<Void>> rejectVideo(@PathVariable UUID id) {
    ApiResult<Void> result = adminArticleFacade.rejectVideo(id);
    if (result.isSuccess()) {
      return ResponseEntity.ok(ApiResponse.ok(result.getMessage(), null));
    }
    return ResponseEntity.status(result.getStatus())
        .body(ApiResponse.error(result.getStatus().value(), result.getMessage()));
  }

  /**
   * POST /api/secure/admin/articles/{id}/video/accept
   *
   * <p>Sets {@code isVideoAccepted = true} so the video is displayed publicly.
   */
  @PostMapping("/articles/{id}/video/accept")
  public ResponseEntity<ApiResponse<Void>> acceptVideo(@PathVariable UUID id) {
    ApiResult<Void> result = adminArticleFacade.acceptVideo(id);
    if (result.isSuccess()) {
      return ResponseEntity.ok(ApiResponse.ok(result.getMessage(), null));
    }
    return ResponseEntity.status(result.getStatus())
        .body(ApiResponse.error(result.getStatus().value(), result.getMessage()));
  }
}
