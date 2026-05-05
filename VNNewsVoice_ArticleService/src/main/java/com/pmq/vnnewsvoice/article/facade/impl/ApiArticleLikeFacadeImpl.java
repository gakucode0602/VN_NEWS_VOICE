package com.pmq.vnnewsvoice.article.facade.impl;

import com.pmq.vnnewsvoice.article.dto.ApiResult;
import com.pmq.vnnewsvoice.article.dto.ArticleLikeCountResponse;
import com.pmq.vnnewsvoice.article.dto.ArticleLikeDto;
import com.pmq.vnnewsvoice.article.dto.ArticleLikeListResponse;
import com.pmq.vnnewsvoice.article.dto.ArticleLikeStatusResponse;
import com.pmq.vnnewsvoice.article.enums.ArticleStatus;
import com.pmq.vnnewsvoice.article.facade.ApiArticleLikeFacade;
import com.pmq.vnnewsvoice.article.helpers.PaginationHelper;
import com.pmq.vnnewsvoice.article.mapper.ArticleLikeMapper;
import com.pmq.vnnewsvoice.article.pojo.Article;
import com.pmq.vnnewsvoice.article.pojo.ArticleLike;
import com.pmq.vnnewsvoice.article.pojo.CustomUserDetails;
import com.pmq.vnnewsvoice.article.service.ArticleLikeService;
import com.pmq.vnnewsvoice.article.service.ArticleService;
import com.pmq.vnnewsvoice.article.utils.Pagination;
import java.util.Date;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
public class ApiArticleLikeFacadeImpl implements ApiArticleLikeFacade {
  private final ArticleLikeService articleLikeService;
  private final ArticleService articleService;
  private final PaginationHelper paginationHelper;
  private final ArticleLikeMapper articleLikeMapper;

  // No UserInfoService: userId comes directly from JWT claims via CustomUserDetails.getUserId()

  @Override
  public ApiResult<ArticleLikeStatusResponse> getIsLikedArticle(
      UUID id, CustomUserDetails principal) {
    Optional<Article> article = articleService.getArticleById(id);
    if (article.isEmpty() || !isPublicArticle(article.get())) {
      return ApiResult.failure(HttpStatus.BAD_REQUEST, "Bài viết không hợp lệ");
    }

    Optional<ArticleLike> articleLike =
        articleLikeService.getArticleLikeByUserIdAndArticleId(
            principal.getUserId(), article.get().getId());

    ArticleLikeStatusResponse response = new ArticleLikeStatusResponse(articleLike.isPresent());
    return ApiResult.success(HttpStatus.OK, response);
  }

  @Override
  public ApiResult<ArticleLikeCountResponse> getNumberOfArticleLike(UUID id) {
    if (id == null) {
      return ApiResult.failure(HttpStatus.BAD_REQUEST, "Dữ liệu không hợp lệ");
    }

    Optional<Article> article = articleService.getArticleById(id);
    if (article.isEmpty() || !isPublicArticle(article.get())) {
      return ApiResult.failure(HttpStatus.BAD_REQUEST, "Bài viết không hợp lệ");
    }

    long totalLike = articleLikeService.countArticleLikesByArticleId(article.get().getId());
    ArticleLikeCountResponse response = new ArticleLikeCountResponse(totalLike);
    return ApiResult.success(HttpStatus.OK, response);
  }

  @Override
  public ApiResult<ArticleLikeListResponse> getPersonalArticleLikes(
      CustomUserDetails principal, Map<String, String> params) {
    try {
      Long userId = principal.getUserId();
      List<ArticleLike> articleLikes = articleLikeService.getArticlesLikeByUserId(userId, params);
      long totalLikes = articleLikeService.countArticleLikeByUserId(userId);
      Pagination pagination = paginationHelper.createPagination(params, totalLikes, 5);

      List<ArticleLikeDto> articleLikeDtos =
          articleLikes.stream().map(articleLikeMapper::toDto).toList();

      ArticleLikeListResponse response = new ArticleLikeListResponse(articleLikeDtos, pagination);
      return ApiResult.success(HttpStatus.OK, response);
    } catch (Exception ex) {
      return ApiResult.failure(HttpStatus.INTERNAL_SERVER_ERROR, "Không thể tải dữ liệu");
    }
  }

  @Override
  public ApiResult<Void> addArticleLike(UUID id, CustomUserDetails principal) {
    Optional<Article> article = articleService.getArticleById(id);
    if (article.isEmpty() || !isPublicArticle(article.get())) {
      return ApiResult.failure(HttpStatus.BAD_REQUEST, "Bài viết không hợp lệ");
    }

    ArticleLike articleLike = new ArticleLike();
    articleLike.setArticleId(article.get());
    // readerId stores UserInfo.id extracted directly from JWT claims
    articleLike.setReaderId(principal.getUserId());
    articleLike.setCreatedAt(new Date());

    if (articleLikeService.addArticleLike(articleLike) != null) {
      return ApiResult.success(HttpStatus.CREATED, null, "Đã thích bài viết");
    }

    return ApiResult.failure(HttpStatus.BAD_REQUEST, "Không thể thích bài viết");
  }

  @Override
  public ApiResult<Void> deleteArticleLike(UUID id, CustomUserDetails principal) {
    Optional<Article> article = articleService.getArticleById(id);
    if (article.isEmpty() || !isPublicArticle(article.get())) {
      return ApiResult.failure(HttpStatus.BAD_REQUEST, "Bài viết không hợp lệ");
    }

    Optional<ArticleLike> articleLike =
        articleLikeService.getArticleLikeByUserIdAndArticleId(
            principal.getUserId(), article.get().getId());
    if (articleLike.isEmpty()) {
      return ApiResult.failure(HttpStatus.NOT_FOUND, "Không tìm thấy dữ liệu yêu thích");
    }

    if (articleLikeService.deleteArticleLikesByUserIdAndArticleId(
        principal.getUserId(), article.get().getId())) {
      return ApiResult.success(HttpStatus.OK, null, "Đã bỏ thích bài viết");
    }

    return ApiResult.failure(HttpStatus.BAD_REQUEST, "Không thể bỏ thích bài viết");
  }

  private boolean isPublicArticle(Article article) {
    return article.getStatus() == ArticleStatus.PUBLISHED
        && Boolean.TRUE.equals(article.getIsActive());
  }
}
