import { apiGet, apiPost } from "./apiClient";
import type {
  ApiParams,
  ArticleLikeListResponse,
  ChangePasswordRequest,
  CommentListResponse,
  ReaderProfile,
} from "../types";

export const getProfile = () => apiGet<ReaderProfile>("/secure/profile");

export const updateProfile = (formData: FormData) =>
  apiPost<void>("/secure/profile", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

export const changePassword = (payload: ChangePasswordRequest) =>
  apiPost<void>("/secure/change-password", payload);

export const getPersonalComments = (params?: ApiParams) =>
  apiGet<CommentListResponse>("/secure/comments", { params });

export const getPersonalArticleLikes = (params?: ApiParams) =>
  apiGet<ArticleLikeListResponse>("/secure/article-likes", { params });
