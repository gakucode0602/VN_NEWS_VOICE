import { useMemo, useState, type ComponentType } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  Search,
  RefreshCw,
  Trash2,
  CheckCircle,
  XCircle,
  Clock,
  Eye,
  Newspaper,
  CalendarDays,
  FilterX,
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { articlesService } from '../../services/articles.service';
import type { ArticleDto } from '../../services/articles.service';

const STATUS_OPTIONS = [
  { value: '', label: 'Tất cả trạng thái' },
  { value: 'DRAFT', label: 'Bản nháp' },
  { value: 'PENDING', label: 'Chờ duyệt' },
  { value: 'PUBLISHED', label: 'Đã xuất bản' },
  { value: 'REJECTED', label: 'Từ chối' },
  { value: 'DELETED', label: 'Đã xoá' },
];

const VALID_TRANSITIONS: Record<string, string[]> = {
  DRAFT: ['PENDING'],
  PENDING: ['PUBLISHED', 'REJECTED'],
  REJECTED: ['PENDING'],
  PUBLISHED: ['REJECTED'],
  DELETED: ['PENDING', 'PUBLISHED'],
};

const STATUS_LABELS: Record<string, string> = {
  DRAFT: 'Bản nháp',
  PENDING: 'Chờ duyệt',
  PUBLISHED: 'Đã xuất bản',
  REJECTED: 'Từ chối',
  DELETED: 'Đã xoá',
};

const STATUS_BADGE: Record<string, { label: string; cls: string; icon: ComponentType<{ size?: number }> }> = {
  DRAFT: { label: 'Bản nháp', cls: 'bg-slate-100 text-slate-700', icon: Clock },
  PENDING: { label: 'Chờ duyệt', cls: 'bg-yellow-100 text-yellow-700', icon: Clock },
  PUBLISHED: { label: 'Đã xuất bản', cls: 'bg-green-100 text-green-700', icon: CheckCircle },
  REJECTED: { label: 'Từ chối', cls: 'bg-red-100 text-red-700', icon: XCircle },
  DELETED: { label: 'Đã xoá', cls: 'bg-gray-100 text-gray-500', icon: XCircle },
};

const formatPublishedDate = (value?: string) => {
  if (!value) {
    return 'Chưa có ngày đăng';
  }

  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return value;
  }

  return parsed.toLocaleDateString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
};

const getSummary = (article: ArticleDto) => {
  const value = article.summary?.trim() || '';
  if (!value) {
    return 'Bài viết chưa có tóm tắt.';
  }

  return value.length > 140 ? `${value.slice(0, 140)}...` : value;
};

const ARTICLE_PERIOD_OPTIONS = [
  { value: '', label: 'Khoảng thời gian' },
  { value: '7', label: '1 tuần qua' },
  { value: '30', label: '1 tháng qua' },
  { value: '180', label: '6 tháng qua' },
  { value: '365', label: '1 năm qua' },
];

const ArticlesPage = () => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [searchInput, setSearchInput] = useState('');
  const [statusInput, setStatusInput] = useState('');
  const [categoryInput, setCategoryInput] = useState('');
  const [fromDateInput, setFromDateInput] = useState('');
  const [toDateInput, setToDateInput] = useState('');
  const [periodInput, setPeriodInput] = useState('');
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<number | undefined>(undefined);
  const [fromDate, setFromDate] = useState('');
  const [toDate, setToDate] = useState('');

  const { data: categories = [] } = useQuery({
    queryKey: ['admin-article-categories'],
    queryFn: () => articlesService.getCategories(),
  });

  const { data, isLoading, error } = useQuery({
    queryKey: ['admin-articles', page, search, statusFilter, categoryFilter, fromDate, toDate],
    queryFn: () =>
      articlesService.getArticles({
        page,
        pageSize: 9,
        title: search || undefined,
        status: statusFilter || undefined,
        categoryId: categoryFilter,
        fromDate: fromDate || undefined,
        toDate: toDate || undefined,
      }),
    placeholderData: (prev) => prev,
  });

  const changStatusMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      articlesService.changeStatus(id, status),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-articles'] }),
    onError: (err: unknown) => {
      const msg =
        (err as { response?: { data?: { message?: string } } })?.response?.data?.message ??
        'Đổi trạng thái thất bại';
      alert(msg);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => articlesService.deleteArticle(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['admin-articles'] }),
  });

  const handleApplyFilters = () => {
    setPage(1);
    setSearch(searchInput.trim());
    setStatusFilter(statusInput);
    setCategoryFilter(categoryInput ? Number(categoryInput) : undefined);
    setFromDate(fromDateInput);
    setToDate(toDateInput);
  };

  const handleResetFilters = () => {
    setPage(1);
    setSearchInput('');
    setStatusInput('');
    setCategoryInput('');
    setFromDateInput('');
    setToDateInput('');
    setPeriodInput('');
    setSearch('');
    setStatusFilter('');
    setCategoryFilter(undefined);
    setFromDate('');
    setToDate('');
  };

  const handlePeriodSelect = (days: string) => {
    setPeriodInput(days);
    if (!days) {
      setFromDateInput('');
      setToDateInput('');
      return;
    }
    const today = new Date();
    const from = new Date();
    from.setDate(today.getDate() - Number(days));
    const fmt = (d: Date) => d.toISOString().split('T')[0];
    setFromDateInput(fmt(from));
    setToDateInput(fmt(today));
  };

  const pageButtons = useMemo(() => {
    if (!data || data.totalPages <= 1) {
      return [];
    }

    const start = Math.max(1, page - 2);
    const end = Math.min(data.totalPages, start + 4);
    const adjustedStart = Math.max(1, end - 4);
    const buttons: number[] = [];

    for (let i = adjustedStart; i <= end; i += 1) {
      buttons.push(i);
    }

    return buttons;
  }, [data, page]);

  const articles = data?.articles ?? [];

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-900">Quản lý Bài Báo</h1>
        <span className="text-sm text-gray-500">{data?.totalItems ?? 0} bài báo</span>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-4 space-y-3">
        <div className="flex items-center justify-end">
          <button
            type="button"
            onClick={handleResetFilters}
            className="inline-flex items-center gap-2 rounded-lg border border-gray-200 px-3 py-2 text-sm text-gray-600 hover:bg-gray-50"
          >
            <FilterX size={16} /> Xoá bộ lọc
          </button>
        </div>

        <div className="flex flex-col gap-2 md:flex-row">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
            <input
              type="text"
              placeholder="Tìm theo tiêu đề"
              className="w-full rounded-lg border border-gray-200 py-2 pl-9 pr-3 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleApplyFilters()}
            />
          </div>
          <button
            type="button"
            onClick={handleApplyFilters}
            className="rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700"
          >
            Tìm
          </button>
        </div>

        <div className="flex flex-col gap-2 md:flex-row">
          <select
            className="rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 bg-white"
            value={categoryInput}
            onChange={(e) => setCategoryInput(e.target.value)}
          >
            <option value="">Tất cả danh mục</option>
            {categories.map((category) => (
              <option key={category.id} value={String(category.id)}>
                {category.name}
              </option>
            ))}
          </select>

          <select
            className="rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 bg-white"
            value={statusInput}
            onChange={(e) => setStatusInput(e.target.value)}
          >
            {STATUS_OPTIONS.map((status) => (
              <option key={status.value} value={status.value}>
                {status.label}
              </option>
            ))}
          </select>

          <button
            type="button"
            onClick={handleApplyFilters}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white hover:bg-blue-700"
          >
            Lọc
          </button>
        </div>

        {/* Date range row */}
        <div className="flex flex-col gap-2 md:flex-row md:items-center">
          <label className="text-sm text-gray-500 whitespace-nowrap">Ngày đăng:</label>
          <select
            value={periodInput}
            onChange={(e) => handlePeriodSelect(e.target.value)}
            className="rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 bg-white"
          >
            {ARTICLE_PERIOD_OPTIONS.map((opt) => (
              <option key={opt.value} value={opt.value}>{opt.label}</option>
            ))}
          </select>
          <div className="flex flex-1 gap-2 items-center">
            <input
              type="date"
              value={fromDateInput}
              max={toDateInput || undefined}
              onChange={(e) => { setFromDateInput(e.target.value); setPeriodInput(''); }}
              className="flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
            />
            <span className="text-gray-400 text-sm">—</span>
            <input
              type="date"
              value={toDateInput}
              min={fromDateInput || undefined}
              onChange={(e) => { setToDateInput(e.target.value); setPeriodInput(''); }}
              className="flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
            />
          </div>
          {(fromDate || toDate) && (
            <span className="text-xs text-green-600 font-medium whitespace-nowrap">
              Đang lọc {fromDate || '...'} → {toDate || '...'}
            </span>
          )}
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
        {isLoading && (
          <div className="flex justify-center items-center py-20 text-gray-400">
            <RefreshCw className="animate-spin mr-2" size={20} /> Đang tải...
          </div>
        )}

        {!isLoading && error && (
          <div className="text-center py-20 text-red-500">Lỗi tải dữ liệu</div>
        )}

        {!isLoading && !error && articles.length === 0 && (
          <div className="text-center py-16 text-gray-500">
            <Newspaper size={40} className="mx-auto mb-2 text-gray-300" />
            Không tìm thấy bài viết phù hợp với bộ lọc.
          </div>
        )}

        {!isLoading && !error && articles.length > 0 && (
          <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
            {articles.map((article: ArticleDto) => {
              const badge = STATUS_BADGE[article.status] || STATUS_BADGE.PENDING;
              const BadgeIcon = badge.icon;

              return (
                <article
                  key={article.id}
                  className="overflow-hidden rounded-xl border border-gray-100 bg-white shadow-sm transition-shadow hover:shadow-md"
                >
                  {article.topImageUrl ? (
                    <img
                      src={article.topImageUrl}
                      alt={article.title}
                      className="h-48 w-full object-cover"
                      loading="lazy"
                      referrerPolicy="no-referrer"
                    />
                  ) : (
                    <div className="flex h-48 items-center justify-center bg-gray-100 text-gray-400">
                      <Newspaper size={34} />
                    </div>
                  )}

                  <div className="space-y-3 p-4">
                    <div className="flex flex-wrap gap-2">
                      <span className="inline-flex items-center rounded-full bg-blue-50 px-2 py-1 text-xs font-semibold text-blue-700">
                        {article.categoryName || 'Uncategorized'}
                      </span>
                      <span className={`inline-flex items-center gap-1 rounded-full px-2 py-1 text-xs font-semibold ${badge.cls}`}>
                        <BadgeIcon size={12} />
                        {badge.label}
                      </span>
                    </div>

                    <h3 className="line-clamp-2 text-base font-semibold text-gray-900">{article.title}</h3>
                    <p className="line-clamp-3 text-sm leading-6 text-gray-600">{getSummary(article)}</p>

                    <div className="space-y-1.5 text-xs text-gray-500">
                      <div>Nguồn: {article.generatorName || 'Không rõ nguồn'}</div>
                      <div className="inline-flex items-center gap-1">
                        <CalendarDays size={12} />
                        {formatPublishedDate(article.publishedAt)}
                      </div>
                    </div>

                    <div className="space-y-2 pt-1">
                      <select
                        className="w-full rounded-lg border border-gray-200 px-2 py-1.5 text-xs focus:outline-none focus:ring-1 focus:ring-green-500"
                        value=""
                        onChange={(e) => e.target.value && changStatusMutation.mutate({ id: article.id, status: e.target.value })}
                      >
                        <option value="">Đổi trạng thái...</option>
                        {(VALID_TRANSITIONS[article.status] ?? []).map((val) => (
                          <option key={val} value={val}>
                            {STATUS_LABELS[val]}
                          </option>
                        ))}
                      </select>

                      <div className="flex items-center justify-between border-t border-gray-100 pt-2">
                        <span className="text-xs text-gray-400">ID: {article.id}</span>
                        <div className="flex items-center gap-1">
                          <button
                            onClick={() => navigate(`/articles/${article.id}`)}
                            className="rounded-lg p-1.5 text-blue-500 hover:bg-blue-50"
                            title="Xem chi tiết"
                          >
                            <Eye size={16} />
                          </button>
                          <button
                            onClick={() => {
                              if (confirm('Xoá bài báo này?')) {
                                deleteMutation.mutate(article.id);
                              }
                            }}
                            className="rounded-lg p-1.5 text-red-500 hover:bg-red-50"
                            title="Xoá"
                          >
                            <Trash2 size={16} />
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </div>

      {data && data.totalPages > 1 && (
        <div className="flex flex-wrap items-center justify-between gap-3 text-sm text-gray-600">
          <span>Hiển thị {data.startIndex}-{data.endIndex} / {data.totalItems}</span>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((prev) => Math.max(1, prev - 1))}
              disabled={page === 1}
              className="rounded-lg border border-gray-200 px-3 py-1.5 hover:bg-gray-50 disabled:opacity-40"
            >
              Trước
            </button>

            {pageButtons.map((pg) => (
              <button
                key={pg}
                onClick={() => setPage(pg)}
                className={`rounded-lg border px-3 py-1.5 ${
                  pg === page
                    ? 'border-green-600 bg-green-600 text-white'
                    : 'border-gray-200 hover:bg-gray-50'
                }`}
              >
                {pg}
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

export default ArticlesPage;
