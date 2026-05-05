/* eslint-disable react-hooks/set-state-in-effect */
import { useEffect, useMemo, useState } from "react";
import { Button, Container, Pagination } from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { useSearchContext } from "../../../contexts/useSearchContext";
import { getArticles, type ArticleListParams } from "../../../services/articles.service";
import ArticleStreamList from "../components/ArticleStreamList";
import type { ApiError, ArticleListResponse } from "../../../types";
import "../../../styles/NewsOverview.css";

const LatestNews = () => {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const [publishedDates, setPublishedDates] = useState<number | null>(null);

  const { searchTerm, selectedCategory, selectedGenerator } = useSearchContext();

  useEffect(() => {
    setPage(1);
  }, [searchTerm, selectedCategory, selectedGenerator, publishedDates]);

  const params = useMemo(() => {
    const nextParams: ArticleListParams = { page };

    if (searchTerm) {
      nextParams.name = searchTerm;
    }

    if (selectedCategory) {
      nextParams.categoryId = selectedCategory;
    }

    if (selectedGenerator) {
      nextParams.generatorId = selectedGenerator;
    }

    if (publishedDates !== null) {
      nextParams.publishedDates = publishedDates;
    }

    return nextParams;
  }, [page, searchTerm, selectedCategory, selectedGenerator, publishedDates]);

  const {
    data,
    isLoading,
    isFetching,
    error,
  } = useQuery<ArticleListResponse, ApiError>({
    queryKey: [
      "articles",
      "latest",
      page,
      searchTerm,
      selectedCategory,
      selectedGenerator,
      publishedDates,
    ],
    queryFn: () => getArticles(params),
    placeholderData: keepPreviousData,
  });

  const pagination = data?.pagination;

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

  const handleArticleClick = (article) => {
    if (article?.id) {
      navigate(`/articles/${article.id}`);
    }
  };

  const handlePageChange = (nextPage: number) => {
    setPage(nextPage);
  };

  const renderPagination = () => {
    if (!pagination || !pagination.totalPages) return null;

    const items = Array.from(
      { length: pagination.totalPages },
      (_, index) => {
        const pageNumber = index + 1;
        return (
          <Pagination.Item
            key={pageNumber}
            active={pageNumber === page}
            onClick={() => handlePageChange(pageNumber)}
          >
            {pageNumber}
          </Pagination.Item>
        );
      }
    );

    return (
      <Pagination className="justify-content-center latest-pagination">
        <Pagination.Prev
          disabled={page === 1}
          onClick={() => handlePageChange(page - 1)}
        />
        {items}
        <Pagination.Next
          disabled={page === pagination.totalPages}
          onClick={() => handlePageChange(page + 1)}
        />
      </Pagination>
    );
  };

  return (
    <div className="news-overview">
      <Container>
        <div className="latest-page-header">
          <div>
            <span className="section-eyebrow">Tổng quan</span>
            <h2 className="latest-page-title">Danh sách bài báo mới nhất</h2>
          </div>
          <p className="latest-page-subtitle">
            Cập nhật liên tục.
          </p>
        </div>

        <div className="d-flex flex-wrap gap-2 mb-4">
          {[
            { label: "Tất cả", value: null },
            { label: "Hôm nay", value: 1 },
            { label: "7 ngày qua", value: 7 },
            { label: "30 ngày qua", value: 30 },
            { label: "90 ngày qua", value: 90 },
          ].map((preset) => (
            <Button
              key={String(preset.value)}
              size="sm"
              variant={
                publishedDates === preset.value
                  ? "primary"
                  : "outline-secondary"
              }
              onClick={() => setPublishedDates(preset.value)}
            >
              {preset.label}
            </Button>
          ))}
        </div>

        {error && (
          <div className="alert alert-danger text-center mb-4" role="alert">
            <i className="bi bi-exclamation-triangle-fill me-2"></i>
            {error.message ||
              "Không thể kết nối đến máy chủ. Vui lòng thử lại sau."}
          </div>
        )}

        <section className="news-stream">
          {isLoading ? (
            <div className="text-center py-5">
              <div className="spinner-border text-primary" role="status">
                <span className="visually-hidden">Loading...</span>
              </div>
              <p className="mt-3">Đang tải bài viết...</p>
            </div>
          ) : (
            <ArticleStreamList
              articles={sortedArticles}
              onArticleClick={handleArticleClick}
              emptyMessage="Chưa có bài viết nào được cập nhật."
            />
          )}

          {isFetching && !isLoading ? (
            <div className="text-center mt-3 text-muted">Đang cập nhật...</div>
          ) : null}

          {renderPagination()}
        </section>
      </Container>
    </div>
  );
};

export default LatestNews;
