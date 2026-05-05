import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { Search, RefreshCw, ShieldCheck, ShieldOff, UserCheck, UserX } from 'lucide-react';
import { usersService } from '../../services/users.service';
import type { UserDto } from '../../services/users.service';

const ROLES = ['ROLE_READER', 'ROLE_ADMIN'];

const UsersPage = () => {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');

  const { data, isLoading, error } = useQuery({
    queryKey: ['admin-users', page, pageSize, search, roleFilter],
    queryFn: () =>
      usersService.getUsers({
        page,
        pageSize,
        username: search || undefined,
        role: roleFilter || undefined,
      }),
    placeholderData: (prev) => prev,
  });

  const toggleMutation = useMutation({
    mutationFn: (id: number) => usersService.toggleStatus(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-users'] }),
  });



  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Tài khoản hệ thống</h1>
        <span className="text-sm text-gray-500">
          {data?.totalItems ?? 0} tài khoản
        </span>
      </div>

      {/* Filter Bar */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
          <input
            type="text"
            placeholder="Tìm theo tên đăng nhập..."
            className="w-full pl-9 pr-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
          />
        </div>

        <select
          className="border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 bg-white"
          value={roleFilter}
          onChange={(e) => { setRoleFilter(e.target.value); setPage(1); }}
        >
          <option value="">Tất cả quyền</option>
          {ROLES.map((r) => (
            <option key={r} value={r}>{r.replace('ROLE_', '')}</option>
          ))}
        </select>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {isLoading ? (
          <div className="flex justify-center items-center py-20 text-gray-400">
            <RefreshCw className="animate-spin mr-2" size={20} /> Đang tải...
          </div>
        ) : error ? (
          <div className="text-center py-20 text-red-500">Lỗi tải dữ liệu</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="text-left px-6 py-3 font-semibold text-gray-600">#</th>
                <th className="text-left px-6 py-3 font-semibold text-gray-600">Tên đăng nhập</th>
                <th className="text-left px-6 py-3 font-semibold text-gray-600">Email</th>
                <th className="text-left px-6 py-3 font-semibold text-gray-600">Quyền</th>
                <th className="text-left px-6 py-3 font-semibold text-gray-600">Trạng thái</th>
                <th className="text-center px-6 py-3 font-semibold text-gray-600">Hành động</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {(data?.users ?? []).map((user: UserDto, idx) => (
                <tr key={user.id} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 text-gray-400">
                    {(data?.startIndex ?? 0) + idx}
                  </td>
                  <td className="px-6 py-4 font-medium text-gray-900">{user.userIdUsername}</td>
                  <td className="px-6 py-4 text-gray-500">{user.userIdEmail}</td>
                  <td className="px-6 py-4">
                    <span className="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-blue-100 text-blue-700">
                      {user.role.replace('ROLE_', '')}
                    </span>
                  </td>
                  <td className="px-6 py-4">
                    <span className={`inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium ${
                      user.isActive ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                    }`}>
                      {user.isActive ? <UserCheck size={12} /> : <UserX size={12} />}
                      {user.isActive ? 'Hoạt động' : 'Bị khoá'}
                    </span>
                  </td>
                  <td className="px-6 py-4 text-center">
                    <button
                      onClick={() => toggleMutation.mutate(user.id)}
                      disabled={toggleMutation.isPending}
                      className={`inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
                        user.isActive
                          ? 'bg-red-50 text-red-600 hover:bg-red-100'
                          : 'bg-green-50 text-green-600 hover:bg-green-100'
                      }`}
                    >
                      {user.isActive ? <ShieldOff size={14} /> : <ShieldCheck size={14} />}
                      {user.isActive ? 'Khoá' : 'Mở khoá'}
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {data && data.totalPages > 1 && (
        <div className="flex items-center justify-between text-sm text-gray-600">
          <span>
            Hiển thị {data.startIndex}–{data.endIndex} / {data.totalItems}
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Trước
            </button>
            {Array.from({ length: data.totalPages }, (_, i) => i + 1).map((p) => (
              <button
                key={p}
                onClick={() => setPage(p)}
                className={`px-3 py-1.5 border rounded-lg ${
                  page === p
                    ? 'bg-green-600 text-white border-green-600'
                    : 'border-gray-200 hover:bg-gray-50'
                }`}
              >
                {p}
              </button>
            ))}
            <button
              onClick={() => setPage((p) => Math.min(data.totalPages, p + 1))}
              disabled={page === data.totalPages}
              className="px-3 py-1.5 border border-gray-200 rounded-lg hover:bg-gray-50 disabled:opacity-40 disabled:cursor-not-allowed"
            >
              Tiếp
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default UsersPage;
