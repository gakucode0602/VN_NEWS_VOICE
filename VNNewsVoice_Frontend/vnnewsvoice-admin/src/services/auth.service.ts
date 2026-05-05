import axios from 'axios';
import { AUTH_SERVICE_URL } from '../lib/apiClient';

interface AuthUser {
  id: number;
  username: string;
  role: string;
  avatarUrl: string | null;
}

interface AuthResult {
  accessToken: string;
  user?: AuthUser;
}

interface AuthApiResponse {
  success?: boolean;
  code?: number;
  message?: string;
  result?: AuthResult;
}

interface LoginResponse {
  success: boolean;
  code: number;
  message: string;
  result: AuthResult & { user: AuthUser };
}

const decodeBase64Url = (value: string) => {
  const normalized = value.replace(/-/g, '+').replace(/_/g, '/');
  const padded = normalized + '='.repeat((4 - (normalized.length % 4)) % 4);
  return atob(padded);
};

const decodeJwtPayload = (token: string): Record<string, unknown> | null => {
  try {
    const parts = token.split('.');
    if (parts.length < 2) {
      return null;
    }
    const payloadJson = decodeBase64Url(parts[1]);
    return JSON.parse(payloadJson) as Record<string, unknown>;
  } catch {
    return null;
  }
};

const buildUserFromAccessToken = (accessToken: string): AuthUser => {
  const payload = decodeJwtPayload(accessToken);
  const rawId = payload?.userId;
  const parsedId =
    typeof rawId === 'number' ? rawId : Number.parseInt(String(rawId ?? '0'), 10);

  return {
    id: Number.isFinite(parsedId) ? parsedId : 0,
    username: typeof payload?.sub === 'string' ? payload.sub : '',
    role: typeof payload?.role === 'string' ? payload.role : 'ROLE_READER',
    avatarUrl: null,
  };
};

export const authService = {
  login: async (username: string, password: string): Promise<LoginResponse> => {
    const response = await axios.post<AuthApiResponse>(
      `${AUTH_SERVICE_URL}/api/user/login`,
      { username, password },
      {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );

    const result = response.data.result;
    if (!result?.accessToken) {
      throw new Error('Invalid login response from AuthService');
    }

    return {
      success: response.data.success ?? true,
      code: response.data.code ?? 200,
      message: response.data.message ?? 'Success',
      result: {
        ...result,
        user: result.user ?? buildUserFromAccessToken(result.accessToken),
      },
    };
  },

  logout: async () => {
    await axios.post(
      `${AUTH_SERVICE_URL}/api/auth/logout`,
      {},
      {
        withCredentials: true,
        headers: {
          'Content-Type': 'application/json',
        },
      }
    );
  },
};
