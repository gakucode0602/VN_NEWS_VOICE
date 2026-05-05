import { apiGet, apiPost, apiDelete } from "./apiClient";
import type {
  ApiError,
  ApiParams,
  Comment,
  CommentLikeResponse,
  CommentListResponse,
  CreateCommentRequest,
} from "../types";

export interface CommentListParams extends ApiParams {
  page?: number;
}

export const COMMENTS_ENABLED =
  (import.meta.env.VITE_ENABLE_COMMENTS ?? "true").toLowerCase() !== "false";

const UNAVAILABLE_STATUSES = new Set([404, 502, 503, 504]);

const buildEmptyComments = (page = 1): CommentListResponse => ({
  comments: [],
  pagination: {
    currentPage: page,
    pageSize: 10,
    totalItems: 0,
    totalPages: 1,
    startIndex: 0,
    endIndex: 0,
  },
});

const isCommentsTemporarilyUnavailable = (error: unknown) => {
  const status = (error as ApiError | undefined)?.status;
  return typeof status === "number" && UNAVAILABLE_STATUSES.has(status);
};

export const getComments = async (id: string, params?: CommentListParams) => {
  const page = Number(params?.page) || 1;

  if (!COMMENTS_ENABLED) {
    return buildEmptyComments(page);
  }

  try {
    return await apiGet<CommentListResponse>(`/articles/${id}/comments`, { params });
  } catch (error) {
    if (isCommentsTemporarilyUnavailable(error)) {
      return buildEmptyComments(page);
    }
    throw error;
  }
};

export const createComment = (
  id: string,
  payload: CreateCommentRequest
) => {
  if (!COMMENTS_ENABLED) {
    const disabledError = new Error(
      "Tính năng bình luận đang tạm thời tắt."
    ) as ApiError;
    disabledError.status = 503;
    throw disabledError;
  }

  return apiPost<Comment>(`/secure/articles/${id}/comments`, payload);
};

export const deleteComment = (commentId: number) =>
  apiDelete<void>(`/secure/comments/${commentId}`);

export const toggleCommentLike = (commentId: number) =>
  apiPost<CommentLikeResponse>(`/secure/comments/${commentId}/like`);

export const getCommentById = (commentId: number) =>
  apiGet<Comment>(`/comments/${commentId}`);
