/* eslint-disable react-hooks/set-state-in-effect */
import { useEffect, useMemo, useState } from "react";
import {
  Alert,
  Button,
  Card,
  Col,
  Container,
  Form,
  Pagination,
  Row,
} from "react-bootstrap";
import { useNavigate } from "react-router-dom";
import { useQuery, keepPreviousData } from "@tanstack/react-query";
import { useSearchContext } from "../../../contexts/useSearchContext";
import { getArticles, type ArticleListParams } from "../../../services/articles.service";
import { getCategories } from "../../../services/categories.service";
import { getGenerators } from "../../../services/generators.service";
import MySpinner from "../../../components/layouts/MySpinner";
import type {
  ApiError,
  ArticleListResponse,
  Category,
  Generator,
} from "../../../types";

const SearchArticle = () => {
  const {
    searchTerm,
    setSearchTerm,
    selectedCategory,
    setSelectedCategory,
    selectedGenerator,
    setSelectedGenerator,
  } = useSearchContext();

  const [searchInput, setSearchInput] = useState("");
  const [activeSearchTerm, setActiveSearchTerm] = useState("");
  const [page, setCurrentPage] = useState(1);
  const [publishedDates, setPublishedDates] = useState<number | null>(null);
  const [fromDate, setFromDate] = useState("");
  const [toDate, setToDate] = useState("");
  const navigate = useNavigate();

  useEffect(() => {
    if (searchTerm) {
      setSearchInput(searchTerm);
      setActiveSearchTerm(searchTerm);
      setSearchTerm("");
      setCurrentPage(1);
    }
  }, [searchTerm, setSearchTerm]);

  useEffect(() => {
    setCurrentPage(1);
  }, [selectedCategory, selectedGenerator, publishedDates, fromDate, toDate]);

  const { data: categories = [] } = useQuery<Category[], ApiError>({
    queryKey: ["categories"],
    queryFn: () => getCategories(),
  });

  const { data: generators = [] } = useQuery<Generator[], ApiError>({
    queryKey: ["generators"],
    queryFn: () => getGenerators(),
  });

  const params = useMemo(() => {
    const nextParams: ArticleListParams = { page };

    if (activeSearchTerm) {
      nextParams.name = activeSearchTerm;
    }

    if (selectedCategory) {
      nextParams.categoryId = selectedCategory;
    }

    if (selectedGenerator) {
      nextParams.generatorId = selectedGenerator;
    }

    if (fromDate && toDate) {
      nextParams.fromDate = fromDate;
      nextParams.toDate = toDate;
    } else if (publishedDates !== null) {
      nextParams.publishedDates = publishedDates;
    }

    return nextParams;
  }, [activeSearchTerm, page, selectedCategory, selectedGenerator, publishedDates, fromDate, toDate]);

  const {
    data,
    isLoading,
    error,
  } = useQuery<ArticleListResponse, ApiError>({
    queryKey: [
      "articles",
      "search",
      page,
      activeSearchTerm,
      selectedCategory,
      selectedGenerator,
      publishedDates,
      fromDate,
      toDate,
    ],
    queryFn: () => getArticles(params),
    placeholderData: keepPreviousData,
  });

  const articles = data?.articles || [];
  const pagination = data?.pagination;

  const handleArticleClick = (article) => {
    if (article?.id) {
      navigate(`/articles/${article.id}`);
    }
  };

  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
  };

  const renderPagination = () => {
    if (!pagination || !pagination.totalPages) return null;

    const items = Array.from({ length: pagination.totalPages }, (_, index) => {
      const pageNumber = index + 1;
      return (
        <Pagination.Item
          key={pageNumber}
          active={pageNumber === page}
          onClick={pageNumber === page ? null : () => handlePageChange(pageNumber)}
        >
          {pageNumber}
        </Pagination.Item>
      );
    });

    return (
      <Pagination className="justify-content-center">
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

  const handleSubmit = (event) => {
    event.preventDefault();
    const term = searchInput.trim();
    setCurrentPage(1);
    setActiveSearchTerm(term);
  };

  return (
    <Container className="py-4">
      <h2 className="mb-4">Kết quả tìm kiếm</h2>

      <Form className="d-flex" onSubmit={handleSubmit}>
        <Form.Control
          type="search"
          placeholder="Tìm kiếm bài viết..."
          className="me-2"
          aria-label="Search"
          value={searchInput}
          onChange={(event) => setSearchInput(event.target.value)}
        />
        <Button variant="outline-success" type="submit">
          <i className="bi bi-search me-1"></i>
        </Button>
      </Form>

      <div className="mb-4">
        <Form.Group className="mb-4">
          <Form.Label>Chọn nguồn</Form.Label>
          <Form.Select
            value={selectedGenerator}
            onChange={(event) => {
              setSelectedGenerator(event.target.value);
              setCurrentPage(1);
            }}
          >
            <option value="">Tất cả nguồn</option>
            {generators.map((generator) => (
              <option key={generator.id} value={String(generator.id)}>
                {generator.name}
              </option>
            ))}
          </Form.Select>
        </Form.Group>

        <Form.Group className="mb-4">
          <Form.Label>Chọn danh mục</Form.Label>
          <Form.Select
            value={selectedCategory}
            onChange={(event) => {
              setSelectedCategory(event.target.value);
              setCurrentPage(1);
            }}
          >
            <option value="">Tất cả danh mục</option>
            {categories.map((category) => (
              <option key={category.id} value={String(category.id)}>
                {category.name}
              </option>
            ))}
          </Form.Select>
        </Form.Group>

        <Form.Group className="mb-3">
          <Form.Label>Lọc theo thời gian</Form.Label>
          <div className="d-flex flex-wrap gap-2 mb-3">
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
                  publishedDates === preset.value && !fromDate && !toDate
                    ? "primary"
                    : "outline-secondary"
                }
                onClick={() => {
                  setPublishedDates(preset.value);
                  setFromDate("");
                  setToDate("");
                }}
              >
                {preset.label}
              </Button>
            ))}
          </div>
          <Row className="g-2">
            <Col xs={12} sm={6}>
              <Form.Label className="small text-muted">Từ ngày</Form.Label>
              <Form.Control
                type="date"
                value={fromDate}
                onChange={(event) => {
                  setFromDate(event.target.value);
                  setPublishedDates(null);
                }}
              />
            </Col>
            <Col xs={12} sm={6}>
              <Form.Label className="small text-muted">Đến ngày</Form.Label>
              <Form.Control
                type="date"
                value={toDate}
                onChange={(event) => {
                  setToDate(event.target.value);
                  setPublishedDates(null);
                }}
              />
            </Col>
          </Row>
        </Form.Group>

        {error && (
          <Alert variant="danger" className="mt-4">
            {error.message ||
              "Không thể kết nối đến máy chủ. Vui lòng thử lại sau."}
          </Alert>
        )}

        {isLoading ? (
          <MySpinner />
        ) : (
          <Row xs={1} md={2} lg={3} className="g-4">
            {articles.length > 0 ? (
              articles.map((article) => (
                <Col key={article.id}>
                  <Card
                    className="h-100 shadow-sm"
                    onClick={() => handleArticleClick(article)}
                    style={{ cursor: "pointer" }}
                  >
                    <div
                      className="card-img-top d-flex align-items-center justify-content-center bg-light"
                      style={{ height: "180px" }}
                    >
                      {article.topImageUrl ? (
                        <img
                          src={article.topImageUrl}
                          alt={article.title}
                          className="img-fluid"
                          style={{
                            maxHeight: "180px",
                            objectFit: "cover",
                            width: "100%",
                          }}
                        />
                      ) : (
                        <i
                          className="bi bi-newspaper text-primary"
                          style={{ fontSize: "3rem" }}
                        ></i>
                      )}
                    </div>
                    <Card.Body>
                      <Card.Title>{article.title}</Card.Title>
                      {article.author && (
                        <Card.Subtitle className="mb-2 text-muted">
                          By {article.author}
                        </Card.Subtitle>
                      )}
                      <Card.Text>
                        {article.summary
                          ? article.summary.length > 100
                            ? `${article.summary.substring(0, 100)}...`
                            : article.summary
                          : "No summary available"}
                      </Card.Text>
                    </Card.Body>
                    <Card.Footer className="bg-white">
                      <div className="d-flex justify-content-between align-items-center">
                        <small className="text-muted">
                          {article.publishedDate
                            ? new Date(article.publishedDate).toLocaleDateString()
                            : "Unknown date"}
                        </small>
                      </div>
                    </Card.Footer>
                  </Card>
                </Col>
              ))
            ) : (
              <Col className="text-center">
                <p>Không có bài viết nào phù hợp với tìm kiếm của bạn</p>
              </Col>
            )}
          </Row>
        )}

        {renderPagination()}
      </div>
    </Container>
  );
};

export default SearchArticle;
