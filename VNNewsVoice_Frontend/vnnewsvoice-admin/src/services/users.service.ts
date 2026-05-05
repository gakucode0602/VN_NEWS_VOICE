import apiClient, { AUTH_SERVICE_URL } from '../lib/apiClient';

interface ApiResponse<T> {
  result: T;
}

interface BackendUserDto {
  id: number;
  username: string;
  email: string;
  avatarUrl: string;
  isActive: boolean;
  roleName: string;
  createdAt: string;
}

interface BackendUserListResponse {
  users: BackendUserDto[];
  totalUsers: number;
  currentPage: number;
  totalPages: number;
  startIndex: number;
  endIndex: number;
}

export interface UserDto {
  id: number;
  userIdUsername: string;
  userIdEmail: string;
  avatarUrl: string;
  isActive: boolean;
  role: string;
  createdAt: string;
}

export interface UserListResponse {
  users: UserDto[];
  totalItems: number;
  currentPage: number;
  totalPages: number;
  startIndex: number;
  endIndex: number;
}

export const usersService = {
  getUsers: async (params: { page: number; pageSize: number; username?: string; role?: string; isActive?: boolean }) => {
    const res = await apiClient.get<ApiResponse<BackendUserListResponse>>(`${AUTH_SERVICE_URL}/api/secure/admin/users`, {
      params,
    });

    return {
      users: res.data.result.users.map((user) => ({
        id: user.id,
        userIdUsername: user.username,
        userIdEmail: user.email,
        avatarUrl: user.avatarUrl,
        isActive: user.isActive,
        role: user.roleName,
        createdAt: user.createdAt,
      })),
      totalItems: res.data.result.totalUsers,
      currentPage: res.data.result.currentPage,
      totalPages: res.data.result.totalPages,
      startIndex: res.data.result.startIndex,
      endIndex: res.data.result.endIndex,
    } satisfies UserListResponse;
  },

  toggleStatus: async (id: number) => {
    const res = await apiClient.put(`${AUTH_SERVICE_URL}/api/secure/admin/users/${id}/status`);
    return res.data;
  },

  updateRole: async (id: number, roleName: string) => {
    const res = await apiClient.put(`${AUTH_SERVICE_URL}/api/secure/admin/users/${id}/roles`, {
      roleName,
    });
    return res.data;
  },
};
