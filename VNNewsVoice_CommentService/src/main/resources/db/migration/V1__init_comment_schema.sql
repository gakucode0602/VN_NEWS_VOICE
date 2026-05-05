-- V1__init_comment_schema.sql
-- CommentService — comment_db
-- Cross-service references (article_id, user_id) are stored as plain BIGINT — no FK to external DBs.
-- comment_reply_id is a self-reference within comment_db — FK is safe here.

CREATE TABLE comment
(
    id               BIGSERIAL PRIMARY KEY,
    content          TEXT         NOT NULL,
    article_id       BIGINT       NOT NULL,       -- ref ArticleService article_db (no FK — cross-service)
    user_id          BIGINT       NOT NULL,       -- ref AuthService auth_db (no FK — cross-service)
    username         VARCHAR(255) NOT NULL,       -- denormalized at write time from JWT claim
    comment_reply_id BIGINT REFERENCES comment (id) ON DELETE SET NULL, -- self-ref OK (same DB)
    created_at       TIMESTAMP DEFAULT NOW(),
    deleted_at       TIMESTAMP                    -- soft delete: NULL = active, non-NULL = deleted
);

CREATE TABLE comment_like
(
    id         BIGSERIAL PRIMARY KEY,
    comment_id BIGINT NOT NULL REFERENCES comment (id) ON DELETE CASCADE,
    user_id    BIGINT NOT NULL,                   -- ref AuthService auth_db (no FK — cross-service)
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (comment_id, user_id)                  -- 1 user can only like each comment once
);

-- Indexes for common query patterns
CREATE INDEX idx_comment_article_id ON comment (article_id);
CREATE INDEX idx_comment_user_id ON comment (user_id);
CREATE INDEX idx_comment_reply_id ON comment (comment_reply_id);
CREATE INDEX idx_comment_created_at ON comment (created_at DESC);
CREATE INDEX idx_comment_like_comment_id ON comment_like (comment_id);
CREATE INDEX idx_comment_like_user_id ON comment_like (user_id);
