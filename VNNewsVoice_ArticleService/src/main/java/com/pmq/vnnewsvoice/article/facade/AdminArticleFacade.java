package com.pmq.vnnewsvoice.article.facade;

import com.pmq.vnnewsvoice.article.dto.AdminArticleDetailResponse;
import com.pmq.vnnewsvoice.article.dto.AdminArticleListResponse;
import com.pmq.vnnewsvoice.article.dto.AdminArticleResponse;
import com.pmq.vnnewsvoice.article.dto.ApiResult;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;

public interface AdminArticleFacade {

  AdminArticleListResponse listArticles(Map<String, String> params);

  Optional<AdminArticleDetailResponse> getArticleDetail(UUID id);

  ApiResult<Void> deleteArticle(UUID id);

  ApiResult<AdminArticleResponse> saveCategory(UUID id, Long categoryId);

  ApiResult<AdminArticleResponse> changeStatus(UUID id, String status);

  ApiResult<AdminArticleResponse> saveVideoUrl(UUID id, String videoUrl);

  ApiResult<Void> generateVideo(UUID id, String videoStyle, Integer durationSeconds);

  /** Marks video as rejected — keeps videoUrl in DB, sets isVideoAccepted = false. */
  ApiResult<Void> rejectVideo(UUID id);

  /** Marks video as accepted — sets isVideoAccepted = true so it is displayed publicly. */
  ApiResult<Void> acceptVideo(UUID id);
}
