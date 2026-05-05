import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import {
  Alert,
  Button,
  Col,
  Container,
  Image,
  Row,
  Spinner,
} from "react-bootstrap";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import AudioPlayer from "../components/AudioPlayer";
import Comments from "../components/Comments";
import ArticleCarousel from "../components/ArticleCarousel";
import ModalLogin from "../../auth/components/ModalLogin";
import { ArticleChatWidget } from "../components/ArticleChatWidget";
import {
  getArticleDetail,
  getArticleLikeCount,
  getArticleLikeStatus,
  getArticles,
  likeArticle,
  unlikeArticle,
} from "../../../services/articles.service";
import { useAuth } from "../../auth/auth-context";
import type {
  ApiError,
  ArticleDetailResponse,
  ArticleListResponse,
  ArticleLikeCountResponse,
  ArticleLikeStatusResponse,
} from "../../../types";
import "../../../styles/ArticleDetail.css";

const ArticleDetail = () => {
  const { id } = useParams<{ id: string }>();
  const [showLoginModal, setShowLoginModal] = useState(false);
  const { isAuthenticated } = useAuth();
  const queryClient = useQueryClient();

  const idValue = id ?? "";
  const canQuery = Boolean(id);

  const articleQuery = useQuery<ArticleDetailResponse, ApiError>({
    queryKey: ["article", id],
    queryFn: () => getArticleDetail(idValue),
    enabled: canQuery,
  });

  const likeCountQuery = useQuery<ArticleLikeCountResponse, ApiError>({
    queryKey: ["articleLikeCount", id],
    queryFn: () => getArticleLikeCount(idValue),
    enabled: canQuery,
  });

  const likeStatusQuery = useQuery<ArticleLikeStatusResponse, ApiError>({
    queryKey: ["articleLikeStatus", id],
    queryFn: () => getArticleLikeStatus(idValue),
    enabled: Boolean(canQuery && isAuthenticated),
  });

  const categoryId = articleQuery.data?.article?.categoryIdId;
  const hasCategory = typeof categoryId === "number";

  const relatedByCategoryQuery = useQuery<ArticleListResponse, ApiError>({
    queryKey: ["relatedByCategory", categoryId, id],
    queryFn: () =>
      getArticles({
        page: 1,
        categoryId: String(categoryId),
      }),
    enabled: Boolean(canQuery && hasCategory),
  });

  const latestQuery = useQuery<ArticleListResponse, ApiError>({
    queryKey: ["latestArticles", id],
    queryFn: () => getArticles({ page: 1 }),
    enabled: canQuery,
  });

  const toggleLikeMutation = useMutation<
    void,
    ApiError,
    { liked: boolean },
    {
      previousLikeStatus?: ArticleLikeStatusResponse;
      previousLikeCount?: ArticleLikeCountResponse;
    }
  >({
    mutationFn: ({ liked }: { liked: boolean }) =>
      liked ? unlikeArticle(idValue) : likeArticle(idValue),
    onMutate: async ({ liked }) => {
      await queryClient.cancelQueries({
        queryKey: ["articleLikeStatus", id],
      });
      await queryClient.cancelQueries({
        queryKey: ["articleLikeCount", id],
      });

      const previousLikeStatus = queryClient.getQueryData<ArticleLikeStatusResponse>([
        "articleLikeStatus",
        id,
      ]);
      const previousLikeCount = queryClient.getQueryData<ArticleLikeCountResponse>([
        "articleLikeCount",
        id,
      ]);

      const nextLiked = !liked;
      queryClient.setQueryData<ArticleLikeStatusResponse>(["articleLikeStatus", id], {
        ...(previousLikeStatus ?? {}),
        isLiked: nextLiked,
        liked: nextLiked,
      });

      const currentLikeCount = previousLikeCount?.totalLike ?? 0;
      const nextLikeCount = Math.max(0, currentLikeCount + (liked ? -1 : 1));
      queryClient.setQueryData<ArticleLikeCountResponse>(["articleLikeCount", id], {
        totalLike: nextLikeCount,
      });

      return { previousLikeStatus, previousLikeCount };
    },
    onError: (_error, _variables, context) => {
      if (context?.previousLikeStatus) {
        queryClient.setQueryData(["articleLikeStatus", id], context.previousLikeStatus);
      }
      if (context?.previousLikeCount) {
        queryClient.setQueryData(["articleLikeCount", id], context.previousLikeCount);
      }
    },
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: ["articleLikeCount", id],
      });
      queryClient.invalidateQueries({
        queryKey: ["articleLikeStatus", id],
      });
    },
  });

  useEffect(() => {
    window.scrollTo(0, 0);
  }, [id]);

  const liked =
    likeStatusQuery.data?.isLiked ?? likeStatusQuery.data?.liked ?? false;

  const handleLikeArticle = async () => {
    if (!isAuthenticated) {
      setShowLoginModal(true);
      return;
    }

    if (!id) {
      return;
    }

    await toggleLikeMutation.mutateAsync({ liked });
  };

  if (articleQuery.isLoading) {
    return (
      <Container className="d-flex justify-content-center my-5">
        <Spinner animation="border" />
      </Container>
    );
  }

  if (articleQuery.error) {
    return (
      <Container className="my-5">
        <Alert variant="danger">
          {articleQuery.error.message ||
            "Không thể tải thông tin bài viết. Vui lòng thử lại sau."}
        </Alert>
      </Container>
    );
  }

  const article = articleQuery.data?.article;
  const blocks = articleQuery.data?.blocks || [];
  const totalLike = likeCountQuery.data?.totalLike || 0;
  if (!article) {
    return (
      <Container className="my-5">
        <Alert variant="info">Không tìm thấy bài viết.</Alert>
      </Container>
    );
  }

  const getPublishedTime = (date?: string | null) =>
    date ? new Date(date).getTime() : 0;

  const relatedByCategory = (relatedByCategoryQuery.data?.articles ?? [])
    .filter((item) => item.id !== article.id)
    .sort(
      (left, right) =>
        getPublishedTime(right.publishedDate) -
        getPublishedTime(left.publishedDate)
    )
    .slice(0, 10);

  const relatedIds = new Set(relatedByCategory.map((item) => item.id));

  const latestRecommendations = (latestQuery.data?.articles ?? [])
    .filter(
      (item) => item.id !== article.id && !relatedIds.has(item.id)
    )
    .sort(
      (left, right) =>
        getPublishedTime(right.publishedDate) -
        getPublishedTime(left.publishedDate)
    )
    .slice(0, 10);

  return (
    <Container className="my-5 article-detail">
      <Row className="justify-content-center">
        <Col md={6}>
          <h1 className="mb-4">{article.title}</h1>
          <div className="article-meta mb-3">
            <p>
              <strong>Nguồn: </strong>Báo {article.generatorIdName}
            </p>
            <p>
              <strong>Ngày xuất bản:</strong>{" "}
              {new Date(article.publishedDate).toLocaleDateString("vi-VN")}
            </p>
            <p>
              <strong>Lượt thích: </strong> {totalLike}
            </p>
            <Button
              variant={liked ? "primary" : "outline-primary"}
              onClick={handleLikeArticle}
              disabled={toggleLikeMutation.isPending}
            >
              {liked ? "Đã thích" : "Thích"}
            </Button>
          </div>

          <div className="article-meta mb-3">
            <p>
              <strong>Thể loại: </strong> {article.categoryIdName}
            </p>
            <p>
              <strong>Bài viết gốc: </strong>
              <a
                href={article.originalUrl}
                target="_blank"
                rel="noopener noreferrer"
              >
                Xem tại đây
              </a>
            </p>
          </div>

          {article.audioUrl && (
            <AudioPlayer
              audioUrl={article.audioUrl}
              title={`Nghe: ${article.title}`}
            />
          )}

          {article.videoUrl && article.isVideoAccepted && (
            <div className="mb-4">
              <p className="fw-semibold mb-2">📹 Video bài viết</p>
              <video
                src={article.videoUrl}
                controls
                style={{ width: "100%", borderRadius: "8px", background: "#000" }}
              />
            </div>
          )}

          {article.topImageUrl && (
            <div className="mb-4">
              <Image
                src={article.topImageUrl}
                fluid
                className="w-100"
                style={{ maxHeight: "500px", objectFit: "cover" }}
                referrerPolicy="no-referrer"
              />
            </div>
          )}

          {article.summary && (
            <div className="article-summary-box mb-4">
              <span className="article-summary-label">Tóm tắt nhanh</span>
              <p className="article-summary-text">{article.summary}</p>
            </div>
          )}

          <div className="article-content">
            {blocks.map((block, index) => {
              switch (block.type) {
                case "text":
                case "paragraph":
                  return <p key={index}>{block.content}</p>;
                case "heading":
                  return block.tag === "h2" ? (
                    <h2 key={index}>{block.text}</h2>
                  ) : (
                    <h3 key={index}>{block.text}</h3>
                  );
                case "image":
                  return (
                    <div key={index} className="my-4">
                      <Image src={block.src} fluid referrerPolicy="no-referrer" />
                      {block.caption && (
                        <p className="text-center text-muted mt-2">
                          {block.caption}
                        </p>
                      )}
                    </div>
                  );
                default:
                  return null;
              }
            })}
          </div>

          <Comments id={id} />
          <div className="article-recommendations">
            <ArticleCarousel
              eyebrow="Liên quan"
              title="Tin bài cùng danh mục"
              subtitle="Các bài viết mới nhất trong cùng chuyên mục."
              articles={relatedByCategory}
              emptyMessage={
                relatedByCategoryQuery.isLoading
                  ? "Đang tải bài viết liên quan..."
                  : "Chưa có bài viết liên quan."
              }
            />
            <ArticleCarousel
              eyebrow="Gợi ý"
              title="Bạn có thể muốn xem"
              subtitle="Tuyển chọn các bài báo mới nhất vừa lên sóng."
              articles={latestRecommendations}
              emptyMessage={
                latestQuery.isLoading
                  ? "Đang tải tin mới nhất..."
                  : "Chưa có tin mới nhất."
              }
            />
          </div>
        </Col>
      </Row>
      <ModalLogin show={showLoginModal} onHide={() => setShowLoginModal(false)} />
      {/* Floating article-contextual AI chat widget */}
      <ArticleChatWidget key={String(article.id)} articleId={String(article.id)} articleTitle={article.title} />
    </Container>
  );
};

export default ArticleDetail;
