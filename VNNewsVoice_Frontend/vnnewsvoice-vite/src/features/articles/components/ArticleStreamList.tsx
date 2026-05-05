import type { Article } from "../../../types";

type ArticleStreamListProps = {
  articles: Article[];
  onArticleClick: (article: Article) => void;
  emptyMessage?: string;
};

const ArticleStreamList = ({
  articles,
  onArticleClick,
  emptyMessage = "Không có bài viết nào.",
}: ArticleStreamListProps) => {
  if (articles.length === 0) {
    return (
      <div className="stream-empty">
        <p>{emptyMessage}</p>
      </div>
    );
  }

  return (
    <div className="stream-list">
      {articles.map((article) => {
        const publishedDate = article.publishedDate
          ? new Date(article.publishedDate).toLocaleDateString("vi-VN")
          : "Chưa cập nhật";

        return (
          <article
            key={article.id}
            className="stream-item"
            onClick={() => onArticleClick(article)}
          >
            <div className="stream-media">
              {article.topImageUrl ? (
                <img src={article.topImageUrl} alt={article.title} />
              ) : (
                <div className="stream-placeholder">
                  <i className="bi bi-newspaper"></i>
                </div>
              )}
            </div>
            <div className="stream-body">
              <div className="stream-meta">
                {article.generatorIdName ? (
                  <span className="stream-source">
                    Báo {article.generatorIdName}
                  </span>
                ) : (
                  <span className="stream-source">Nguồn đang cập nhật</span>
                )}
                <span className="stream-date">{publishedDate}</span>
              </div>
              <h3 className="stream-title">{article.title}</h3>
              <p className="stream-summary">
                {article.summary
                  ? article.summary
                  : "Chưa có phần tóm tắt cho bài viết này."}
              </p>
            </div>
          </article>
        );
      })}
    </div>
  );
};

export default ArticleStreamList;
