import axios, { type InternalAxiosRequestConfig } from 'axios';
import { useAuthStore } from '../store/authStore';

const removeTrailingSlash = (value: string) => value.replace(/\/+$/, '');

const resolveServiceUrl = (
  explicitUrl: string | undefined,
  host: string,
  port: string
) => {
  if (explicitUrl && explicitUrl.trim().length > 0) {
    return removeTrailingSlash(explicitUrl.trim());
  }

  const normalizedHost = removeTrailingSlash(host.trim());
  // Empty host → return '' so all requests are origin-relative.
  // This pairs with Vercel rewrites that proxy /api/* to the backend.
  if (!normalizedHost) return '';
  const normalizedPort = port.trim();
  return normalizedPort ? `${normalizedHost}:${normalizedPort}` : normalizedHost;
};

// URL của các microservices, tách theo service + port để đổi port không cần sửa code.
// In production (Vercel), VITE_API_HOST is set to '' so service URLs become ''
// (origin-relative) and Vercel edge rewrites /api/* to the DO backend.
const API_HOST = import.meta.env.VITE_API_HOST ?? 'http://localhost';
const AUTH_SERVICE_PORT = import.meta.env.VITE_AUTH_SERVICE_PORT || '8088';
const ARTICLE_SERVICE_PORT = import.meta.env.VITE_ARTICLE_SERVICE_PORT || '8088';

export const AUTH_SERVICE_URL = resolveServiceUrl(
  import.meta.env.VITE_AUTH_API_URL,
  API_HOST,
  AUTH_SERVICE_PORT
);

export const ARTICLE_SERVICE_URL = resolveServiceUrl(
  import.meta.env.VITE_ARTICLE_API_URL,
  API_HOST,
  ARTICLE_SERVICE_PORT
);

const apiClient = axios.create({
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

let isRefreshing = false;
let failedQueue: Array<{
  resolve: (token: string) => void;
  reject: (err: unknown) => void;
}> = [];

interface RefreshResult {
  accessToken: string;
}

interface RefreshApiResponse {
  result?: RefreshResult;
  accessToken?: string;
}

const shouldAttemptRefresh = (
  error: unknown,
  originalRequest: (InternalAxiosRequestConfig & { _retry?: boolean })
) => {
  const status =
    error && typeof error === 'object'
      ? (error as { response?: { status?: number } }).response?.status
      : undefined;
  const requestUrl = String(originalRequest.url ?? '');
  const isAuthRoute =
    requestUrl.includes('/api/auth/refresh') ||
    requestUrl.includes('/api/user/login') ||
    requestUrl.includes('/api/user/register') ||
    requestUrl.includes('/api/user/google-login');
  const isSecureRoute = requestUrl.includes('/api/secure/');

  if (originalRequest._retry || isAuthRoute) {
    return false;
  }

  if (status === 401) {
    return true;
  }

  // Some services may return 403 for expired/invalid token in stateless mode.
  return status === 403 && isSecureRoute;
};

// Xử lý hàng đợi request bị kẹt lúc đang refresh token
const processQueue = (error: unknown, token: string | null = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else if (token) {
      prom.resolve(token);
    }
  });
  failedQueue = [];
};

// 1. Gắn AccessToken vào mỗi Request API
apiClient.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().accessToken;
    if (token) {
      config.headers = config.headers ?? {};
      (config.headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 2. Chặn lỗi 401 Từ server trả về (Stateless verification)
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config as
      | (InternalAxiosRequestConfig & { _retry?: boolean })
      | undefined;

    if (!originalRequest) {
      return Promise.reject(error);
    }

    if (shouldAttemptRefresh(error, originalRequest)) {
      if (isRefreshing) {
        // Nếu có 1 request đang refresh, xếp hàng các request đến sau
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers = originalRequest.headers ?? {};
            (originalRequest.headers as Record<string, string>)['Authorization'] =
              `Bearer ${token}`;
            return apiClient.request(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;
      const { logout, updateAccessToken } = useAuthStore.getState();

      try {
        // Refresh endpoint dùng HttpOnly cookie nên phải gửi credentials.
        const res = await axios.post<RefreshApiResponse>(
          `${AUTH_SERVICE_URL}/api/auth/refresh`,
          {},
          {
            withCredentials: true,
          }
        );

        const newAccessToken = res.data.result?.accessToken ?? res.data.accessToken;

        if (!newAccessToken) {
          throw new Error('Invalid refresh token response from AuthService');
        }

        // Cập nhật access token lên Zustand. Refresh token chỉ nằm trong HttpOnly cookie.
        updateAccessToken(newAccessToken);
        originalRequest.headers = originalRequest.headers ?? {};
        (originalRequest.headers as Record<string, string>)['Authorization'] =
          `Bearer ${newAccessToken}`;

        processQueue(null, newAccessToken);
        isRefreshing = false;

        // Re-call API đã thất bại với Token mới lấy
        return apiClient.request(originalRequest);
      } catch (refreshError) {
        processQueue(refreshError, null);
        isRefreshing = false;
        // Quá hạn cả Refresh Token -> Ép Logout
        logout();
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

export default apiClient;
