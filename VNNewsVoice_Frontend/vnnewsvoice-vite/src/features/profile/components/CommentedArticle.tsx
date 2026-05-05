import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Pagination, Row, Col, Card, Badge } from "react-bootstrap";
import { useQuery } from "@tanstack/react-query";
import { getPersonalComments } from "../../../services/profile.service";
import type { ApiError, Comment, CommentListResponse } from "../../../types";

const CommentedArticles = () => {
  const [currentPage, setCurrentPage] = useState(1);
  const navigate = useNavigate();

  const commentsQuery = useQuery<CommentListResponse, ApiError>({
    queryKey: ["profile-comments", currentPage],
    queryFn: () => getPersonalComments({ page: currentPage }),
  });

  const comments = (commentsQuery.data?.comments || []) as Comment[];
  const pagination = commentsQuery.data?.pagination;

  const handleArticleClick = (articleId?: string | null) => {
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
    if (!pagination || !pagination.totalPages) return null;

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
      <Pagination className="justify-content-center mt-4">
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
      <h2>Bài viết đã bình luận</h2>

      {commentsQuery.error && (
        <div className="alert alert-danger text-center mb-4">
          <i className="bi bi-exclamation-triangle-fill me-2"></i>
          {commentsQuery.error.message ||
            "Không thể tải danh sách bài viết đã bình luận."}
        </div>
      )}

      {commentsQuery.isLoading ? (
        <div className="text-center py-5">
          <div className="spinner-border text-primary" role="status">
            <span className="visually-hidden">Loading...</span>
          </div>
          <p className="mt-3">Đang tải bài viết...</p>
        </div>
      ) : (
        <>
          {comments.length > 0 ? (
            <Row>
              {comments.map((comment) => (
                <Col md={12} key={comment.id} className="mb-3">
                  <Card className="shadow-sm h-100">
                    <Card.Body>
                      <div className="d-flex justify-content-between align-items-start">
                        <div>
                          <Card.Title
                            className="mb-2 article-title"
                            style={{ cursor: "pointer" }}
                            onClick={() => handleArticleClick(comment.articleId)}
                          >
                            {comment.articleTitle}
                          </Card.Title>
                          <Card.Subtitle className="mb-3 text-muted">
                            <small>Bình luận vào {formatDate(comment.createdAt)}</small>
                          </Card.Subtitle>
                        </div>
                        <Badge bg="info" className="ms-2">
                          <i className="bi bi-hand-thumbs-up me-1"></i>
                          {comment.likeCount}
                        </Badge>
                      </div>
                      <Card.Text className="border-top pt-2">
                        <i className="bi bi-chat-quote me-2"></i>
                        {comment.content}
                      </Card.Text>
                    </Card.Body>
                  </Card>
                </Col>
              ))}
            </Row>
          ) : (
            <div className="text-center py-5">
              <i className="bi bi-chat-square-text fs-1 text-muted"></i>
              <p className="mt-3">Bạn chưa bình luận bài viết nào.</p>
            </div>
          )}
          {renderPagination()}
        </>
      )}
    </div>
  );
};

export default CommentedArticles;
