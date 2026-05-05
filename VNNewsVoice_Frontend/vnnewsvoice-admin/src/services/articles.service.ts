import apiClient, { ARTICLE_SERVICE_URL } from '../lib/apiClient';

interface ApiResponse<T> {
  result: T;
}

// --- Dashboard Statistics ---

export interface CategoryStatisticsDto {
  categoryName: string;
  articleCount: number;
}

export interface GeneratorStatisticsDto {
  generatorName: string;
  articleCount: number;
}

export interface StatusStatisticsDto {
  status: string;
  articleCount: number;
}

export interface DashboardStatisticsDto {
  totalArticles: number;
  totalLikes: number;
  totalActiveCategories: number;
  totalCategories: number;
  totalActiveGenerators: number;
  totalGenerators: number;
  publishedLast7Days: number;
  publishedLast30Days: number;
  publishedLastNDays: number;
  byStatus: StatusStatisticsDto[];
  byCategory: CategoryStatisticsDto[];
  byGenerator: GeneratorStatisticsDto[];
}

interface BackendArticleDto {
  id: string;
  title: string;
  slug: string;
  status: string;
  categoryIdId?: number;
  categoryIdName: string;
  generatorIdName: string;
  createdAt: string;
  publishedDate: string;
  summary?: string;
  topImageUrl?: string;
  audioUrl?: string;
  videoUrl?: string;
  isVideoAccepted?: boolean;
}

interface PaginationDto {
  currentPage: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
  startIndex: number;
  endIndex: number;
}

interface BackendArticleListResponse {
  articles: BackendArticleDto[];
  pagination: PaginationDto;
}

export interface ArticleBlockDto {
  id: number;
  orderIndex: number;
  type: string;
  content?: string;
  text?: string;
  tag?: string;
  src?: string;
  alt?: string;
  caption?: string;
}

interface BackendArticleDetailResponse {
  article: BackendArticleDto;
  blocks: ArticleBlockDto[];
}

export interface ArticleDto {
  id: string;
  title: string;
  slug: string;
  status: string;
  categoryId?: number;
  categoryName: string;
  generatorName: string;
  createdAt: string;
  publishedAt: string;
  summary?: string;
  topImageUrl?: string;
  audioUrl?: string;
  videoUrl?: string;
  isVideoAccepted?: boolean;
}

export interface ArticleListResponse {
  articles: ArticleDto[];
  totalItems: number;
  currentPage: number;
  totalPages: number;
  startIndex: number;
  endIndex: number;
}

export interface ArticleDetailResponse {
  article: ArticleDto;
  blocks: ArticleBlockDto[];
}

export interface CategoryDto {
  id: number;
  name: string;
  description?: string;
  isActive: boolean;
}

interface BackendAdminCategoryListResponse {
  categories: CategoryDto[];
  totalItems: number;
  currentPage: number;
  totalPages: number;
  startIndex: number;
  endIndex: number;
}

export interface AdminCategoryListResponse {
  categories: CategoryDto[];
  totalItems: number;
  currentPage: number;
  totalPages: number;
  startIndex: number;
  endIndex: number;
}

const normalizeArticle = (article: BackendArticleDto): ArticleDto => ({
  id: article.id,
  title: article.title,
  slug: article.slug,
  status: article.status,
  categoryId: article.categoryIdId,
  categoryName: article.categoryIdName,
  generatorName: article.generatorIdName,
  createdAt: article.createdAt,
  publishedAt: article.publishedDate,
  summary: article.summary,
  topImageUrl: article.topImageUrl,
  audioUrl: article.audioUrl,
  videoUrl: article.videoUrl,
  isVideoAccepted: article.isVideoAccepted,
});

export const articlesService = {
  getArticles: async (params: {
    page: number;
    pageSize: number;
    title?: string;
    status?: string;
    categoryId?: number;
    generatorId?: number;
    fromDate?: string;
    toDate?: string;
  }) => {
    const res = await apiClient.get<ApiResponse<BackendArticleListResponse>>(
      `${ARTICLE_SERVICE_URL}/api/secure/admin/articles`,
      { params }
    );

    return {
      articles: res.data.result.articles.map(normalizeArticle),
      totalItems: res.data.result.pagination.totalItems,
      currentPage: res.data.result.pagination.currentPage,
      totalPages: res.data.result.pagination.totalPages,
      startIndex: res.data.result.pagination.startIndex,
      endIndex: res.data.result.pagination.endIndex,
    } satisfies ArticleListResponse;
  },

  getArticleDetail: async (id: string) => {
    const res = await apiClient.get<ApiResponse<BackendArticleDetailResponse>>(
      `${ARTICLE_SERVICE_URL}/api/secure/admin/articles/${id}`
    );

    const sortedBlocks = [...(res.data.result.blocks ?? [])].sort(
      (a, b) => a.orderIndex - b.orderIndex
    );

    return {
      article: normalizeArticle(res.data.result.article),
      blocks: sortedBlocks,
    } satisfies ArticleDetailResponse;
  },

  changeStatus: async (id: string, status: string) => {
    const res = await apiClient.put(
      `${ARTICLE_SERVICE_URL}/api/secure/admin/articles/${id}/change-status`,
      { status }
    );
    return res.data;
  },

  deleteArticle: async (id: string) => {
    const res = await apiClient.delete(
      `${ARTICLE_SERVICE_URL}/api/secure/admin/articles/${id}`
    );
    return res.data;
  },

  getCategories: async () => {
    const res = await apiClient.get<ApiResponse<BackendAdminCategoryListResponse>>(
      `${ARTICLE_SERVICE_URL}/api/secure/admin/categories`,
      {
        params: {
          page: 1,
          pageSize: 500,
        },
      }
    );

    return res.data.result.categories;
  },

  saveCategory: async (articleId: string, categoryId: number) => {
    const res = await apiClient.put(
      `${ARTICLE_SERVICE_URL}/api/secure/admin/articles/${articleId}/save-category`,
      null,
      {
        params: { categoryId },
      }
    );
    return res.data;
  },

  getAdminCategories: async (params: {
    page: number;
    pageSize: number;
    name?: string;
    isActive?: boolean;
  }) => {
    const res = await apiClient.get<ApiResponse<BackendAdminCategoryListResponse>>(
      `${ARTICLE_SERVICE_URL}/api/secure/admin/categories`,
      { params }
    );

    return {
      categories: res.data.result.categories,
      totalItems: res.data.result.totalItems,
      currentPage: res.data.result.currentPage,
      totalPages: res.data.result.totalPages,
      startIndex: res.data.result.startIndex,
      endIndex: res.data.result.endIndex,
    } satisfies AdminCategoryListResponse;
  },

  createCategory: async (payload: { name: string; isActive?: boolean }) => {
    const res = await apiClient.post<ApiResponse<CategoryDto>>(
      `${ARTICLE_SERVICE_URL}/api/secure/admin/categories`,
      payload
    );
    return res.data.result;
  },

  updateCategory: async (id: number, payload: { name: string; isActive?: boolean }) => {
    const res = await apiClient.put<ApiResponse<CategoryDto>>(
      `${ARTICLE_SERVICE_URL}/api/secure/admin/categories/${id}`,
      payload
    );
    return res.data.result;
  },

  toggleCategoryStatus: async (id: number) => {
    const res = await apiClient.put(
      `${ARTICLE_SERVICE_URL}/api/secure/admin/categories/${id}/status`
    );
    return res.data;
  },

  deleteCategory: async (id: number) => {
    const res = await apiClient.delete(
      `${ARTICLE_SERVICE_URL}/api/secure/admin/categories/${id}`
    );
    return res.data;
  },

  getDashboardStatistics: async (days = 7): Promise<DashboardStatisticsDto> => {
    const res = await apiClient.get<ApiResponse<DashboardStatisticsDto>>(
      `${ARTICLE_SERVICE_URL}/api/secure/admin/statistics`,
      { params: { days } }
    );
    return res.data.result;
  },

  generateVideo: async (
    articleId: string,
    videoStyle?: string,
    durationSeconds?: number,
  ) => {
    const res = await apiClient.post(
      `${ARTICLE_SERVICE_URL}/api/secure/admin/articles/${articleId}/generate-video`,
      null,
      {
        params: {
          ...(videoStyle ? { videoStyle } : {}),
          ...(durationSeconds ? { durationSeconds } : {}),
        },
      },
    );
    return res.data;
  },

  rejectVideo: async (articleId: string) => {
    const res = await apiClient.delete(
      `${ARTICLE_SERVICE_URL}/api/secure/admin/articles/${articleId}/video`,
    );
    return res.data;
  },

  acceptVideo: async (articleId: string) => {
    const res = await apiClient.post(
      `${ARTICLE_SERVICE_URL}/api/secure/admin/articles/${articleId}/video/accept`,
    );
    return res.data;
  },
};
