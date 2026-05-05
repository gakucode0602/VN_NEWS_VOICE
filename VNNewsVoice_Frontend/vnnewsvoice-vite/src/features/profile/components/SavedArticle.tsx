import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Card, Col, Pagination, Row } from "react-bootstrap";
import { useQuery } from "@tanstack/react-query";
import { getPersonalArticleLikes } from "../../../services/profile.service";
import type { ApiError, ArticleLike, ArticleLikeListResponse } from "../../../types";

const SavedArticles = () => {
  const [currentPage, setCurrentPage] = useState(1);
  const navigate = useNavigate();

  const likedQuery = useQuery<ArticleLikeListResponse, ApiError>({
    queryKey: ["profile-liked-articles", currentPage],
    queryFn: () =>
      getPersonalArticleLikes({ page: currentPage < 1 ? 1 : currentPage }),
  });

  const likedArticles = (likedQuery.data?.articleLikes || []) as ArticleLike[];
  const pagination = likedQuery.data?.pagination;

  const handleArticleClick = (
    articleId?: string | null
  ) => {
    if (articleId) {
      navigate(`/articles/${articleId}`);
    }
  };

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  const formatDate = (dateString?: string | null) => {
    try {
      if (!dateString) return "";
      const date = new Date(dateString);
      return new Intl.DateTimeFormat("vi-VN", {
        year: "numeric",
        month: "long",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      }).format(date);
    } catch {
      return dateString || "";
    }
  };

  const renderPagination = () => {
    if (!pagination || !pagination.totalPages) {
      return null;
    }

    const items = Array.from({ length: pagination.totalPages }, (_, index) => {
      const pageNumber = index + 1;
      return (
        <Pagination.Item
          key={pageNumber}
          active={pageNumber === currentPage}
          onClick={() => handlePageChange(pageNumber)}
        >
          {pageNumber}
        </Pagination.Item>
      );
    });

    return (
      <Pagination>
        <Pagination.Prev
          disabled={currentPage === 1}
          onClick={() => handlePageChange(currentPage - 1)}
        />
        {items}
        <Pagination.Next
          disabled={currentPage === pagination.totalPages}
          onClick={() => handlePageChange(currentPage + 1)}
        />
      </Pagination>
    );
  };

  return (
    <div className="general-info-section">
      <h2>Bài viết đã lưu</h2>
      {likedQuery.error && (
        <div className="alert alert-danger text-center mb-4">
          <i className="bi bi-exclamation-triangle-fill me-2"></i>
          {likedQuery.error.message}
        </div>
      )}

      {likedQuery.isLoading ? (
        <div className="spinner-border" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      ) : (
        <>
          {likedArticles.length > 0 ? (
            <Row>
              {likedArticles.map((item) => (
                <Col md={12} key={item.id} className="mb-3">
                  <Card className="shadow-sm h-100">
                    <Card.Body>
                      <div className="d-flex justify-content-between align-items-start">
                        <div>
                          <Card.Title
                            className="mb-2 article-title"
                            style={{ cursor: "pointer" }}
                            onClick={() => handleArticleClick(item.articleIdId)}
                          >
                            {item.articleIdTitle}
                          </Card.Title>
                          <Card.Subtitle className="mb-3 text-muted">
                            <small>{formatDate(item.createdAt)}</small>
                          </Card.Subtitle>
                        </div>
                      </div>
                    </Card.Body>
                  </Card>
                </Col>
              ))}
            </Row>
          ) : (
            <div className="text-center py-5">
              <i className="bi bi-chat-square-text fs-1 text-muted"></i>
              <p className="mt-3">Chưa có bài viết nào được lưu.</p>
            </div>
          )}
          {renderPagination()}
        </>
      )}
    </div>
  );
};

export default SavedArticles;
