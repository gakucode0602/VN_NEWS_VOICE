import { apiDelete, apiGet, apiPost } from "./apiClient";
import type {
  ApiParams,
  ArticleDetailResponse,
  ArticleLikeCountResponse,
  ArticleLikeStatusResponse,
  ArticleListResponse,
  RelatedArticlesResponse,
} from "../types";

export interface ArticleListParams extends ApiParams {
  page?: number;
  name?: string;
  categoryId?: string;
  generatorId?: string;
  fromDate?: string;
  toDate?: string;
  publishedDates?: number;
}

export const getArticles = (params?: ArticleListParams) =>
  apiGet<ArticleListResponse>("/articles", { params });

export const getArticleDetail = (id: string) =>
  apiGet<ArticleDetailResponse>(`/articles/${id}`);

export const getRelatedArticles = (id: string, limit = 10) =>
  apiGet<RelatedArticlesResponse>(`/articles/${id}/related`, {
    params: { limit },
  });

export const getArticleLikeCount = (id: string) =>
  apiGet<ArticleLikeCountResponse>(`/articles/${id}/article-like`);

export const getArticleLikeStatus = (id: string) =>
  apiGet<ArticleLikeStatusResponse>(`/secure/articles/${id}/is-liked`);

export const likeArticle = (id: string) =>
  apiPost<void>(`/secure/articles/${id}/add-article-like`);

export const unlikeArticle = (id: string) =>
  apiDelete<void>(`/secure/articles/${id}/delete-article-like`);
