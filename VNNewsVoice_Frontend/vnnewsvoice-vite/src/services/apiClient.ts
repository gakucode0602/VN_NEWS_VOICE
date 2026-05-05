import axios, {
  AxiosError,
  AxiosHeaders,
  AxiosRequestConfig,
  InternalAxiosRequestConfig,
} from "axios";
import type { ApiError, ApiResponse, AuthResponse } from "../types";

const API_GATEWAY_BASE_URL =
  import.meta.env.VITE_API_GATEWAY_BASE_URL || "http://localhost:8088";

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || `${API_GATEWAY_BASE_URL}/api`;

const AUTH_API_BASE_URL =
  import.meta.env.VITE_AUTH_API_BASE_URL || `${API_GATEWAY_BASE_URL}/api`;

const RAG_API_BASE_URL =
  import.meta.env.VITE_RAG_API_BASE_URL || `${API_GATEWAY_BASE_URL}/chat`;

const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

const authApiClient = axios.create({
  baseURL: AUTH_API_BASE_URL,
  withCredentials: true,
});

const ragApiClient = axios.create({
  baseURL: RAG_API_BASE_URL,
});

let accessToken: string | null = null;
let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (error: unknown) => void;
}> = [];

const authFailureListeners = new Set<() => void>();

const setAuthHeader = (config: AxiosRequestConfig, token: string) => {
  const headers =
    config.headers instanceof AxiosHeaders
      ? config.headers
      : new AxiosHeaders(config.headers);
  headers.set("Authorization", `Bearer ${token}`);
  config.headers = headers;
};

const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((promise) => {
    if (error) {
      promise.reject(error);
    } else if (token) {
      promise.resolve(token);
    }
  });
  failedQueue = [];
};

const notifyAuthFailure = () => {
  authFailureListeners.forEach((listener) => listener());
};

const shouldRefresh = (
  error: AxiosError<ApiResponse<unknown>>,
  originalRequest?: InternalAxiosRequestConfig & { _retry?: boolean }
) => {
  if (!originalRequest) {
    return false;
  }

  const status = error.response?.status;
  const requestUrl = originalRequest.url || "";
  const isAuthRoute =
    requestUrl.includes("/auth/refresh") ||
    requestUrl.includes("/user/login") ||
    requestUrl.includes("/user/google-login");

  return status === 401 && !originalRequest._retry && !isAuthRoute;
};

const refreshAccessTokenInternal = async () => {
  const response = await authApiClient.post<ApiResponse<AuthResponse>>(
    "/auth/refresh",
    {}
  );
  const payload = unwrapResponse(response.data);
  if (!payload?.accessToken) {
    throw buildApiError("Thiếu access token khi refresh", 401, response.data);
  }
  return payload.accessToken;
};

const handleRefreshAndRetry = async (
  error: AxiosError<ApiResponse<unknown>>,
  originalRequest: InternalAxiosRequestConfig & { _retry?: boolean },
  client: typeof apiClient
) => {
  if (isRefreshing) {
    return new Promise((resolve, reject) => {
      failedQueue.push({
        resolve: (token: string) => {
          setAuthHeader(originalRequest, token);
          resolve(client.request(originalRequest));
        },
        reject,
      });
    });
  }

  originalRequest._retry = true;
  isRefreshing = true;

  try {
    const newToken = await refreshAccessTokenInternal();
    setAccessToken(newToken);
    processQueue(null, newToken);
    setAuthHeader(originalRequest, newToken);
    return client.request(originalRequest);
  } catch (refreshError) {
    clearAccessToken();
    processQueue(refreshError, null);
    notifyAuthFailure();
    return Promise.reject(refreshError);
  } finally {
    isRefreshing = false;
  }
};

export const setAccessToken = (token: string | null) => {
  accessToken = token;
};

export const getAccessToken = () => accessToken;

export const clearAccessToken = () => {
  accessToken = null;
};

export const subscribeAuthFailure = (listener: () => void): (() => void) => {
  authFailureListeners.add(listener);
  return () => {
    authFailureListeners.delete(listener);
  };
};

// Attach JWT access token in memory to resource requests.
apiClient.interceptors.request.use((config) => {
  if (accessToken) {
    setAuthHeader(config, accessToken);
  }
  return config;
});

// Reuse same auth interceptor for RAG Service
ragApiClient.interceptors.request.use((config) => {
  if (accessToken) {
    setAuthHeader(config, accessToken);
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiResponse<unknown>>) => {
    const originalRequest = error.config as
      | (InternalAxiosRequestConfig & { _retry?: boolean })
      | undefined;

    if (!shouldRefresh(error, originalRequest)) {
      return Promise.reject(error);
    }

    return handleRefreshAndRetry(error, originalRequest!, apiClient);
  }
);

ragApiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiResponse<unknown>>) => {
    const originalRequest = error.config as
      | (InternalAxiosRequestConfig & { _retry?: boolean })
      | undefined;

    if (!shouldRefresh(error, originalRequest)) {
      return Promise.reject(error);
    }

    return handleRefreshAndRetry(error, originalRequest!, ragApiClient);
  }
);

const buildApiError = (message: string, status?: number, data?: unknown) => {
  const error = new Error(message) as ApiError;
  error.status = status;
  error.data = data;
  return error;
};

const unwrapResponse = <T,>(payload: ApiResponse<T> | T): T => {
  if (payload && typeof payload === "object" && "success" in payload) {
    const wrapped = payload as ApiResponse<T>;
    if (!wrapped.success) {
      throw buildApiError(wrapped.message || "Request failed", wrapped.code, wrapped);
    }
    return wrapped.result as T;
  }
  return payload as T;
};

const request = async <T,>(config: AxiosRequestConfig): Promise<T> => {
  try {
    const response = await apiClient.request<ApiResponse<T>>(config);
    return unwrapResponse(response.data);
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const payload = error.response?.data as ApiResponse<unknown> | undefined;
      const message = payload?.message || error.message || "Request failed";
      throw buildApiError(message, error.response?.status, payload);
    }
    if (error instanceof Error) {
      throw buildApiError(error.message);
    }
    throw buildApiError("Request failed");
  }
};

const apiGet = <T,>(url: string, config?: AxiosRequestConfig) =>
  request<T>({ url, method: "GET", ...config });

const apiPost = <T,>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig
) => request<T>({ url, method: "POST", data, ...config });

const apiPut = <T,>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
  request<T>({ url, method: "PUT", data, ...config });

const apiDelete = <T,>(url: string, config?: AxiosRequestConfig) =>
  request<T>({ url, method: "DELETE", ...config });

const authRequest = async <T,>(config: AxiosRequestConfig): Promise<T> => {
  try {
    const response = await authApiClient.request<ApiResponse<T>>(config);
    return unwrapResponse(response.data);
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const payload = error.response?.data as ApiResponse<unknown> | undefined;
      const message = payload?.message || error.message || "Request failed";
      throw buildApiError(message, error.response?.status, payload);
    }
    if (error instanceof Error) {
      throw buildApiError(error.message);
    }
    throw buildApiError("Request failed");
  }
};

const authApiGet = <T,>(url: string, config?: AxiosRequestConfig) =>
  authRequest<T>({ url, method: "GET", ...config });

const authApiPost = <T,>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig
) => authRequest<T>({ url, method: "POST", data, ...config });

const authApiPut = <T,>(
  url: string,
  data?: unknown,
  config?: AxiosRequestConfig
) => authRequest<T>({ url, method: "PUT", data, ...config });

const authApiDelete = <T,>(url: string, config?: AxiosRequestConfig) =>
  authRequest<T>({ url, method: "DELETE", ...config });

const ragRequest = async <T,>(config: AxiosRequestConfig): Promise<T> => {
  try {
    const response = await ragApiClient.request<ApiResponse<T>>(config);
    return unwrapResponse(response.data);
  } catch (error) {
    if (axios.isAxiosError(error)) {
      const payload = error.response?.data as ApiResponse<unknown> | undefined;
      const message = payload?.message || error.message || "Request failed";
      throw buildApiError(message, error.response?.status, payload);
    }
    if (error instanceof Error) throw buildApiError(error.message);
    throw buildApiError("Request failed");
  }
};

const ragApiGet = <T,>(url: string, config?: AxiosRequestConfig) =>
  ragRequest<T>({ url, method: "GET", ...config });

const ragApiPost = <T,>(url: string, data?: unknown, config?: AxiosRequestConfig) =>
  ragRequest<T>({ url, method: "POST", data, ...config });

export {
  apiClient,
  authApiClient,
  ragApiClient,
  API_BASE_URL,
  AUTH_API_BASE_URL,
  RAG_API_BASE_URL,
  apiGet,
  apiPost,
  apiPut,
  apiDelete,
  authApiGet,
  authApiPost,
  authApiPut,
  authApiDelete,
  ragApiGet,
  ragApiPost,
};
