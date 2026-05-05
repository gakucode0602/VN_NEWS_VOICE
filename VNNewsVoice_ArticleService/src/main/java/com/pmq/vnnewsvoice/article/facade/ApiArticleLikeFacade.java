package com.pmq.vnnewsvoice.article.facade;

import com.pmq.vnnewsvoice.article.dto.ApiResult;
import com.pmq.vnnewsvoice.article.dto.ArticleLikeCountResponse;
import com.pmq.vnnewsvoice.article.dto.ArticleLikeListResponse;
import com.pmq.vnnewsvoice.article.dto.ArticleLikeStatusResponse;
import com.pmq.vnnewsvoice.article.pojo.CustomUserDetails;
import java.util.Map;
import java.util.UUID;

public interface ApiArticleLikeFacade {
  ApiResult<ArticleLikeStatusResponse> getIsLikedArticle(UUID id, CustomUserDetails principal);

  ApiResult<ArticleLikeCountResponse> getNumberOfArticleLike(UUID id);

  ApiResult<ArticleLikeListResponse> getPersonalArticleLikes(
      CustomUserDetails principal, Map<String, String> params);

  ApiResult<Void> addArticleLike(UUID id, CustomUserDetails principal);

  ApiResult<Void> deleteArticleLike(UUID id, CustomUserDetails principal);
}
