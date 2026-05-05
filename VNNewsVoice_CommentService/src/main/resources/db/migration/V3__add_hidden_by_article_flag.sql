-- V3__add_hidden_by_article_flag.sql
-- Track article-level visibility separately from user soft delete.

ALTER TABLE comment
ADD COLUMN IF NOT EXISTS hidden_by_article BOOLEAN NOT NULL DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_comment_article_visibility
ON comment (article_id, hidden_by_article, deleted_at);
