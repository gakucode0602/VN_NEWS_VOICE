import type { Article } from "../../../types";

type LatestHighlightsProps = {
  articles: Article[];
  onArticleClick: (article: Article) => void;
};

const LatestHighlights = ({
  articles,
  onArticleClick,
}: LatestHighlightsProps) => {
  const visibleArticles = articles.slice(0, 4);

  if (visibleArticles.length === 0) {
    return (
      <section className="latest-highlights">
        <div className="section-header">
          <div>
            <span className="section-eyebrow">Tin mới</span>
            <h2 className="section-title">Chưa có bài viết mới</h2>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="latest-highlights">
      <div className="section-header">
        <div>
          <span className="section-eyebrow">Tin mới nhất</span>
          <h2 className="section-title">4 bài báo vừa lên sóng</h2>
        </div>
        <p className="section-caption">
          Tổng hợp từ các nguồn báo uy tín và cập nhật liên tục.
        </p>
      </div>
      <div className="highlights-grid">
        {visibleArticles.map((article, index) => {
          const publishedDate = article.publishedDate
            ? new Date(article.publishedDate).toLocaleDateString("vi-VN")
            : "Chưa cập nhật";

          return (
            <article
              key={article.id}
              className={`highlight-card ${
                index === 0 ? "featured" : "compact"
              }`}
              onClick={() => onArticleClick(article)}
            >
              <div className="highlight-media">
                {article.topImageUrl ? (
                  <img src={article.topImageUrl} alt={article.title} />
                ) : (
                  <div className="highlight-placeholder">
                    <i className="bi bi-newspaper"></i>
                  </div>
                )}
                <div className="highlight-overlay"></div>
              </div>
              <div className="highlight-body">
                <div className="highlight-meta">
                  {article.generatorIdName && (
                    <span className="highlight-source">
                      Báo {article.generatorIdName}
                    </span>
                  )}
                  <span className="highlight-date">{publishedDate}</span>
                </div>
                <h3 className="highlight-title">{article.title}</h3>
                {index === 0 && article.summary && (
                  <p className="highlight-summary">{article.summary}</p>
                )}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
};

export default LatestHighlights;
