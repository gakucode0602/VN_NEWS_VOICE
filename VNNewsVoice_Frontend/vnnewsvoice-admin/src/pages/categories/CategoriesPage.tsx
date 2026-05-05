import { useMemo, useState, type FormEvent } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  Plus,
  RefreshCw,
  Search,
  ToggleLeft,
  ToggleRight,
  Pencil,
  Save,
  X,
  Trash2,
} from 'lucide-react';
import { articlesService } from '../../services/articles.service';
import type { CategoryDto } from '../../services/articles.service';

type FeedbackState = {
  type: 'success' | 'error';
  text: string;
} | null;

const getErrorMessage = (error: unknown, fallback: string) => {
  if (error && typeof error === 'object') {
    const maybeResponse = error as {
      response?: { data?: { message?: string } };
      message?: string;
    };

    return maybeResponse.response?.data?.message || maybeResponse.message || fallback;
  }

  return fallback;
};

const CategoriesPage = () => {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [searchInput, setSearchInput] = useState('');
  const [search, setSearch] = useState('');
  const [newCategoryName, setNewCategoryName] = useState('');
  const [editingCategoryId, setEditingCategoryId] = useState<number | null>(null);
  const [editingCategoryName, setEditingCategoryName] = useState('');
  const [feedback, setFeedback] = useState<FeedbackState>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ['admin-categories', page, pageSize, search],
    queryFn: () =>
      articlesService.getAdminCategories({
        page,
        pageSize,
        name: search || undefined,
      }),
    placeholderData: (prev) => prev,
  });

  const createMutation = useMutation({
    mutationFn: (payload: { name: string; isActive?: boolean }) =>
      articlesService.createCategory(payload),
    onSuccess: () => {
      setFeedback({ type: 'success', text: 'Tạo danh mục thành công.' });
      setNewCategoryName('');
      queryClient.invalidateQueries({ queryKey: ['admin-categories'] });
    },
    onError: (mutationError) => {
      setFeedback({
        type: 'error',
        text: getErrorMessage(mutationError, 'Không thể tạo danh mục.'),
      });
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, payload }: { id: number; payload: { name: string; isActive?: boolean } }) =>
      articlesService.updateCategory(id, payload),
    onSuccess: () => {
      setFeedback({ type: 'success', text: 'Cập nhật danh mục thành công.' });
      setEditingCategoryId(null);
      setEditingCategoryName('');
      queryClient.invalidateQueries({ queryKey: ['admin-categories'] });
    },
    onError: (mutationError) => {
      setFeedback({
        type: 'error',
        text: getErrorMessage(mutationError, 'Không thể cập nhật danh mục.'),
      });
    },
  });

  const toggleStatusMutation = useMutation({
    mutationFn: (id: number) => articlesService.toggleCategoryStatus(id),
    onSuccess: () => {
      setFeedback({ type: 'success', text: 'Đã cập nhật trạng thái danh mục.' });
      queryClient.invalidateQueries({ queryKey: ['admin-categories'] });
    },
    onError: (mutationError) => {
      setFeedback({
        type: 'error',
        text: getErrorMessage(mutationError, 'Không thể cập nhật trạng thái.'),
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: number) => articlesService.deleteCategory(id),
    onSuccess: () => {
      setFeedback({ type: 'success', text: 'Đã xóa danh mục.' });
      queryClient.invalidateQueries({ queryKey: ['admin-categories'] });
    },
    onError: (mutationError) => {
      setFeedback({
        type: 'error',
        text: getErrorMessage(mutationError, 'Không thể xóa danh mục.'),
      });
    },
  });

  const handleSearch = () => {
    setPage(1);
    setSearch(searchInput.trim());
  };

  const handleResetSearch = () => {
    setPage(1);
    setSearchInput('');
    setSearch('');
  };

  const handleCreateCategory = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const name = newCategoryName.trim();
    if (!name) {
      setFeedback({ type: 'error', text: 'Tên danh mục không được để trống.' });
      return;
    }

    createMutation.mutate({ name, isActive: true });
  };

  const handleStartEdit = (category: CategoryDto) => {
    setEditingCategoryId(category.id);
    setEditingCategoryName(category.name || '');
  };

  const handleCancelEdit = () => {
    setEditingCategoryId(null);
    setEditingCategoryName('');
  };

  const handleSaveEdit = (category: CategoryDto) => {
    const name = editingCategoryName.trim();
    if (!name) {
      setFeedback({ type: 'error', text: 'Tên danh mục không được để trống.' });
      return;
    }

    updateMutation.mutate({
      id: category.id,
      payload: {
        name,
        isActive: category.isActive,
      },
    });
  };

  const pageButtons = useMemo(() => {
    if (!data || data.totalPages <= 1) {
      return [] as number[];
    }

    const start = Math.max(1, page - 2);
    const end = Math.min(data.totalPages, start + 4);
    const adjustedStart = Math.max(1, end - 4);
    const buttons: number[] = [];

    for (let current = adjustedStart; current <= end; current += 1) {
      buttons.push(current);
    }

    return buttons;
  }, [data, page]);

  const categories = data?.categories ?? [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Quản lý danh mục</h1>
        <span className="text-sm text-gray-500">{data?.totalItems ?? 0} danh mục</span>
      </div>

      {feedback && (
        <div
          className={`rounded-lg border px-4 py-3 text-sm ${
            feedback.type === 'success'
              ? 'border-green-200 bg-green-50 text-green-700'
              : 'border-red-200 bg-red-50 text-red-700'
          }`}
        >
          {feedback.text}
        </div>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 space-y-3">
        <form className="flex flex-col gap-2 md:flex-row" onSubmit={handleCreateCategory}>
          <input
            type="text"
            value={newCategoryName}
            onChange={(event) => setNewCategoryName(event.target.value)}
            placeholder="Tên danh mục mới"
            className="flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
          />
          <button
            type="submit"
            disabled={createMutation.isPending}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-60"
          >
            <Plus size={16} /> Thêm danh mục
          </button>
        </form>

        <div className="flex flex-col gap-2 md:flex-row">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
            <input
              type="text"
              value={searchInput}
              onChange={(event) => setSearchInput(event.target.value)}
              placeholder="Tìm theo tên danh mục"
              className="w-full rounded-lg border border-gray-200 py-2 pl-9 pr-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>
          <button
            type="button"
            onClick={handleSearch}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
          >
            Search
          </button>
          <button
            type="button"
            onClick={handleResetSearch}
            className="rounded-lg border border-gray-200 px-4 py-2 text-sm text-gray-600 hover:bg-gray-50"
          >
            Reset
          </button>
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {isLoading ? (
          <div className="flex justify-center items-center py-20 text-gray-400">
            <RefreshCw className="animate-spin mr-2" size={20} /> Đang tải...
          </div>
        ) : error ? (
          <div className="text-center py-20 text-red-500">Không thể tải danh mục.</div>
        ) : categories.length === 0 ? (
          <div className="text-center py-20 text-gray-500">Không có danh mục nào.</div>
        ) : (
          <table className="w-full text-sm">
            <thead className="bg-gray-50 border-b border-gray-100">
              <tr>
                <th className="text-left px-5 py-3 font-semibold text-gray-600">ID</th>
                <th className="text-left px-5 py-3 font-semibold text-gray-600">Tên danh mục</th>
                <th className="text-left px-5 py-3 font-semibold text-gray-600">Description</th>
                <th className="text-left px-5 py-3 font-semibold text-gray-600">Trạng thái</th>
                <th className="text-center px-5 py-3 font-semibold text-gray-600">Hành động</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-50">
              {categories.map((category) => {
                const isEditing = editingCategoryId === category.id;

                return (
                  <tr key={category.id} className="hover:bg-gray-50">
                    <td className="px-5 py-4 text-gray-500">{category.id}</td>
                    <td className="px-5 py-4">
                      {isEditing ? (
                        <input
                          type="text"
                          value={editingCategoryName}
                          onChange={(event) => setEditingCategoryName(event.target.value)}
                          className="w-full rounded-lg border border-gray-200 px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                      ) : (
                        <span className="font-medium text-gray-900">{category.name}</span>
                      )}
                    </td>
                    <td className="px-5 py-4 text-gray-500">{category.description || '-'}</td>
                    <td className="px-5 py-4">
                      <span
                        className={`inline-flex rounded-full px-2 py-1 text-xs font-semibold ${
                          category.isActive
                            ? 'bg-green-100 text-green-700'
                            : 'bg-red-100 text-red-700'
                        }`}
                      >
                        {category.isActive ? 'Đang hoạt động' : 'Đã vô hiệu hóa'}
                      </span>
                    </td>
                    <td className="px-5 py-4">
                      <div className="flex items-center justify-center gap-1">
                        <button
                          type="button"
                          onClick={() => toggleStatusMutation.mutate(category.id)}
                          disabled={toggleStatusMutation.isPending}
                          className={`inline-flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium ${
                            category.isActive
                              ? 'text-orange-600 hover:bg-orange-50'
                              : 'text-green-600 hover:bg-green-50'
                          }`}
                        >
                          {category.isActive ? <ToggleLeft size={14} /> : <ToggleRight size={14} />}
                          {category.isActive ? 'Vô hiệu hóa' : 'Kích hoạt'}
                        </button>

                        {isEditing ? (
                          <>
                            <button
                              type="button"
                              onClick={() => handleSaveEdit(category)}
                              disabled={updateMutation.isPending}
                              className="inline-flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium text-blue-600 hover:bg-blue-50"
                            >
                              <Save size={14} /> Lưu
                            </button>
                            <button
                              type="button"
                              onClick={handleCancelEdit}
                              className="inline-flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium text-gray-600 hover:bg-gray-100"
                            >
                              <X size={14} /> Hủy
                            </button>
                          </>
                        ) : (
                          <button
                            type="button"
                            onClick={() => handleStartEdit(category)}
                            className="inline-flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium text-blue-600 hover:bg-blue-50"
                          >
                            <Pencil size={14} /> Sửa
                          </button>
                        )}

                        <button
                          type="button"
                          onClick={() => {
                            const confirmed = confirm(
                              `Bạn có chắc muốn xóa danh mục "${category.name}"?`
                            );
                            if (confirmed) {
                              deleteMutation.mutate(category.id);
                            }
                          }}
                          disabled={deleteMutation.isPending}
                          className="inline-flex items-center gap-1 rounded-lg px-2.5 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50"
                        >
                          <Trash2 size={14} /> Xóa
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        )}
      </div>

      {data && data.totalPages > 1 && (
        <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-gray-600">
          <span>
            Hiển thị {data.startIndex}-{data.endIndex} / {data.totalItems}
          </span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((prev) => Math.max(1, prev - 1))}
              disabled={page === 1}
              className="rounded-lg border border-gray-200 px-3 py-1.5 hover:bg-gray-50 disabled:opacity-40"
            >
              Trước
            </button>

            {pageButtons.map((buttonPage) => (
              <button
                key={buttonPage}
                onClick={() => setPage(buttonPage)}
                className={`rounded-lg border px-3 py-1.5 ${
                  buttonPage === page
                    ? 'border-green-600 bg-green-600 text-white'
                    : 'border-gray-200 hover:bg-gray-50'
                }`}
              >
                {buttonPage}
              </button>
            ))}

            <button
              onClick={() => setPage((prev) => Math.min(data.totalPages, prev + 1))}
              disabled={page === data.totalPages}
              className="rounded-lg border border-gray-200 px-3 py-1.5 hover:bg-gray-50 disabled:opacity-40"
            >
              Tiếp
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default CategoriesPage;
