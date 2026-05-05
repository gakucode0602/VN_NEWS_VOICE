import { useRef } from "react";
import { Link } from "react-router-dom";
import type { Article } from "../../../types";
import "../../../styles/ArticleCarousel.css";

type ArticleCarouselProps = {
  title: string;
  subtitle?: string;
  eyebrow?: string;
  articles: Article[];
  emptyMessage?: string;
};

const ArticleCarousel = ({
  title,
  subtitle,
  eyebrow = "Gợi ý",
  articles,
  emptyMessage = "Chưa có bài viết để hiển thị.",
}: ArticleCarouselProps) => {
  const trackRef = useRef<HTMLDivElement | null>(null);

  const handleScroll = (direction: "prev" | "next") => {
    if (!trackRef.current) return;
    const scrollAmount = trackRef.current.clientWidth * 0.85;
    trackRef.current.scrollBy({
      left: direction === "next" ? scrollAmount : -scrollAmount,
      behavior: "smooth",
    });
  };

  return (
    <section className="article-carousel">
      <div className="carousel-header">
        <div className="carousel-heading">
          <span className="carousel-eyebrow">{eyebrow}</span>
          <h3 className="carousel-title">{title}</h3>
          {subtitle && <p className="carousel-subtitle">{subtitle}</p>}
        </div>
        <div className="carousel-actions">
          <button
            type="button"
            className="carousel-button"
            onClick={() => handleScroll("prev")}
            aria-label="Trượt sang trái"
          >
            <i className="bi bi-arrow-left"></i>
          </button>
          <button
            type="button"
            className="carousel-button"
            onClick={() => handleScroll("next")}
            aria-label="Trượt sang phải"
          >
            <i className="bi bi-arrow-right"></i>
          </button>
        </div>
      </div>

      {articles.length === 0 ? (
        <div className="carousel-empty">{emptyMessage}</div>
      ) : (
        <div className="carousel-track" ref={trackRef}>
          {articles.map((article) => {
            const publishedDate = article.publishedDate
              ? new Date(article.publishedDate).toLocaleDateString("vi-VN")
              : "Chưa cập nhật";
            const articlePath = `/articles/${article.id}`;

            return (
              <Link
                key={article.id}
                to={articlePath}
                className="carousel-card"
              >
                <div className="carousel-media">
                  {article.topImageUrl ? (
                    <img src={article.topImageUrl} alt={article.title} referrerPolicy="no-referrer" />
                  ) : (
                    <div className="carousel-placeholder">
                      <i className="bi bi-newspaper"></i>
                    </div>
                  )}
                </div>
                <div className="carousel-body">
                  <div className="carousel-meta">
                    <span className="carousel-source">
                      {article.generatorIdName
                        ? `Báo ${article.generatorIdName}`
                        : "Nguồn cập nhật"}
                    </span>
                    <span className="carousel-date">{publishedDate}</span>
                  </div>
                  <h4 className="carousel-card-title">{article.title}</h4>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </section>
  );
};

export default ArticleCarousel;
