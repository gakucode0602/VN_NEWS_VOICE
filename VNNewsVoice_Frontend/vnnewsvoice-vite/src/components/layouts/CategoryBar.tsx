import { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import Container from "react-bootstrap/Container";
import Dropdown from "react-bootstrap/Dropdown";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useSearchContext } from "../../contexts/useSearchContext";
import { getCategories } from "../../services/categories.service";
import { getGenerators } from "../../services/generators.service";
import type { Category, Generator } from "../../types";
import "../../styles/CategoryBar.css";

const CategoryBar = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    selectedCategory,
    setSelectedCategory,
    selectedGenerator,
    setSelectedGenerator,
  } = useSearchContext();

  const { data: categories = [] } = useQuery<Category[]>({
    queryKey: ["categories"],
    queryFn: () => getCategories(),
  });

  useEffect(() => {
    if (!selectedCategory) {
      return;
    }

    const categoryStillVisible = categories.some(
      (category) => String(category.id) === selectedCategory
    );

    if (!categoryStillVisible) {
      setSelectedCategory("");
    }
  }, [categories, selectedCategory, setSelectedCategory]);

  const { data: generators = [] } = useQuery<Generator[]>({
    queryKey: ["generators"],
    queryFn: () => getGenerators(),
  });

  const selectedGeneratorName = generators.find(
    (generator) => String(generator.id) === selectedGenerator
  )?.name;

  const basePath = location.pathname === "/latest" ? "/latest" : "/";

  const handleCategoryChange = (nextId: string) => {
    setSelectedCategory(nextId);
    navigate(basePath);
  };

  const handleGeneratorChange = (nextId: string) => {
    setSelectedGenerator(nextId);
    navigate(basePath);
  };

  return (
    <div className="category-bar">
      <Container>
        <div className="category-bar-inner">
          <div className="category-home">
            <Link to="/" className="category-home-link">
              <i className="bi bi-house-door-fill"></i>
              <span>Trang chủ</span>
            </Link>
            <Link to="/chat" className="category-home-link category-chat-link">
              <i className="bi bi-chat-dots-fill"></i>
              <span>AI Chat</span>
            </Link>
          </div>
          <div className="category-list" role="list">
            <button
              type="button"
              className={`category-chip ${
                selectedCategory === "" ? "active" : ""
              }`}
              onClick={() => handleCategoryChange("")}
            >
              Tất cả
            </button>
            {categories.map((category) => (
              <button
                key={category.id}
                type="button"
                className={`category-chip ${
                  selectedCategory === String(category.id) ? "active" : ""
                }`}
                onClick={() => handleCategoryChange(String(category.id))}
              >
                {category.name}
              </button>
            ))}
          </div>
          <div className="category-source">
            <Dropdown align="end" className="source-dropdown">
              <Dropdown.Toggle variant="light" className="source-toggle">
                <span className="source-label">Nguồn</span>
                <span className="source-value">
                  {selectedGeneratorName || "Tất cả"}
                </span>
                <i className="bi bi-chevron-down"></i>
              </Dropdown.Toggle>
              <Dropdown.Menu className="source-menu">
                <Dropdown.Item
                  key="all"
                  onClick={() => handleGeneratorChange("")}
                  active={selectedGenerator === ""}
                >
                  Tất cả nguồn
                </Dropdown.Item>
                {generators.map((generator) => (
                  <Dropdown.Item
                    key={generator.id}
                    onClick={() => handleGeneratorChange(String(generator.id))}
                    active={selectedGenerator === String(generator.id)}
                  >
                    {generator.name}
                  </Dropdown.Item>
                ))}
              </Dropdown.Menu>
            </Dropdown>
          </div>
        </div>
      </Container>
    </div>
  );
};

export default CategoryBar;
