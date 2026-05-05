export interface UserProvider {
  providerType?: string;
  [key: string]: string | undefined;
}

export interface ReaderProfile {
  id: number;
  userIdId?: number | null;
  userIdUsername?: string | null;
  userIdAvatarUrl?: string | null;
  userIdEmail?: string | null;
  userIdBirthday?: string | null;
  userIdAddress?: string | null;
  userIdPhoneNumber?: string | null;
  userIdGender?: string | null;
  userIdRoleIdId?: number | null;
  userIdRoleIdName?: string | null;
  userIdAvatarPublicId?: string | null;
  userProviders?: UserProvider[];
}

export interface ChangePasswordRequest {
  newPassword: string;
}
