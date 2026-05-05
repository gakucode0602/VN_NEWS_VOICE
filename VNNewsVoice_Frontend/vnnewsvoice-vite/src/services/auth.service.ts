import { authApiPost } from "./apiClient";
import type { AuthResponse, GoogleLoginResponse, LoginRequest, ReaderProfile } from "../types";

export const login = (payload: LoginRequest) =>
  authApiPost<AuthResponse>("/user/login", payload);

export const googleLogin = (tokenId: string) =>
  authApiPost<GoogleLoginResponse>("/user/google-login", { tokenId });

export const register = (formData: FormData) =>
  authApiPost<ReaderProfile>("/user/register", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

export const refreshAccessToken = () =>
  authApiPost<AuthResponse>("/auth/refresh", {});

export const logout = () => authApiPost<void>("/auth/logout", {});
