import { useEffect } from 'react';
import { CheckCircle, Film, RefreshCw, X } from 'lucide-react';
import { VIDEO_STYLES, VIDEO_DURATIONS } from '../constants/videoConstants';

interface VideoGenerationOverlayProps {
  state: 'generating' | 'preview';
  videoUrl?: string;
  elapsedSeconds: number;
  videoStyle: string;
  durationSeconds: number;
  onStyleChange: (style: string) => void;
  onDurationChange: (duration: number) => void;
  onAccept: () => void;
  onReject: () => void;
  onRetry: () => void;
  isAccepting: boolean;
  isRejecting: boolean;
}

const formatElapsed = (seconds: number) => {
  const m = Math.floor(seconds / 60).toString().padStart(2, '0');
  const s = (seconds % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
};

export const VideoGenerationOverlay = ({
  state,
  videoUrl,
  elapsedSeconds,
  videoStyle,
  durationSeconds,
  onStyleChange,
  onDurationChange,
  onAccept,
  onReject,
  onRetry,
  isAccepting,
  isRejecting,
}: VideoGenerationOverlayProps) => {
  // Lock body scroll while overlay is open
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = '';
    };
  }, []);

  return (
    <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/75 backdrop-blur-sm">
      {state === 'generating' ? (
        /* ── GENERATING STATE ── */
        <div className="flex flex-col items-center gap-6 max-w-sm w-full mx-4 text-center select-none">
          {/* Spinner ring */}
          <div className="relative w-24 h-24">
            <div className="absolute inset-0 rounded-full border-4 border-white/20" />
            <div className="absolute inset-0 rounded-full border-4 border-t-violet-400 border-r-transparent border-b-transparent border-l-transparent animate-spin" />
            <Film className="absolute inset-0 m-auto text-white" size={36} />
          </div>

          <div className="space-y-2">
            <h2 className="text-2xl font-bold text-white">Đang tạo video AI...</h2>
            <p className="text-4xl font-mono font-semibold text-violet-300">
              {formatElapsed(elapsedSeconds)}
            </p>
          </div>

          <div className="space-y-1 text-white/70 text-sm leading-relaxed">
            <p>Mô hình Veo đang xử lý yêu cầu của bạn.</p>
            <p>
              Quá trình có thể mất từ{' '}
              <strong className="text-white">1 đến 3 phút</strong>.
            </p>
          </div>

          <div className="rounded-xl border border-amber-500/40 bg-amber-500/10 px-5 py-3 text-amber-200 text-sm">
            ⚠️ Vui lòng <strong className="text-amber-100">không đóng tab</strong> này cho đến khi hoàn thành.
          </div>
        </div>
      ) : (
        /* ── PREVIEW STATE ── */
        <div className="bg-white rounded-2xl shadow-2xl w-full max-w-2xl mx-4 overflow-hidden max-h-[90vh] flex flex-col">
          {/* Header */}
          <div className="bg-gradient-to-r from-violet-600 to-purple-700 px-6 py-4 flex-shrink-0">
            <h2 className="text-lg font-bold text-white flex items-center gap-2">
              <Film size={20} /> Xem trước video
            </h2>
            <p className="text-violet-200 text-sm mt-0.5">
              Xem video rồi chấp nhận, thử lại hoặc từ chối.
            </p>
          </div>

          <div className="p-6 space-y-5 overflow-y-auto">
            {/* Video player */}
            <div className="rounded-xl overflow-hidden bg-black aspect-video">
              {videoUrl && (
                <video src={videoUrl} controls autoPlay className="w-full h-full" />
              )}
            </div>

            {/* Retry config */}
            <div className="rounded-xl border border-gray-200 bg-gray-50 p-4 space-y-3">
              <p className="text-sm font-medium text-gray-600">
                Cấu hình lại cho lần thử tiếp theo:
              </p>
              <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
                <div className="flex-1 space-y-1">
                  <label className="text-xs font-medium text-gray-500">Phong cách video</label>
                  <select
                    value={videoStyle}
                    onChange={(e) => onStyleChange(e.target.value)}
                    className="w-full rounded-lg border border-gray-200 bg-white px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-violet-500"
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
                        onClick={() => onDurationChange(d)}
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
            </div>

            {/* Action buttons */}
            <div className="flex flex-col gap-3 sm:flex-row sm:justify-end">
              <button
                type="button"
                onClick={onReject}
                disabled={isRejecting}
                className="inline-flex items-center justify-center gap-2 rounded-lg border border-red-200 bg-red-50 px-4 py-2.5 text-sm font-semibold text-red-600 hover:bg-red-100 disabled:opacity-60 transition-colors"
              >
                <X size={16} />
                {isRejecting ? 'Đang từ chối...' : 'Từ chối'}
              </button>

              <button
                type="button"
                onClick={onRetry}
                className="inline-flex items-center justify-center gap-2 rounded-lg border border-violet-200 bg-violet-50 px-4 py-2.5 text-sm font-semibold text-violet-700 hover:bg-violet-100 transition-colors"
              >
                <RefreshCw size={16} /> Thử lại
              </button>

              <button
                type="button"
                onClick={onAccept}
                disabled={isAccepting}
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-green-600 px-4 py-2.5 text-sm font-semibold text-white hover:bg-green-700 disabled:opacity-60 transition-colors"
              >
                <CheckCircle size={16} /> {isAccepting ? 'Đang lưu...' : 'Chấp nhận'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
