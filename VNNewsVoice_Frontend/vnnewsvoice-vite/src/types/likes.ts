import type { Pagination } from "./common";

export interface ArticleLike {
  id: number;
  createdAt?: string | null;
  articleIdId?: string | null;
  articleIdTitle?: string | null;
  readerIdId?: number | null;
}

export interface ArticleLikeListResponse {
  articleLikes: ArticleLike[];
  pagination: Pagination;
}
