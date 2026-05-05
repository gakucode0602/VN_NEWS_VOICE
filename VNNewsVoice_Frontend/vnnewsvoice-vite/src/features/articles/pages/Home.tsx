import { useMemo } from "react";
import { Button, Container } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { useSearchContext } from "../../../contexts/useSearchContext";
import { getArticles, type ArticleListParams } from "../../../services/articles.service";
import LatestHighlights from "../components/LatestHighlights";
import ArticleStreamList from "../components/ArticleStreamList";
import type { ApiError, ArticleListResponse } from "../../../types";
import "../../../styles/NewsOverview.css";

const Home = () => {
  const navigate = useNavigate();

  const { searchTerm, selectedCategory, selectedGenerator } = useSearchContext();

  const params = useMemo(() => {
    const nextParams: ArticleListParams = { page: 1 };

    if (searchTerm) {
      nextParams.name = searchTerm;
    }

    if (selectedCategory) {
      nextParams.categoryId = selectedCategory;
    }

    if (selectedGenerator) {
      nextParams.generatorId = selectedGenerator;
    }

    return nextParams;
  }, [searchTerm, selectedCategory, selectedGenerator]);

  const {
    data,
    isLoading,
    isFetching,
    error,
  } = useQuery<ArticleListResponse, ApiError>({
    queryKey: [
      "articles",
      "overview",
      searchTerm,
      selectedCategory,
      selectedGenerator,
    ],
    queryFn: () => getArticles(params),
    placeholderData: keepPreviousData,
  });

  const sortedArticles = useMemo(() => {
    const articles = data?.articles ?? [];
    return [...articles].sort((left, right) => {
      const leftTime = left.publishedDate
        ? new Date(left.publishedDate).getTime()
        : 0;
      const rightTime = right.publishedDate
        ? new Date(right.publishedDate).getTime()
        : 0;
      return rightTime - leftTime;
    });
  }, [data?.articles]);

  const highlightArticles = sortedArticles.slice(0, 4);
  const streamArticles = sortedArticles.slice(4);

  const handleArticleClick = (article) => {
    if (article?.id) {
      navigate(`/articles/${article.id}`);
    }
  };

  return (
    <div className="news-overview">
      <Container>
        {error && (
          <div className="alert alert-danger text-center mb-4" role="alert">
            <i className="bi bi-exclamation-triangle-fill me-2"></i>
            {error.message ||
              "Không thể kết nối đến máy chủ. Vui lòng thử lại sau."}
          </div>
        )}

        {isLoading ? (
          <div className="text-center py-5">
            <div className="spinner-border text-primary" role="status">
              <span className="visually-hidden">Loading...</span>
            </div>
            <p className="mt-3">Đang tải bài viết...</p>
          </div>
        ) : (
          <>
            <LatestHighlights
              articles={highlightArticles}
              onArticleClick={handleArticleClick}
            />

            <section className="news-stream">
              <div className="news-stream-header">
                <div>
                  <span className="section-eyebrow">Dòng thời gian</span>
                  <h3 className="news-stream-title">
                    Danh sách bài viết mới theo thời gian
                  </h3>
                </div>
                <p className="news-stream-desc">
                  Lướt nhanh những bài viết được cập nhật gần nhất.
                </p>
              </div>

              <ArticleStreamList
                articles={streamArticles}
                onArticleClick={handleArticleClick}
                emptyMessage="Chưa có thêm bài viết để hiển thị."
              />

              <div className="latest-cta">
                <Button
                  className="latest-button"
                  onClick={() => navigate("/latest")}
                >
                  Xem tin tức mới nhất
                </Button>
              </div>
            </section>
          </>
        )}

        {isFetching && !isLoading ? (
          <div className="text-center mt-3 text-muted">Đang cập nhật...</div>
        ) : null}
      </Container>
    </div>
  );
};

export default Home;
