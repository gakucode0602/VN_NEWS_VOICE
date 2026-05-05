import type { Pagination } from "./common";

export interface Comment {
  id: number;
  content: string;
  createdAt?: string | null;
  articleId?: string | null;
  articleTitle?: string | null;
  userId?: number | null;
  username?: string | null;
  commentReplyId?: number | null;
  likeCount?: number | null;
  liked?: boolean;
  replies?: Comment[];
}

export interface CommentListResponse {
  comments: Comment[];
  pagination: Pagination;
}

export interface CreateCommentRequest {
  content: string;
  commentReplyId?: number | null;
}

export interface CommentLikeResponse {
  commentId: number;
  isLiked: boolean;
  likeCount: number;
}
