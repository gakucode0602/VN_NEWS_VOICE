/* eslint-disable react-refresh/only-export-components */
import type { Dispatch, ReactNode, SetStateAction } from "react";
import { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getProfile } from "../../services/profile.service";
import {
  clearAccessToken,
  getAccessToken,
  setAccessToken,
  subscribeAuthFailure,
} from "../../services/apiClient";
import {
  googleLogin,
  login as loginRequest,
  logout as logoutRequest,
  refreshAccessToken,
} from "../../services/auth.service";
import type { ApiError, GoogleLoginUser, LoginRequest, ReaderProfile } from "../../types";

type AuthResult = {
  success: boolean;
  message: string;
};

type AuthContextValue = {
  token: string | null;
  user: ReaderProfile | null | undefined;
  isAuthenticated: boolean;
  isAuthLoading: boolean;
  isLoading: boolean;
  error: string | null;
  login: (credentials: LoginRequest) => Promise<AuthResult>;
  loginWithGoogle: (tokenId: string) => Promise<AuthResult>;
  logout: () => void;
  clearError: () => void;
  setError: Dispatch<SetStateAction<string | null>>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

const decodeBase64Url = (value: string) => {
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized + "=".repeat((4 - (normalized.length % 4)) % 4);
  return atob(padded);
};

const decodeJwtPayload = (token: string): Record<string, unknown> | null => {
  try {
    const parts = token.split(".");
    if (parts.length < 2) {
      return null;
    }
    return JSON.parse(decodeBase64Url(parts[1])) as Record<string, unknown>;
  } catch {
    return null;
  }
};

const getRoleFromAccessToken = (token: string): string | null => {
  const payload = decodeJwtPayload(token);
  const role = payload?.role;
  return typeof role === "string" && role.trim().length > 0
    ? role.trim().toUpperCase()
    : null;
};

const isReaderRole = (role: string | null) => role === "ROLE_READER" || role === "READER";

const validateUserAccessTokenRole = (token: string | null): string | null => {
  if (!token) {
    return "Thiếu access token từ máy chủ";
  }

  const role = getRoleFromAccessToken(token);
  if (!role) {
    return "Không xác định được quyền tài khoản";
  }

  if (!isReaderRole(role)) {
    return "Tài khoản quản trị không được phép đăng nhập ở frontend người dùng";
  }

  return null;
};

const mapGoogleUserToProfile = (user?: GoogleLoginUser | null) => {
  if (!user) return null;

  return {
    id: user.id,
    userIdUsername: user.username,
    userIdEmail: user.email,
    userIdAvatarUrl: user.avatarUrl,
    userProviders: [{ providerType: "GOOGLE" }],
  };
};

type AuthProviderProps = {
  children: ReactNode;
};

const AuthProvider = ({ children }: AuthProviderProps) => {
  const queryClient = useQueryClient();
  const [token, setToken] = useState<string | null>(() => getAccessToken());
  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const clearError = useCallback(() => setError(null), []);

  const profileQuery = useQuery<ReaderProfile, ApiError>({
    queryKey: ["profile"],
    queryFn: getProfile,
    enabled: Boolean(token) && !isBootstrapping && isReaderRole(getRoleFromAccessToken(token)),
  });

  useEffect(() => {
    let active = true;

    const bootstrapAuth = async () => {
      try {
        const result = await refreshAccessToken();
        if (!active) {
          return;
        }

        if (result?.accessToken) {
          const roleError = validateUserAccessTokenRole(result.accessToken);
          if (roleError) {
            clearAccessToken();
            setToken(null);
            setError(roleError);
            return;
          }

          setAccessToken(result.accessToken);
          setToken(result.accessToken);
        }
      } catch {
        clearAccessToken();
        if (active) {
          setToken(null);
        }
      } finally {
        if (active) {
          setIsBootstrapping(false);
        }
      }
    };

    void bootstrapAuth();

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const unsubscribe = subscribeAuthFailure(() => {
      clearAccessToken();
      setToken(null);
      queryClient.removeQueries({ queryKey: ["profile"] });
    });

    return () => {
      unsubscribe();
    };
  }, [queryClient]);

  useEffect(() => {
    if (
      profileQuery.isError
      && (profileQuery.error?.status === 401 || profileQuery.error?.status === 403)
    ) {
      clearAccessToken();
      setToken(null);
      if (profileQuery.error?.status === 403) {
        setError("Tài khoản hiện tại không có quyền truy cập frontend người dùng");
      }
      queryClient.removeQueries({ queryKey: ["profile"] });
    }
  }, [profileQuery.isError, profileQuery.error, queryClient]);

  const login = async (credentials: LoginRequest): Promise<AuthResult> => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await loginRequest(credentials);
      const accessToken = result?.accessToken;

      const roleError = validateUserAccessTokenRole(accessToken);
      if (roleError) {
        clearAccessToken();
        setToken(null);
        throw new Error(roleError);
      }

      setAccessToken(accessToken);
      setToken(accessToken);
      await queryClient.invalidateQueries({ queryKey: ["profile"] });

      return { success: true, message: "Đăng nhập thành công" };
    } catch (err) {
      const message =
        (err as ApiError | undefined)?.message || "Đăng nhập thất bại";
      setError(message);
      return { success: false, message };
    } finally {
      setIsLoading(false);
    }
  };

  const loginWithGoogle = async (tokenId: string): Promise<AuthResult> => {
    setIsLoading(true);
    setError(null);

    try {
      const result = await googleLogin(tokenId);
      const tokenValue = result?.token;

      const roleError = validateUserAccessTokenRole(tokenValue);
      if (roleError) {
        clearAccessToken();
        setToken(null);
        throw new Error(roleError);
      }

      setAccessToken(tokenValue);
      setToken(tokenValue);

      const mappedUser = mapGoogleUserToProfile(result?.user);
      if (mappedUser) {
        queryClient.setQueryData(["profile"], mappedUser);
      } else {
        await queryClient.invalidateQueries({ queryKey: ["profile"] });
      }

      return { success: true, message: "Đăng nhập thành công" };
    } catch (err) {
      const message =
        (err as ApiError | undefined)?.message || "Đăng nhập thất bại";
      setError(message);
      return { success: false, message };
    } finally {
      setIsLoading(false);
    }
  };

  const logout = () => {
    void logoutRequest().catch(() => undefined);
    clearAccessToken();
    setToken(null);
    setError(null);
    queryClient.removeQueries({ queryKey: ["profile"] });
  };

  const isAuthenticated = useMemo(() => {
    if (!token) {
      return false;
    }
    return isReaderRole(getRoleFromAccessToken(token));
  }, [token]);

  const value: AuthContextValue = {
    token,
    user: profileQuery.data,
    isAuthenticated,
    isAuthLoading: isBootstrapping || profileQuery.isLoading,
    isLoading,
    error,
    login,
    loginWithGoogle,
    logout,
    clearError,
    setError,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }

  return context;
};

export { AuthProvider, useAuth };
