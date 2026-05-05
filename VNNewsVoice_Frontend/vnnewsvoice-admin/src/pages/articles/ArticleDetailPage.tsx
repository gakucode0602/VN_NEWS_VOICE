import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  ArrowLeft,
  CalendarDays,
  CheckCircle,
  Film,
  FolderOpen,
  Newspaper,
  RefreshCw,
  Save,
  Trash2,
  Volume2,
} from 'lucide-react';
import { articlesService } from '../../services/articles.service';
import type { ArticleBlockDto } from '../../services/articles.service';
import { VideoGenerationOverlay } from '../../components/VideoGenerationOverlay';
import { VIDEO_STYLES, VIDEO_DURATIONS } from '../../constants/videoConstants';

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

const formatPublishedDate = (value?: string) => {
  if (!value) {
    return 'Chưa có ngày đăng';
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleDateString('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  });
};

const renderHeadingBlock = (block: ArticleBlockDto) => {
  const text = (block.text || block.content || '').trim();
  if (!text) {
    return null;
  }

  const tag = (block.tag || 'h2').toLowerCase();

  if (tag === 'h1') {
    return <h1 className="text-2xl font-bold text-gray-900 leading-tight">{text}</h1>;
  }

  if (tag === 'h3') {
    return <h3 className="text-lg font-semibold text-gray-900 leading-snug">{text}</h3>;
  }

  return <h2 className="text-xl font-semibold text-gray-900 leading-snug">{text}</h2>;
};

const renderArticleBlock = (block: ArticleBlockDto) => {
  const type = (block.type || '').toLowerCase();

  if (type === 'heading') {
    return renderHeadingBlock(block);
  }

  if (type === 'image') {
    if (!block.src) {
      return null;
    }

    return (
      <figure className="space-y-2 max-w-3xl mx-auto">
        <img
          src={block.src}
          alt={block.alt || 'Article image'}
          className="max-h-[420px] w-auto max-w-full mx-auto rounded-lg border border-gray-100 bg-gray-50 object-contain"
          loading="lazy"
          referrerPolicy="no-referrer"
        />
        {block.caption && (
          <figcaption className="text-sm text-gray-500 italic text-center">{block.caption}</figcaption>
        )}
      </figure>
    );
  }

  if (block.content && /<[^>]+>/.test(block.content)) {
    return (
      <div
        className="text-[15px] leading-7 text-gray-700 [&_p]:mb-4 [&_a]:text-blue-600 [&_a]:underline"
        dangerouslySetInnerHTML={{ __html: block.content }}
      />
    );
  }

  const text = (block.text || block.content || '').trim();
  if (!text) {
    return null;
  }

  return <p className="text-[15px] leading-7 text-gray-700 whitespace-pre-line">{text}</p>;
};

const STATUS_LABELS: Record<string, string> = {
  DRAFT: 'Bản nháp',
  PENDING: 'Chờ duyệt',
  PUBLISHED: 'Đã xuất bản',
  REJECTED: 'Từ chối',
  DELETED: 'Đã xoá',
};

// Which statuses an admin can manually transition TO from each current status.
// Does NOT include DELETED here — deletion is handled via the dedicated delete button.
const VALID_TRANSITIONS: Record<string, string[]> = {
  DRAFT: ['PENDING'],
  PENDING: ['PUBLISHED', 'REJECTED'],
  REJECTED: ['PENDING'],
  PUBLISHED: ['REJECTED'],
  DELETED: ['PENDING', 'PUBLISHED'],
};

const ArticleDetailPage = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [selectedCategoryId, setSelectedCategoryId] = useState('');
  const [categoryFeedback, setCategoryFeedback] = useState<FeedbackState>(null);
  const [pendingStatus, setPendingStatus] = useState('');
  const [statusFeedback, setStatusFeedback] = useState<FeedbackState>(null);

  // Video generation state
  const [audioError, setAudioError] = useState(false);
  const [videoGenState, setVideoGenState] = useState<'idle' | 'generating' | 'preview'>('idle');
  const [videoStyle, setVideoStyle] = useState('news');
  const [durationSeconds, setDurationSeconds] = useState(8);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [videoGenError, setVideoGenError] = useState<string | null>(null);

  const { data, isLoading, error } = useQuery({
    queryKey: ['admin-article-detail', id],
    queryFn: () => articlesService.getArticleDetail(id as string),
    enabled: !!id,
    refetchInterval: videoGenState === 'generating' ? 5000 : false,
  });

  const { data: categoriesResponse, isLoading: isLoadingCategories } = useQuery({
    queryKey: ['admin-article-categories-for-detail'],
    queryFn: () =>
      articlesService.getAdminCategories({
        page: 1,
        pageSize: 200,
      }),
  });

  const categories = categoriesResponse?.categories ?? [];

  const changeStatusMutation = useMutation({
    mutationFn: ({ articleId, status }: { articleId: string; status: string }) =>
      articlesService.changeStatus(articleId, status),
    onSuccess: () => {
      setPendingStatus('');
      setStatusFeedback({ type: 'success', text: 'Đã cập nhật trạng thái bài viết.' });
      queryClient.invalidateQueries({ queryKey: ['admin-article-detail', id] });
      queryClient.invalidateQueries({ queryKey: ['admin-articles'] });
    },
    onError: (mutationError) => {
      setStatusFeedback({
        type: 'error',
        text: getErrorMessage(mutationError, 'Không thể cập nhật trạng thái.'),
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (articleId: string) => articlesService.deleteArticle(articleId),
    onSuccess: () => {
      setStatusFeedback({ type: 'success', text: 'Đã xoá bài viết.' });
      queryClient.invalidateQueries({ queryKey: ['admin-articles'] });
      navigate(-1);
    },
    onError: (mutationError) => {
      setStatusFeedback({
        type: 'error',
        text: getErrorMessage(mutationError, 'Không thể xoá bài viết.'),
      });
    },
  });

  const saveCategoryMutation = useMutation({
    mutationFn: (categoryId: number) => articlesService.saveCategory(id as string, categoryId),
    onSuccess: () => {
      setCategoryFeedback({ type: 'success', text: 'Đã cập nhật danh mục cho bài viết.' });
      queryClient.invalidateQueries({ queryKey: ['admin-article-detail', id] });
      queryClient.invalidateQueries({ queryKey: ['admin-articles'] });
    },
    onError: (mutationError) => {
      setCategoryFeedback({
        type: 'error',
        text: getErrorMessage(mutationError, 'Không thể cập nhật danh mục.'),
      });
    },
  });

  const generateVideoMutation = useMutation({
    mutationFn: () => articlesService.generateVideo(id!, videoStyle, durationSeconds),
    onSuccess: () => {
      setVideoGenState('generating');
      setElapsedSeconds(0);
      setVideoGenError(null);
    },
    onError: (mutationError) => {
      setVideoGenError(getErrorMessage(mutationError, 'Không thể gửi yêu cầu tạo video.'));
    },
  });

  const acceptVideoMutation = useMutation({
    mutationFn: () => articlesService.acceptVideo(id!),
    onSuccess: () => {
      setVideoGenState('idle');
      queryClient.invalidateQueries({ queryKey: ['admin-article-detail', id] });
      queryClient.invalidateQueries({ queryKey: ['admin-articles'] });
    },
  });

  const rejectVideoMutation = useMutation({
    mutationFn: () => articlesService.rejectVideo(id!),
    onSuccess: () => {
      setVideoGenState('idle');
      queryClient.invalidateQueries({ queryKey: ['admin-article-detail', id] });
      queryClient.invalidateQueries({ queryKey: ['admin-articles'] });
    },
  });

  // Derived state: transition to 'preview' when polled data shows videoUrl arrived
  const effectiveVideoGenState: 'idle' | 'generating' | 'preview' =
    videoGenState === 'generating' && data?.article?.videoUrl ? 'preview' : videoGenState;

  // Elapsed timer (increments every second while generating)
  useEffect(() => {
    if (videoGenState !== 'generating') return;
    const t = setInterval(() => setElapsedSeconds((s) => s + 1), 1000);
    return () => clearInterval(t);
  }, [videoGenState]);

  // beforeunload guard + 10-minute timeout
  useEffect(() => {
    if (videoGenState !== 'generating') return;
    const handler = (e: BeforeUnloadEvent) => {
      e.preventDefault();
    };
    window.addEventListener('beforeunload', handler);
    const timeout = setTimeout(() => {
      setVideoGenState('idle');
      setVideoGenError('Quá thời gian chờ (10 phút). Veo có thể đang bận. Thử lại sau.');
    }, 600_000);
    return () => {
      window.removeEventListener('beforeunload', handler);
      clearTimeout(timeout);
    };
  }, [videoGenState]);

  const article = data?.article;
  const blocks = data?.blocks ?? [];
  const assignableCategories = categories.filter(
    (category) => category.isActive || category.id === article?.categoryId
  );

  const effectiveSelectedCategoryId =
    selectedCategoryId || (article?.categoryId ? String(article.categoryId) : '');

  const effectivePendingStatus = pendingStatus || article?.status || '';

  const handleChangeStatus = () => {
    if (!effectivePendingStatus || effectivePendingStatus === article?.status) return;
    setStatusFeedback(null);
    changeStatusMutation.mutate({ articleId: id as string, status: effectivePendingStatus });
  };

  const handleSaveCategory = () => {
    if (!effectiveSelectedCategoryId) {
      setCategoryFeedback({ type: 'error', text: 'Vui lòng chọn danh mục trước khi cập nhật.' });
      return;
    }

    const categoryId = Number(effectiveSelectedCategoryId);
    if (Number.isNaN(categoryId)) {
      setCategoryFeedback({ type: 'error', text: 'Danh mục không hợp lệ.' });
      return;
    }

    const selectedCategory = categories.find((category) => category.id === categoryId);
    if (!selectedCategory) {
      setCategoryFeedback({ type: 'error', text: 'Không tìm thấy danh mục đã chọn.' });
      return;
    }

    if (!selectedCategory.isActive && article?.categoryId !== selectedCategory.id) {
      setCategoryFeedback({
        type: 'error',
        text: 'Danh mục đã bị vô hiệu hóa. Vui lòng chọn danh mục đang hoạt động.',
      });
      return;
    }

    setCategoryFeedback(null);
    saveCategoryMutation.mutate(categoryId);
  };

  return (
    <div className="space-y-6">
      {/* Video generation overlay — renders on top of everything while generating/previewing */}
      {effectiveVideoGenState !== 'idle' && (
        <VideoGenerationOverlay
          state={effectiveVideoGenState}
          videoUrl={data?.article?.videoUrl}
          elapsedSeconds={elapsedSeconds}
          videoStyle={videoStyle}
          durationSeconds={durationSeconds}
          onStyleChange={setVideoStyle}
          onDurationChange={setDurationSeconds}
          onAccept={() => acceptVideoMutation.mutate()}
          onReject={() => rejectVideoMutation.mutate()}
          onRetry={() => generateVideoMutation.mutate()}
          isAccepting={acceptVideoMutation.isPending}
          isRejecting={rejectVideoMutation.isPending}
        />
      )}

      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-sm text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft size={16} /> Quay lại
      </button>

      {isLoading ? (
        <div className="flex items-center gap-2 text-gray-400 py-20 justify-center">
          <RefreshCw className="animate-spin" size={20} /> Đang tải...
        </div>
      ) : error ? (
        <div className="text-center py-20 text-red-500">Không tìm thấy bài báo</div>
      ) : (
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-8 space-y-4">
            <h1 className="text-2xl font-bold text-gray-900">{article?.title}</h1>
            <div className="flex flex-wrap gap-x-6 gap-y-2 text-sm text-gray-500">
              <span className="inline-flex items-center gap-2">
                <FolderOpen size={14} />
                <strong>{article?.categoryName || 'Chưa phân loại'}</strong>
              </span>
              <span className="inline-flex items-center gap-2">
                <Newspaper size={14} />
                <strong>{article?.generatorName || 'Không rõ nguồn'}</strong>
              </span>
              <span className="inline-flex items-center gap-2">
                <CalendarDays size={14} />
                <strong>{formatPublishedDate(article?.publishedAt)}</strong>
              </span>
              <span>
                Trạng thái: <strong>{article?.status || 'N/A'}</strong>
              </span>
            </div>

            {article?.topImageUrl && (
              <img
                src={article.topImageUrl}
                alt={article.title}
                className="rounded-lg max-h-72 w-auto max-w-full mx-auto object-contain border border-gray-100 bg-gray-50"
                referrerPolicy="no-referrer"
              />
            )}
          </div>

          <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">Trạng thái &amp; thao tác</h2>

            {statusFeedback && (
              <div
                className={`rounded-lg border px-3 py-2 text-sm ${
                  statusFeedback.type === 'success'
                    ? 'border-green-200 bg-green-50 text-green-700'
                    : 'border-red-200 bg-red-50 text-red-700'
                }`}
              >
                {statusFeedback.text}
              </div>
            )}

            <div className="space-y-3">
              <p className="text-sm text-gray-600">
                Trạng thái hiện tại:{' '}
                <strong className="text-gray-900">
                  {STATUS_LABELS[article?.status ?? ''] ?? article?.status ?? 'N/A'}
                </strong>
              </p>
              {(VALID_TRANSITIONS[article?.status ?? ''] ?? []).length > 0 ? (
                <div className="flex flex-col gap-2 md:flex-row">
                  <select
                    value={effectivePendingStatus}
                    onChange={(e) => setPendingStatus(e.target.value)}
                    className="flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                  >
                    <option value="">-- Chọn trạng thái --</option>
                    {(VALID_TRANSITIONS[article?.status ?? ''] ?? []).map((val) => (
                      <option key={val} value={val}>
                        {STATUS_LABELS[val]}
                      </option>
                    ))}
                  </select>
                  <button
                    type="button"
                    onClick={handleChangeStatus}
                    disabled={
                      changeStatusMutation.isPending ||
                      !effectivePendingStatus ||
                      effectivePendingStatus === article?.status
                    }
                    className="inline-flex items-center justify-center gap-2 rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-60"
                  >
                    <CheckCircle size={16} />
                    {changeStatusMutation.isPending ? 'Đang cập nhật...' : 'Cập nhật trạng thái'}
                  </button>
                  {article?.status !== 'DELETED' && (
                    <button
                      type="button"
                      onClick={() => {
                        setStatusFeedback(null);
                        deleteMutation.mutate(id as string);
                      }}
                      disabled={deleteMutation.isPending}
                      className="inline-flex items-center justify-center gap-2 rounded-lg bg-red-600 px-4 py-2 text-sm font-semibold text-white hover:bg-red-700 disabled:opacity-60"
                    >
                      <Trash2 size={16} />
                      {deleteMutation.isPending ? 'Đang xoá...' : 'Xoá bài viết'}
                    </button>
                  )}
                </div>
              ) : (
                <p className="text-sm text-gray-400">Không có chuyển đổi trạng thái nào khả dụng.</p>
              )}
            </div>
          </section>

          <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-3">
            <h2 className="text-lg font-semibold text-gray-900">Phân loại bài viết</h2>
            <p className="text-sm text-gray-600">
              Danh mục hiện tại: <strong>{article?.categoryName || 'Chưa phân loại'}</strong>
            </p>

            {categoryFeedback && (
              <div
                className={`rounded-lg border px-3 py-2 text-sm ${
                  categoryFeedback.type === 'success'
                    ? 'border-green-200 bg-green-50 text-green-700'
                    : 'border-red-200 bg-red-50 text-red-700'
                }`}
              >
                {categoryFeedback.text}
              </div>
            )}

            <div className="flex flex-col gap-2 md:flex-row">
              <select
                value={effectiveSelectedCategoryId}
                onChange={(event) => setSelectedCategoryId(event.target.value)}
                className="flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500"
                disabled={isLoadingCategories}
              >
                <option value="">Chọn danh mục</option>
                {assignableCategories.map((category) => (
                  <option key={category.id} value={String(category.id)}>
                    {category.name}
                    {category.isActive ? '' : ' (Đã vô hiệu hóa - chỉ giữ cho bài cũ)'}
                  </option>
                ))}
              </select>

              <button
                type="button"
                onClick={handleSaveCategory}
                disabled={
                  saveCategoryMutation.isPending ||
                  !effectiveSelectedCategoryId ||
                  (article?.categoryId
                    ? String(article.categoryId) === effectiveSelectedCategoryId
                    : false)
                }
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-green-600 px-4 py-2 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-60"
              >
                <Save size={16} />
                {saveCategoryMutation.isPending ? 'Đang cập nhật...' : 'Cập nhật danh mục'}
              </button>
            </div>

            <p className="text-xs text-gray-500">
              Danh mục đã vô hiệu hóa chỉ giữ cho bài cũ và không thể gán mới.
            </p>
          </section>

          <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-3">
            <h2 className="text-lg font-semibold text-gray-900">Tóm tắt bài viết</h2>
            <div className="rounded-lg bg-gray-50 border border-gray-100 p-4 text-gray-700 whitespace-pre-line leading-7">
              {article?.summary?.trim() || 'Chưa có tóm tắt cho bài viết này.'}
            </div>
          </section>

          {article?.audioUrl && !audioError && (
          <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-3">
            <h2 className="text-lg font-semibold text-gray-900 inline-flex items-center gap-2">
              <Volume2 size={18} /> Audio bài viết
            </h2>
              <div className="rounded-lg bg-gray-50 border border-gray-100 p-4 space-y-2">
                <audio controls className="w-full" onError={() => setAudioError(true)}>
                  <source src={article.audioUrl} />
                  Trình duyệt của bạn không hỗ trợ audio.
                </audio>
                <p className="text-xs text-gray-500 break-all">URL: {article.audioUrl}</p>
              </div>
          </section>
          )}

          <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900 inline-flex items-center gap-2">
              <Film size={18} /> Video AI
            </h2>

            {videoGenError && (
              <div className="rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {videoGenError}
              </div>
            )}

            {article?.videoUrl && article.isVideoAccepted ? (
              /* Accepted video — show player + management buttons */
              <div className="space-y-3">
                <div className="rounded-xl overflow-hidden bg-black aspect-video">
                  <video src={article.videoUrl} controls className="w-full h-full" />
                </div>
                <div className="flex gap-2 flex-wrap">
                  <button
                    type="button"
                    onClick={() => generateVideoMutation.mutate()}
                    disabled={generateVideoMutation.isPending}
                    className="inline-flex items-center gap-2 rounded-lg border border-violet-200 bg-violet-50 px-3 py-2 text-sm font-semibold text-violet-700 hover:bg-violet-100 disabled:opacity-60 transition-colors"
                  >
                    <RefreshCw size={14} /> Tạo lại
                  </button>
                  <button
                    type="button"
                    onClick={() => rejectVideoMutation.mutate()}
                    disabled={rejectVideoMutation.isPending}
                    className="inline-flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm font-semibold text-red-600 hover:bg-red-100 disabled:opacity-60 transition-colors"
                  >
                    {rejectVideoMutation.isPending ? 'Đang bỏ...' : 'Bỏ video này'}
                  </button>
                </div>
              </div>
            ) : article?.videoUrl && !article.isVideoAccepted ? (
              /* Video generated but not yet accepted */
              <div className="rounded-lg border border-amber-200 bg-amber-50 p-4 space-y-3">
                <p className="text-sm text-amber-800">
                  Có video chưa được chấp nhận. Bạn có thể xem lại để quyết định.
                </p>
                <div className="flex gap-2 flex-wrap">
                  <button
                    type="button"
                    onClick={() => setVideoGenState('preview')}
                    className="inline-flex items-center gap-2 rounded-lg bg-violet-600 px-3 py-2 text-sm font-semibold text-white hover:bg-violet-700 transition-colors"
                  >
                    <Film size={14} /> Xem lại video
                  </button>
                  <button
                    type="button"
                    onClick={() => generateVideoMutation.mutate()}
                    disabled={generateVideoMutation.isPending}
                    className="inline-flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm font-semibold text-gray-700 hover:bg-gray-50 disabled:opacity-60 transition-colors"
                  >
                    <RefreshCw size={14} /> Tạo video mới
                  </button>
                </div>
              </div>
            ) : (
              /* No video yet — show generation form */
              <div className="space-y-3">
                <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
                  <div className="flex-1 space-y-1">
                    <label className="text-xs font-medium text-gray-500">Phong cách video</label>
                    <select
                      value={videoStyle}
                      onChange={(e) => setVideoStyle(e.target.value)}
                      className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
                    >
                      {VIDEO_STYLES.map((s) => (
                        <option key={s.value} value={s.value}>
                          {s.label}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="space-y-1">
                    <label className="text-xs font-medium text-gray-500">Thời lượng</label>
                    <div className="flex gap-2">
                      {VIDEO_DURATIONS.map((d) => (
                        <button
                          key={d}
                          type="button"
                          onClick={() => setDurationSeconds(d)}
                          className={`px-3 py-2 rounded-lg text-sm font-semibold border transition-colors ${
                            durationSeconds === d
                              ? 'bg-violet-600 text-white border-violet-600'
                              : 'bg-white text-gray-600 border-gray-200 hover:border-violet-400 hover:text-violet-600'
                          }`}
                        >
                          {d}s
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => generateVideoMutation.mutate()}
                  disabled={generateVideoMutation.isPending}
                  className="inline-flex items-center gap-2 rounded-lg bg-violet-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-violet-700 disabled:opacity-60 transition-colors"
                >
                  <Film size={16} />
                  {generateVideoMutation.isPending ? 'Đang gửi...' : 'Tạo Video AI'}
                </button>
              </div>
            )}
          </section>

          <section className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 space-y-4">
            <h2 className="text-lg font-semibold text-gray-900">Nội dung đầy đủ</h2>
            {blocks.length > 0 ? (
              <div className="space-y-4">
                {blocks.map((block, index) => (
                  <div
                    key={`${block.id ?? 'block'}-${block.orderIndex}-${index}`}
                    className="pb-4 last:pb-0 border-b border-gray-100/70 last:border-b-0"
                  >
                    {renderArticleBlock(block)}
                  </div>
                ))}
              </div>
            ) : (
              <div className="rounded-lg bg-gray-50 border border-gray-100 p-4 text-gray-500">
                Bài viết chưa có block nội dung.
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
};

export default ArticleDetailPage;
