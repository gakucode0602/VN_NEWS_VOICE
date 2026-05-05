import type { FormEvent } from "react";
import { useRef, useState } from "react";
import { Button, Card, Form, Spinner } from "react-bootstrap";
import { FaThumbsUp, FaTrash, FaReply } from "react-icons/fa";
import type { InfiniteData } from "@tanstack/react-query";
import { useInfiniteQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "../../auth/auth-context";
import ModalLogin from "../../auth/components/ModalLogin";
import {
  COMMENTS_ENABLED,
  createComment,
  deleteComment,
  getCommentById,
  toggleCommentLike,
  getComments,
} from "../../../services/comments.service";
import type {
  ApiError,
  Comment,
  CommentLikeResponse,
  CommentListResponse,
  CreateCommentRequest,
} from "../../../types";

type CommentsProps = {
  id: string | null;
};

const Comments = ({ id }: CommentsProps) => {
  const { isAuthenticated, user } = useAuth();
  const [commentText, setCommentText] = useState("");
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [replyingToId, setReplyingToId] = useState<number | null>(null);
  const [replyText, setReplyText] = useState("");
  const commentInputRef = useRef<HTMLTextAreaElement | null>(null);
  const queryClient = useQueryClient();

  const idValue = id ?? "";

  const commentsQuery = useInfiniteQuery<CommentListResponse, ApiError>({
    queryKey: ["comments", id],
    queryFn: ({ pageParam = 1 }) =>
      getComments(idValue, { page: Number(pageParam) }),
    enabled: Boolean(id),
    initialPageParam: 1,
    getNextPageParam: (lastPage) => {
      const pagination = lastPage?.pagination as (typeof lastPage.pagination & { hasNext?: boolean }) | undefined;
      if (!pagination) return undefined;
      // Prefer the backend's explicit hasNext flag; fall back to page comparison
      if (pagination.hasNext === false) return undefined;
      if (
        typeof pagination.currentPage === "number" &&
        typeof pagination.totalPages === "number" &&
        pagination.currentPage >= pagination.totalPages
      ) return undefined;
      return typeof pagination.currentPage === "number"
        ? pagination.currentPage + 1
        : undefined;
    },
  });

  // ── Top-level comment submit ────────────────────────────────────────────────
  const submitCommentMutation = useMutation<Comment, ApiError, CreateCommentRequest>({
    mutationFn: (payload: CreateCommentRequest) => createComment(idValue, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["comments", id] });
      setCommentText("");
    },
  });

  // ── Delete comment ──────────────────────────────────────────────────────────
  const deleteCommentMutation = useMutation<void, ApiError, number>({
    mutationFn: (commentId: number) => deleteComment(commentId),
    onSuccess: (_data, commentId) => {
      queryClient.setQueryData<InfiniteData<CommentListResponse>>(
        ["comments", id],
        (data) => {
          if (!data) return data;
          return {
            ...data,
            pages: data.pages.map((page) => {
              // Could be a top-level delete or a reply delete
              const isTopLevel = (page.comments || []).some((c) => c.id === commentId);
              return {
                ...page,
                comments: (page.comments || [])
                  .filter((c) => c.id !== commentId)
                  .map((c) => ({
                    ...c,
                    replies: (c.replies ?? []).filter((r) => r.id !== commentId),
                  })),
                pagination: isTopLevel
                  ? {
                      ...page.pagination,
                      totalItems: Math.max(0, (page.pagination?.totalItems ?? 1) - 1),
                    }
                  : page.pagination,
              };
            }),
          };
        }
      );
    },
  });

  // ── Like / unlike — optimistic with server reconciliation ──────────────────
  const likeMutation = useMutation<
    CommentLikeResponse,
    ApiError,
    number,
    { previousData: InfiniteData<CommentListResponse> | undefined }
  >({
    mutationFn: (commentId: number) => toggleCommentLike(commentId),
    onMutate: async (commentId) => {
      await queryClient.cancelQueries({ queryKey: ["comments", id] });
      const previousData = queryClient.getQueryData<InfiniteData<CommentListResponse>>(
        ["comments", id]
      );
      queryClient.setQueryData<InfiniteData<CommentListResponse>>(
        ["comments", id],
        (data) => {
          if (!data) return data;
          return {
            ...data,
            pages: data.pages.map((page) => ({
              ...page,
              comments: (page.comments || []).map((c) =>
                c.id === commentId
                  ? {
                      ...c,
                      likeCount: c.liked
                        ? Math.max(0, (c.likeCount ?? 0) - 1)
                        : (c.likeCount ?? 0) + 1,
                      liked: !c.liked,
                    }
                  : c
              ),
            })),
          };
        }
      );
      return { previousData };
    },
    onSuccess: (data, commentId) => {
      queryClient.setQueryData<InfiniteData<CommentListResponse>>(
        ["comments", id],
        (cacheData) => {
          if (!cacheData) return cacheData;
          return {
            ...cacheData,
            pages: cacheData.pages.map((page) => ({
              ...page,
              comments: (page.comments || []).map((c) =>
                c.id === commentId
                  ? { ...c, likeCount: data.likeCount, liked: data.isLiked }
                  : c
              ),
            })),
          };
        }
      );
    },
    onError: (_err, _commentId, context) => {
      if (context?.previousData) {
        queryClient.setQueryData(["comments", id], context.previousData);
      }
    },
  });

  // ── Reply submit ─────────────────────────────────────────────────────────────
  const submitReplyMutation = useMutation<
    Comment,
    ApiError,
    { content: string; commentReplyId: number }
  >({
    mutationFn: (payload) => createComment(idValue, payload),
    onSuccess: async (newComment) => {
      const parentId = newComment.commentReplyId;
      if (parentId) {
        try {
          // Fetch the updated parent so replies array is authoritative from server
          const updatedParent = await getCommentById(parentId);
          queryClient.setQueryData<InfiniteData<CommentListResponse>>(
            ["comments", id],
            (data) => {
              if (!data) return data;
              return {
                ...data,
                pages: data.pages.map((page) => ({
                  ...page,
                  comments: (page.comments || []).map((c) =>
                    c.id === parentId
                      ? { ...c, replies: updatedParent.replies ?? [] }
                      : c
                  ),
                })),
              };
            }
          );
        } catch {
          // Fallback: add locally if server fetch fails
          queryClient.setQueryData<InfiniteData<CommentListResponse>>(
            ["comments", id],
            (data) => {
              if (!data) return data;
              return {
                ...data,
                pages: data.pages.map((page) => ({
                  ...page,
                  comments: (page.comments || []).map((c) =>
                    c.id === parentId
                      ? { ...c, replies: [...(c.replies ?? []), newComment] }
                      : c
                  ),
                })),
              };
            }
          );
        }
      }
      setReplyingToId(null);
      setReplyText("");
    },
  });

  // ── Derived data ─────────────────────────────────────────────────────────────
  const pages = (commentsQuery.data?.pages ?? []) as CommentListResponse[];
  // Only top-level comments — replies are already nested inside parent.replies
  const comments = pages
    .flatMap((page) => page.comments || [])
    .filter((c) => c.commentReplyId == null) as Comment[];
  const lastPage = pages[pages.length - 1];
  const pagination = lastPage?.pagination;

  // ── Handlers ─────────────────────────────────────────────────────────────────
  const handleModalClose = () => {
    setShowLoginModal(false);
    commentInputRef.current?.blur();
  };

  const handleLoadMore = () => {
    if (commentsQuery.hasNextPage) commentsQuery.fetchNextPage();
  };

  const handleLike = (commentId: number) => {
    if (!isAuthenticated) { setShowLoginModal(true); return; }
    likeMutation.mutate(commentId);
  };

  const handleDelete = (commentId: number) => {
    if (!window.confirm("Bạn có chắc muốn xóa bình luận này không?")) return;
    deleteCommentMutation.mutate(commentId);
  };

  const handleReplyToggle = (commentId: number) => {
    if (!isAuthenticated) { setShowLoginModal(true); return; }
    if (replyingToId === commentId) {
      setReplyingToId(null);
      setReplyText("");
    } else {
      setReplyingToId(commentId);
      setReplyText("");
    }
  };

  const handleReplySubmit = (e: FormEvent, parentId: number) => {
    e.preventDefault();
    if (!replyText.trim()) return;
    submitReplyMutation.mutate({ content: replyText.trim(), commentReplyId: parentId });
  };

  const handleSubmitComment = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!isAuthenticated) { setShowLoginModal(true); return; }
    if (!commentText.trim()) return;
    await submitCommentMutation.mutateAsync({ content: commentText.trim() });
  };

  // ── Comment renderer (reused for top-level and replies) ─────────────────────
  const renderComment = (comment: Comment, isReply = false) => (
    <div
      key={comment.id}
      className={isReply ? "ms-4 mt-2" : "comment-item mb-4"}
    >
      <div className="d-flex">
        <div className="comment-avatar me-3 flex-shrink-0">
          <div
            className="bg-secondary text-white rounded-circle d-flex align-items-center justify-content-center"
            style={{
              width: isReply ? "32px" : "40px",
              height: isReply ? "32px" : "40px",
              fontSize: isReply ? "12px" : "14px",
            }}
          >
            {comment.username?.charAt(0)?.toUpperCase() ?? "U"}
          </div>
        </div>

        <div className="comment-content flex-grow-1">
          <Card>
            <Card.Body className={isReply ? "py-2 px-3" : undefined}>
              {/* Header */}
              <div className="d-flex justify-content-between align-items-center mb-2">
                <h6 className="mb-0 fw-semibold">{comment.username ?? "Người dùng"}</h6>
                <div className="d-flex align-items-center gap-2">
                  <small className="text-muted">
                    {comment.createdAt
                      ? new Date(comment.createdAt).toLocaleDateString("vi-VN")
                      : ""}
                  </small>
                  {isAuthenticated && Number(user?.userIdId) === Number(comment.userId) && (
                    <Button
                      variant="link"
                      size="sm"
                      className="text-danger p-0"
                      title="Xóa bình luận"
                      onClick={() => handleDelete(comment.id)}
                      disabled={
                        deleteCommentMutation.isPending &&
                        deleteCommentMutation.variables === comment.id
                      }
                    >
                      {deleteCommentMutation.isPending &&
                      deleteCommentMutation.variables === comment.id ? (
                        <Spinner animation="border" size="sm" />
                      ) : (
                        <FaTrash size={11} />
                      )}
                    </Button>
                  )}
                </div>
              </div>

              {/* Content */}
              <p className="mb-2">{comment.content}</p>

              {/* Actions */}
              <div className="d-flex align-items-center gap-2">
                <Button
                  variant="link"
                  className={`d-flex align-items-center gap-1 p-0 ${
                    comment.liked ? "text-primary" : "text-secondary"
                  }`}
                  onClick={() => handleLike(comment.id)}
                  disabled={
                    likeMutation.isPending && likeMutation.variables === comment.id
                  }
                >
                  <FaThumbsUp size={13} />
                  <span className="small">Thích</span>
                </Button>
                <span className="text-muted small">{comment.likeCount ?? 0}</span>

                {!isReply && (
                  <Button
                    variant="link"
                    className="d-flex align-items-center gap-1 p-0 text-secondary ms-1"
                    onClick={() => handleReplyToggle(comment.id)}
                  >
                    <FaReply size={13} />
                    <span className="small">Trả lời</span>
                  </Button>
                )}
              </div>
            </Card.Body>
          </Card>

          {/* Reply form */}
          {!isReply && replyingToId === comment.id && (
            <div className="mt-2">
              <Form onSubmit={(e) => handleReplySubmit(e, comment.id)}>
                <Form.Control
                  as="textarea"
                  rows={2}
                  placeholder={`Trả lời ${comment.username ?? ""}...`}
                  value={replyText}
                  onChange={(e) => setReplyText(e.target.value)}
                  autoFocus
                  className="mb-2"
                />
                <div className="d-flex gap-2">
                  <Button
                    size="sm"
                    variant="primary"
                    type="submit"
                    disabled={submitReplyMutation.isPending || !replyText.trim()}
                  >
                    {submitReplyMutation.isPending ? (
                      <>
                        <Spinner animation="border" size="sm" className="me-1" />
                        Đang gửi...
                      </>
                    ) : (
                      "Gửi"
                    )}
                  </Button>
                  <Button
                    size="sm"
                    variant="outline-secondary"
                    type="button"
                    onClick={() => { setReplyingToId(null); setReplyText(""); }}
                  >
                    Hủy
                  </Button>
                </div>
                {submitReplyMutation.error && (
                  <div className="alert alert-warning mt-2 mb-0 py-1 small">
                    {submitReplyMutation.error.message ?? "Không thể gửi trả lời."}
                  </div>
                )}
              </Form>
            </div>
          )}

          {/* Nested replies */}
          {!isReply && (comment.replies ?? []).length > 0 && (
            <div className="replies-section">
              {(comment.replies ?? []).map((reply) => renderComment(reply, true))}
            </div>
          )}
        </div>
      </div>
    </div>
  );

  // ── Render ───────────────────────────────────────────────────────────────────
  return (
    <div className="comments-section mt-5">
      <h3 className="mb-4">Ý kiến ({pagination?.totalItems ?? 0})</h3>

      {!COMMENTS_ENABLED && (
        <div className="alert alert-secondary">
          Bình luận đang tạm thời tắt trong môi trường hiện tại.
        </div>
      )}

      {/* New comment form */}
      <Card className="mb-4">
        <Card.Body>
          <Form onSubmit={handleSubmitComment}>
            <Form.Group className="mb-3">
              <Form.Control
                as="textarea"
                rows={3}
                placeholder="Chia sẻ ý kiến của bạn"
                value={commentText}
                onChange={(event) => setCommentText(event.target.value)}
                ref={commentInputRef}
                disabled={!COMMENTS_ENABLED}
              />
            </Form.Group>
            <div className="d-flex justify-content-end">
              <Button
                variant="primary"
                type="submit"
                disabled={
                  !COMMENTS_ENABLED ||
                  submitCommentMutation.isPending ||
                  !commentText.trim()
                }
              >
                {!COMMENTS_ENABLED ? (
                  "Tạm tắt bình luận"
                ) : submitCommentMutation.isPending ? (
                  <>
                    <Spinner animation="border" size="sm" className="me-2" />
                    Đang gửi...
                  </>
                ) : (
                  "Gửi bình luận"
                )}
              </Button>
            </div>
          </Form>
          {submitCommentMutation.error && (
            <div className="alert alert-warning mt-3 mb-0">
              {submitCommentMutation.error.message ?? "Không thể gửi bình luận lúc này."}
            </div>
          )}
        </Card.Body>
      </Card>

      {/* Sort tabs */}
      <div className="comment-tabs mb-4">
        <Button
          variant="link"
          className="text-decoration-none fw-bold text-dark px-0 me-4"
        >
          Quan tâm nhất
        </Button>
        <Button variant="link" className="text-decoration-none text-secondary px-0">
          Mới nhất
        </Button>
        <hr className="mt-2" />
      </div>

      {/* Comment list */}
      {commentsQuery.error ? (
        <div className="alert alert-danger">
          {commentsQuery.error.message ?? "Không thể tải bình luận. Vui lòng thử lại sau."}
        </div>
      ) : comments.length > 0 ? (
        <div className="comments-list">
          {comments.map((comment) => renderComment(comment))}
          {commentsQuery.hasNextPage && (
            <div className="text-center mt-4">
              <Button
                variant="outline-primary"
                onClick={handleLoadMore}
                disabled={commentsQuery.isFetchingNextPage}
              >
                {commentsQuery.isFetchingNextPage ? (
                  <>
                    <Spinner animation="border" size="sm" className="me-2" />
                    Đang tải...
                  </>
                ) : (
                  "Xem thêm bình luận"
                )}
              </Button>
            </div>
          )}
        </div>
      ) : commentsQuery.isLoading ? (
        <div className="text-center py-5">
          <Spinner animation="border" size="sm" className="me-2" />
          Đang tải bình luận...
        </div>
      ) : (
        <div className="text-center py-5">
          <p className="text-muted">Chưa có bình luận nào.</p>
        </div>
      )}

      <ModalLogin show={showLoginModal} onHide={handleModalClose} />
    </div>
  );
};

export default Comments;

