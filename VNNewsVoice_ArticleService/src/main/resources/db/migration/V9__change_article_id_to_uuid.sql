-- V9__change_article_id_to_uuid.sql

-- Drop default value (sequence) on article.id
ALTER TABLE article ALTER COLUMN id DROP DEFAULT;

-- Alter article.id to UUID
-- cascade will attempt to drop the foreign key constraints or views if needed, but it might fail so we explicitly drop FKs
ALTER TABLE articleblock DROP CONSTRAINT IF EXISTS articleblock_article_id_fkey;
ALTER TABLE articlelike DROP CONSTRAINT IF EXISTS articlelike_article_id_fkey;

-- Convert legacy BIGINT ids to deterministic UUIDs so existing relations are preserved.
-- Example: id=1 => 00000000-0000-0000-0000-000000000001
ALTER TABLE article
	ALTER COLUMN id TYPE UUID
	USING lpad(to_hex(id), 32, '0')::UUID;

-- Alter article_id columns in dependent tables
ALTER TABLE articleblock
	ALTER COLUMN article_id TYPE UUID
	USING lpad(to_hex(article_id), 32, '0')::UUID;

ALTER TABLE articlelike
	ALTER COLUMN article_id TYPE UUID
	USING lpad(to_hex(article_id), 32, '0')::UUID;

-- Add foreign keys back
ALTER TABLE articleblock ADD CONSTRAINT articleblock_article_id_fkey FOREIGN KEY (article_id) REFERENCES article(id) ON DELETE CASCADE;
ALTER TABLE articlelike ADD CONSTRAINT articlelike_article_id_fkey FOREIGN KEY (article_id) REFERENCES article(id) ON DELETE CASCADE;


