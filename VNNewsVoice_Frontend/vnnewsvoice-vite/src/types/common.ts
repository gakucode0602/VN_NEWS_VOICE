export interface ApiResponse<T> {
  success: boolean;
  code: number;
  message?: string | null;
  result?: T;
}

export interface Pagination {
  currentPage: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
  startIndex: number;
  endIndex: number;
}

export type ApiParams = Record<string, string | number | boolean | undefined>;

export type ApiError = Error & {
  status?: number;
  data?: unknown;
};
