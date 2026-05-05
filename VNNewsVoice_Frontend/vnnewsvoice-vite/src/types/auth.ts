export interface LoginRequest {
  username: string;
  password: string;
}

export interface AuthResponse {
  accessToken: string;
}

export interface GoogleLoginUser {
  id: number;
  username: string;
  email: string;
  avatarUrl?: string | null;
}

export interface GoogleLoginResponse {
  token: string;
  user: GoogleLoginUser;
}

export interface RegisterFormValues {
  [key: string]: string;
  email: string;
  username: string;
  password: string;
  confirmPassword: string;
  phoneNumber: string;
}
