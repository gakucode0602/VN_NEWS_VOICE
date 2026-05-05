import type { Pagination } from "./common";

export interface Article {
  id: string;
  title: string;
  author?: string | null;
  publishedDate?: string | null;
  audioUrl?: string | null;
  summary?: string | null;
  isActive?: boolean | null;
  slug?: string | null;
  originalUrl?: string | null;
  categoryIdId?: number | null;
  categoryIdName?: string | null;
  topImageUrl?: string | null;
  videoUrl?: string | null;
  isVideoAccepted?: boolean | null;
  generatorIdId?: number | null;
  generatorIdName?: string | null;
  generatorIdLogoUrl?: string | null;
  generatorIdUrl?: string | null;
  commentCount?: number | null;
}

export interface ArticleBlock {
  id?: number | null;
  orderIndex?: number | null;
  type?: string | null;
  content?: string | null;
  text?: string | null;
  tag?: string | null;
  src?: string | null;
  alt?: string | null;
  caption?: string | null;
}

export interface ArticleListResponse {
  articles: Article[];
  pagination: Pagination;
}

export interface ArticleDetailResponse {
  article: Article;
  blocks: ArticleBlock[];
}

export interface RelatedArticlesResponse {
  relatedArticles: Article[];
}

export interface ArticleLikeCountResponse {
  totalLike: number;
}

export interface ArticleLikeStatusResponse {
  isLiked?: boolean;
  liked?: boolean;
}
