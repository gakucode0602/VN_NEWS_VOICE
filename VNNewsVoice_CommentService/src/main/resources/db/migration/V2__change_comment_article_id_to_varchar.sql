-- V2__change_comment_article_id_to_varchar.sql
-- Migrate comment.article_id from BIGINT to VARCHAR to support UUID article IDs.
-- Existing numeric IDs are preserved as text values.

ALTER TABLE comment
ALTER COLUMN article_id TYPE VARCHAR(64)
USING article_id::text;
