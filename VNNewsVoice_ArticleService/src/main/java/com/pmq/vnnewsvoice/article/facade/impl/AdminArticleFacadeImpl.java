package com.pmq.vnnewsvoice.article.facade.impl;

import com.pmq.vnnewsvoice.article.dto.AdminArticleDetailResponse;
import com.pmq.vnnewsvoice.article.dto.AdminArticleListResponse;
import com.pmq.vnnewsvoice.article.dto.AdminArticleResponse;
import com.pmq.vnnewsvoice.article.dto.ApiResult;
import com.pmq.vnnewsvoice.article.dto.ArticleBlockResponse;
import com.pmq.vnnewsvoice.article.dto.amqp.ArticleEventMessage;
import com.pmq.vnnewsvoice.article.dto.amqp.VideoGenerationMessage;
import com.pmq.vnnewsvoice.article.enums.ArticleStatus;
import com.pmq.vnnewsvoice.article.facade.AdminArticleFacade;
import com.pmq.vnnewsvoice.article.helpers.PaginationHelper;
import com.pmq.vnnewsvoice.article.mapper.AdminArticleMapper;
import com.pmq.vnnewsvoice.article.mapper.ApiArticleBlockMapper;
import com.pmq.vnnewsvoice.article.messaging.ArticleEventsPublisher;
import com.pmq.vnnewsvoice.article.messaging.VideoGenerationPublisher;
import com.pmq.vnnewsvoice.article.pojo.Article;
import com.pmq.vnnewsvoice.article.pojo.ArticleBlock;
import com.pmq.vnnewsvoice.article.pojo.Category;
import com.pmq.vnnewsvoice.article.service.ArticleBlockService;
import com.pmq.vnnewsvoice.article.service.ArticleService;
import com.pmq.vnnewsvoice.article.service.CategoryService;
import com.pmq.vnnewsvoice.article.utils.Pagination;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Locale;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class AdminArticleFacadeImpl implements AdminArticleFacade {

  private static final int DEFAULT_PAGE_SIZE = 10;

  private final ArticleService articleService;
  private final ArticleBlockService articleBlockService;
  private final CategoryService categoryService;
  private final AdminArticleMapper adminArticleMapper;
  private final ApiArticleBlockMapper apiArticleBlockMapper;
  private final PaginationHelper paginationHelper;
  private final ArticleEventsPublisher articleEventsPublisher;
  private final VideoGenerationPublisher videoGenerationPublisher;

  @Override
  public AdminArticleListResponse listArticles(Map<String, String> params) {
    Map<String, String> filters = new HashMap<>(params);

    String statusFilter = filters.get("status");
    if (statusFilter == null || statusFilter.isBlank()) {
      filters.putIfAbsent("isActive", "true");
    } else {
      String normalizedStatus = statusFilter.trim().toUpperCase(Locale.ROOT);
      if ("DELETE".equals(normalizedStatus)) {
        normalizedStatus = "DELETED";
      }
      filters.put("status", normalizedStatus);

      if ("DELETED".equals(normalizedStatus)) {
        // Deleted articles are soft-deleted with isActive=false.
        filters.putIfAbsent("isActive", "false");
      } else {
        filters.putIfAbsent("isActive", "true");
      }
    }

    List<Article> articles = articleService.getArticles(filters);
    long total = articleService.countSearchArticles(filters);
    Pagination pagination = paginationHelper.createPagination(filters, total, DEFAULT_PAGE_SIZE);

    List<AdminArticleResponse> responses =
        articles.stream().map(adminArticleMapper::toResponse).toList();

    return new AdminArticleListResponse(responses, pagination);
  }

  @Override
  public Optional<AdminArticleDetailResponse> getArticleDetail(UUID id) {
    Optional<Article> articleOpt = articleService.getArticleById(id);
    if (articleOpt.isEmpty()) {
      return Optional.empty();
    }
    Article article = articleOpt.get();
    AdminArticleResponse articleResponse = adminArticleMapper.toResponse(article);
    List<ArticleBlock> blocks = articleBlockService.getArticleBlocksByArticleId(article.getId());
    List<ArticleBlockResponse> blockResponses =
        blocks.stream().map(apiArticleBlockMapper::toResponse).toList();

    return Optional.of(new AdminArticleDetailResponse(articleResponse, blockResponses));
  }

  @Override
  public ApiResult<Void> deleteArticle(UUID id) {
    Optional<Article> articleOpt = articleService.getArticleById(id);
    if (articleOpt.isEmpty()) {
      return ApiResult.failure(HttpStatus.NOT_FOUND, "Không tìm thấy bài báo");
    }

    Article article = articleOpt.get();
    ArticleStatus previousStatus = article.getStatus();
    article.setStatus(ArticleStatus.DELETED);
    article.setDeletedAt(new Date());
    article.setIsActive(false);
    article.setUpdatedAt(new Date());
    articleService.updateArticle(article);

    if (isPublished(previousStatus)) {
      publishArticleLifecycleEvent(article, ArticleStatus.DELETED);
    }

    return ApiResult.success(HttpStatus.OK, null, "Đã chuyển bài báo sang trạng thái xóa");
  }

  @Override
  public ApiResult<AdminArticleResponse> saveCategory(UUID id, Long categoryId) {
    Optional<Article> articleOpt = articleService.getArticleById(id);
    if (articleOpt.isEmpty()) {
      return ApiResult.failure(HttpStatus.NOT_FOUND, "Không tìm thấy bài báo");
    }
    Optional<Category> categoryOpt = categoryService.getCategoryById(categoryId);
    if (categoryOpt.isEmpty()) {
      return ApiResult.failure(HttpStatus.NOT_FOUND, "Không tìm thấy danh mục");
    }
    Article article = articleOpt.get();
    Category targetCategory = categoryOpt.get();

    if (!canAssignCategory(article, targetCategory)) {
      return ApiResult.failure(
          HttpStatus.BAD_REQUEST,
          "Danh mục đã bị vô hiệu hóa. Vui lòng chọn danh mục đang hoạt động");
    }

    article.setCategoryId(targetCategory);
    article.setUpdatedAt(new Date());
    articleService.updateArticle(article);
    return ApiResult.success(
        HttpStatus.OK, adminArticleMapper.toResponse(article), "Lưu danh mục thành công");
  }

  @Override
  public ApiResult<AdminArticleResponse> changeStatus(UUID id, String status) {
    Optional<Article> articleOpt = articleService.getArticleById(id);
    if (articleOpt.isEmpty()) {
      return ApiResult.failure(HttpStatus.NOT_FOUND, "Không tìm thấy bài báo");
    }

    ArticleStatus newStatus;
    try {
      newStatus = ArticleStatus.valueOf(status);
    } catch (IllegalArgumentException e) {
      return ApiResult.failure(HttpStatus.BAD_REQUEST, "Trạng thái không hợp lệ: " + status);
    }

    Article article = articleOpt.get();
    ArticleStatus currentStatus = article.getStatus();

    boolean isValidTransition = isValidStatusTransition(currentStatus, newStatus, article);
    if (!isValidTransition) {
      return ApiResult.failure(
          HttpStatus.UNPROCESSABLE_ENTITY,
          "Không thể thay đổi từ trạng thái " + currentStatus + " sang " + newStatus);
    }

    if (newStatus == ArticleStatus.PUBLISHED && !isCategoryActive(article.getCategoryId())) {
      return ApiResult.failure(
          HttpStatus.BAD_REQUEST,
          "Không thể xuất bản bài viết vì danh mục đã bị vô hiệu hóa hoặc không hợp lệ");
    }

    article.setStatus(newStatus);
    if (newStatus == ArticleStatus.PUBLISHED) {
      article.setPublishedDate(new Date());
    }
    if (newStatus == ArticleStatus.DELETED) {
      article.setDeletedAt(new Date());
      article.setIsActive(false);
    } else {
      article.setDeletedAt(null);
      article.setIsActive(true);
    }
    article.setUpdatedAt(new Date());
    articleService.updateArticle(article);

    if (isPublished(currentStatus) && !isPublished(newStatus)) {
      publishArticleLifecycleEvent(article, ArticleStatus.DELETED);
    } else if (!isPublished(currentStatus) && isPublished(newStatus)) {
      publishArticleLifecycleEvent(article, ArticleStatus.PUBLISHED);
    }

    return ApiResult.success(
        HttpStatus.OK,
        adminArticleMapper.toResponse(article),
        "Đã cập nhật trạng thái bài báo thành công");
  }

  @Override
  public ApiResult<AdminArticleResponse> saveVideoUrl(UUID id, String videoUrl) {
    Optional<Article> articleOpt = articleService.getArticleById(id);
    if (articleOpt.isEmpty()) {
      return ApiResult.failure(HttpStatus.NOT_FOUND, "Không tìm thấy bài báo");
    }
    Article article = articleOpt.get();
    article.setVideoUrl(videoUrl);
    article.setUpdatedAt(new Date());
    articleService.updateArticle(article);
    return ApiResult.success(
        HttpStatus.OK, adminArticleMapper.toResponse(article), "Lưu video URL thành công");
  }

  @Override
  public ApiResult<Void> rejectVideo(UUID id) {
    Optional<Article> articleOpt = articleService.getArticleById(id);
    if (articleOpt.isEmpty()) {
      return ApiResult.failure(HttpStatus.NOT_FOUND, "Không tìm thấy bài báo");
    }
    Article article = articleOpt.get();
    article.setIsVideoAccepted(false);
    article.setUpdatedAt(new Date());
    articleService.updateArticle(article);
    return ApiResult.success(HttpStatus.OK, null, "Đã từ chối video");
  }

  @Override
  public ApiResult<Void> acceptVideo(UUID id) {
    Optional<Article> articleOpt = articleService.getArticleById(id);
    if (articleOpt.isEmpty()) {
      return ApiResult.failure(HttpStatus.NOT_FOUND, "Không tìm thấy bài báo");
    }
    Article article = articleOpt.get();
    if (article.getVideoUrl() == null) {
      return ApiResult.failure(HttpStatus.BAD_REQUEST, "Bài báo chưa có video để chấp nhận");
    }
    article.setIsVideoAccepted(true);
    article.setUpdatedAt(new Date());
    articleService.updateArticle(article);
    return ApiResult.success(HttpStatus.OK, null, "Đã chấp nhận video");
  }

  @Override
  public ApiResult<Void> generateVideo(UUID id, String videoStyle, Integer durationSeconds) {
    Optional<Article> articleOpt = articleService.getArticleById(id);
    if (articleOpt.isEmpty()) {
      return ApiResult.failure(HttpStatus.NOT_FOUND, "Không tìm thấy bài báo");
    }
    Article article = articleOpt.get();

    VideoGenerationMessage message =
        VideoGenerationMessage.builder()
            .articleId(article.getId())
            .title(article.getTitle())
            .topImageUrl(article.getTopImageUrl())
            .summary(article.getSummary())
            .videoStyle(videoStyle)
            .durationSeconds(durationSeconds)
            .build();

    videoGenerationPublisher.publishVideoTask(message);
    return ApiResult.success(
        HttpStatus.ACCEPTED,
        null,
        "Yêu cầu tạo video đã được gửi. Video sẽ được lưu sau 1–3 phút.");
  }

  private void publishArticleLifecycleEvent(Article article, ArticleStatus lifecycleStatus) {
    try {
      ArticleEventMessage event = buildArticleUpdatedEvent(article);
      event.setStatus(lifecycleStatus.name());
      event.setIsActive(lifecycleStatus == ArticleStatus.PUBLISHED);
      if (lifecycleStatus == ArticleStatus.PUBLISHED) {
        event.setDeletedAt(null);
      }
      articleEventsPublisher.publishArticleUpdated(event);
    } catch (Exception e) {
      // Keep admin operation successful; reconciliation can retry from DB state if needed.
      org.slf4j.LoggerFactory.getLogger(AdminArticleFacadeImpl.class)
          .error("[AMQP] Failed to publish article.updated for articleId={}", article.getId(), e);
    }
  }

  private ArticleEventMessage buildArticleUpdatedEvent(Article article) {
    List<ArticleBlock> blocks = articleBlockService.getArticleBlocksByArticleId(article.getId());

    List<ArticleEventMessage.BlockMessage> blockMessages =
        blocks.stream().map(this::toBlockMessage).toList();

    ArticleEventMessage event = new ArticleEventMessage();
    event.setArticleId(article.getId());
    event.setSourceId(
        article.getGeneratorId() != null && article.getGeneratorId().getId() != null
            ? String.valueOf(article.getGeneratorId().getId())
            : "");
    event.setSourceName(
        article.getGeneratorId() != null && article.getGeneratorId().getName() != null
            ? article.getGeneratorId().getName()
            : "");
    event.setTitle(article.getTitle());
    event.setTopImage(article.getTopImageUrl());
    event.setUrl(article.getOriginalUrl());
    event.setPublishedAt(
        article.getPublishedDate() != null
            ? article.getPublishedDate().toInstant().toString()
            : null);
    event.setSummary(article.getSummary());
    event.setAudioUrl(article.getAudioUrl());
    event.setBlocks(blockMessages);
    event.setEventType("article.updated");
    event.setStatus(article.getStatus() != null ? article.getStatus().name() : null);
    event.setIsActive(article.getIsActive());
    event.setDeletedAt(
        article.getDeletedAt() != null ? article.getDeletedAt().toInstant().toString() : null);
    return event;
  }

  private ArticleEventMessage.BlockMessage toBlockMessage(ArticleBlock block) {
    ArticleEventMessage.BlockMessage message = new ArticleEventMessage.BlockMessage();
    message.setOrder(block.getOrderIndex());
    message.setType(block.getType());
    message.setContent(block.getContent());
    message.setText(block.getText());
    message.setTag(block.getTag());
    message.setSrc(block.getSrc());
    message.setAlt(block.getAlt());
    message.setCaption(block.getCaption());
    return message;
  }

  private boolean isValidStatusTransition(
      ArticleStatus current, ArticleStatus next, Article article) {
    if (current == null) {
      return false;
    }
    switch (current) {
      case DRAFT:
        return next == ArticleStatus.PENDING || next == ArticleStatus.DELETED;
      case PENDING:
        if (next == ArticleStatus.PUBLISHED
            && (article.getAudioUrl() == null
                || article.getSummary() == null
                || article.getSummary().isEmpty())) {
          return false;
        }
        return next == ArticleStatus.PUBLISHED || next == ArticleStatus.REJECTED;
      case REJECTED:
        return next == ArticleStatus.PENDING || next == ArticleStatus.DELETED;
      case PUBLISHED:
        return next == ArticleStatus.DELETED || next == ArticleStatus.REJECTED;
      case DELETED:
        if (next == ArticleStatus.PUBLISHED
            && (article.getAudioUrl() == null
                || article.getSummary() == null
                || article.getSummary().isEmpty())) {
          return false;
        }
        return next == ArticleStatus.PENDING || next == ArticleStatus.PUBLISHED;
      default:
        return false;
    }
  }

  private boolean canAssignCategory(Article article, Category targetCategory) {
    if (targetCategory == null) {
      return false;
    }

    if (Boolean.TRUE.equals(targetCategory.getIsActive())) {
      return true;
    }

    if (article == null
        || article.getCategoryId() == null
        || article.getCategoryId().getId() == null) {
      return false;
    }

    return article.getCategoryId().getId().equals(targetCategory.getId());
  }

  private boolean isCategoryActive(Category category) {
    return category != null && Boolean.TRUE.equals(category.getIsActive());
  }

  private boolean isPublished(ArticleStatus status) {
    return status == ArticleStatus.PUBLISHED;
  }
}
