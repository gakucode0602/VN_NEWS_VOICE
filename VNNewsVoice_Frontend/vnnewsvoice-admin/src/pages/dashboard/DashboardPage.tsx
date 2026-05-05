import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  FileText,
  Heart,
  FolderTree,
  Rss,
  TrendingUp,
  RefreshCw,
  AlertCircle,
} from 'lucide-react';
import { articlesService } from '../../services/articles.service';
import type {
  StatusStatisticsDto,
  CategoryStatisticsDto,
  GeneratorStatisticsDto,
} from '../../services/articles.service';

// ---------- helpers ----------

const STATUS_LABELS: Record<string, string> = {
  PUBLISHED: 'Đã đăng',
  DRAFT: 'Nháp',
  PENDING: 'Chờ duyệt',
  REJECTED: 'Từ chối',
  DELETED: 'Đã xoá',
};

const STATUS_COLORS: Record<string, string> = {
  PUBLISHED: 'bg-green-500',
  DRAFT: 'bg-gray-400',
  PENDING: 'bg-yellow-400',
  REJECTED: 'bg-red-400',
  DELETED: 'bg-rose-700',
};

const formatNumber = (n: number) => n.toLocaleString('vi-VN');

// ---------- sub-components ----------

interface StatCardProps {
  label: string;
  value: number | string;
  sub?: string;
  icon: React.ReactNode;
  accent: string;
}

const StatCard = ({ label, value, sub, icon, accent }: StatCardProps) => (
  <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 flex items-start gap-4">
    <div className={`${accent} text-white rounded-lg p-3 flex-shrink-0`}>{icon}</div>
    <div className="min-w-0">
      <p className="text-sm text-gray-500 truncate">{label}</p>
      <p className="text-2xl font-bold text-gray-900 mt-0.5">{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-0.5">{sub}</p>}
    </div>
  </div>
);

const HorizontalBar = ({ value, max, colorClass }: { value: number; max: number; colorClass: string }) => {
  const pct = max > 0 ? Math.max(2, Math.round((value / max) * 100)) : 2;
  return (
    <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
      <div className={`${colorClass} h-2.5 rounded-full transition-all duration-500`} style={{ width: `${pct}%` }} />
    </div>
  );
};

const PERIOD_OPTIONS = [
  { value: 7, label: '1 tuần qua' },
  { value: 30, label: '1 tháng qua' },
  { value: 180, label: '6 tháng qua' },
  { value: 365, label: '1 năm qua' },
];

// ---------- main page ----------

const DashboardPage = () => {
  const [selectedDays, setSelectedDays] = useState(7);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [selectedGenerator, setSelectedGenerator] = useState('');

  const { data: stats, isLoading, isError, refetch } = useQuery({
    queryKey: ['admin-dashboard-statistics', selectedDays],
    queryFn: () => articlesService.getDashboardStatistics(selectedDays),
    staleTime: 2 * 60 * 1000, // 2 min
  });

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64 text-gray-400">
        <RefreshCw className="animate-spin mr-2" size={20} />
        <span>Đang tải thống kê…</span>
      </div>
    );
  }

  if (isError || !stats) {
    return (
      <div className="flex flex-col items-center justify-center h-64 gap-3 text-red-500">
        <AlertCircle size={32} />
        <p className="text-sm">Không thể tải dữ liệu thống kê.</p>
        <button
          onClick={() => refetch()}
          className="text-xs px-3 py-1.5 border border-red-400 rounded-lg hover:bg-red-50 transition"
        >
          Thử lại
        </button>
      </div>
    );
  }

  const maxCategoryCount = Math.max(...stats.byCategory.map((c) => c.articleCount), 1);
  const maxGeneratorCount = Math.max(...stats.byGenerator.map((g) => g.articleCount), 1);
  const maxStatusCount = Math.max(...stats.byStatus.map((s) => s.articleCount), 1);

  const filteredCategories = selectedCategory
    ? stats.byCategory.filter((c) => c.categoryName === selectedCategory)
    : stats.byCategory;

  const filteredGenerators = selectedGenerator
    ? stats.byGenerator.filter((g) => g.generatorName === selectedGenerator)
    : stats.byGenerator;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-gray-900">Tổng quan Hệ Thống</h1>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 border border-gray-200 rounded-lg px-3 py-1.5 transition"
        >
          <RefreshCw size={14} />
          Làm mới
        </button>
      </div>

      {/* Overview cards — row 1 */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          label="Tổng bài báo"
          value={formatNumber(stats.totalArticles)}
          icon={<FileText size={20} />}
          accent="bg-blue-500"
        />
        <StatCard
          label="Tổng lượt thích"
          value={formatNumber(stats.totalLikes)}
          icon={<Heart size={20} />}
          accent="bg-pink-500"
        />
        <StatCard
          label="Danh mục"
          value={formatNumber(stats.totalActiveCategories)}
          sub={`/ ${formatNumber(stats.totalCategories)} tổng`}
          icon={<FolderTree size={20} />}
          accent="bg-purple-500"
        />
        <StatCard
          label="Nguồn tin"
          value={formatNumber(stats.totalActiveGenerators)}
          sub={`/ ${formatNumber(stats.totalGenerators)} tổng`}
          icon={<Rss size={20} />}
          accent="bg-orange-500"
        />
      </div>

      {/* Recency card with period selector */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 flex flex-col sm:flex-row sm:items-center gap-4">
        <div className="flex items-center gap-4 flex-1">
          <div className="bg-emerald-500 text-white rounded-lg p-3 flex-shrink-0">
            <TrendingUp size={20} />
          </div>
          <div>
            <p className="text-sm text-gray-500">
              Bài đăng trong{' '}
              <strong className="text-gray-900">
                {PERIOD_OPTIONS.find((o) => o.value === selectedDays)?.label ?? `${selectedDays} ngày qua`}
              </strong>
            </p>
            <p className="text-3xl font-bold text-gray-900 mt-0.5">
              {formatNumber(stats.publishedLastNDays)}
            </p>
          </div>
        </div>
        <select
          value={selectedDays}
          onChange={(e) => setSelectedDays(Number(e.target.value))}
          className="rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white self-start sm:self-auto"
        >
          {PERIOD_OPTIONS.map((opt) => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>

      {/* Breakdown section */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* By status */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h2 className="text-base font-semibold text-gray-800 mb-4">Theo trạng thái</h2>
          <div className="space-y-3">
            {stats.byStatus.map((item: StatusStatisticsDto) => (
              <div key={item.status}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-gray-600">{STATUS_LABELS[item.status] ?? item.status}</span>
                  <span className="font-medium text-gray-900">{formatNumber(item.articleCount)}</span>
                </div>
                <HorizontalBar
                  value={item.articleCount}
                  max={maxStatusCount}
                  colorClass={STATUS_COLORS[item.status] ?? 'bg-gray-400'}
                />
              </div>
            ))}
          </div>
        </div>

        {/* By category */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h2 className="text-base font-semibold text-gray-800 mb-3">Theo danh mục</h2>
          <div className="mb-3">
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full rounded-lg border border-gray-200 px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-green-500 bg-white"
            >
              <option value="">Tất cả danh mục</option>
              {stats.byCategory.map((c) => (
                <option key={c.categoryName} value={c.categoryName}>{c.categoryName}</option>
              ))}
            </select>
          </div>
          <div className="space-y-3 max-h-64 overflow-y-auto pr-1">
            {filteredCategories.length === 0 ? (
              <p className="text-xs text-gray-400 text-center py-4">Không có dữ liệu</p>
            ) : (
              filteredCategories.map((item: CategoryStatisticsDto) => (
                <div key={item.categoryName}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600 truncate max-w-[160px]">{item.categoryName}</span>
                    <span className="font-medium text-gray-900 ml-2 flex-shrink-0">
                      {formatNumber(item.articleCount)}
                    </span>
                  </div>
                  <HorizontalBar value={item.articleCount} max={maxCategoryCount} colorClass="bg-blue-400" />
                </div>
              ))
            )}
          </div>
        </div>

        {/* By generator */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5">
          <h2 className="text-base font-semibold text-gray-800 mb-3">Theo nguồn tin</h2>
          <div className="mb-3">
            <select
              value={selectedGenerator}
              onChange={(e) => setSelectedGenerator(e.target.value)}
              className="w-full rounded-lg border border-gray-200 px-3 py-1.5 text-xs focus:outline-none focus:ring-2 focus:ring-green-500 bg-white"
            >
              <option value="">Tất cả nguồn tin</option>
              {stats.byGenerator.map((g) => (
                <option key={g.generatorName} value={g.generatorName}>{g.generatorName}</option>
              ))}
            </select>
          </div>
          <div className="space-y-3 max-h-64 overflow-y-auto pr-1">
            {filteredGenerators.length === 0 ? (
              <p className="text-xs text-gray-400 text-center py-4">Không tìm thấy nguồn tin</p>
            ) : (
              filteredGenerators.map((item: GeneratorStatisticsDto) => (
                <div key={item.generatorName}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-gray-600 truncate max-w-[160px]">{item.generatorName}</span>
                    <span className="font-medium text-gray-900 ml-2 flex-shrink-0">
                      {formatNumber(item.articleCount)}
                    </span>
                  </div>
                  <HorizontalBar value={item.articleCount} max={maxGeneratorCount} colorClass="bg-orange-400" />
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default DashboardPage;

