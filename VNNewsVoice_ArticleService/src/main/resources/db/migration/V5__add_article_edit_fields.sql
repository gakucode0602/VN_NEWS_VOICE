-- Add article edit tracking and soft-delete fields
ALTER TABLE Article ADD COLUMN IF NOT EXISTS is_being_edited BOOLEAN DEFAULT FALSE;
ALTER TABLE Article ADD COLUMN IF NOT EXISTS edit_started_at TIMESTAMP;
ALTER TABLE Article ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP;

CREATE INDEX IF NOT EXISTS idx_article_is_being_edited ON Article(is_being_edited);
CREATE INDEX IF NOT EXISTS idx_article_edit_started_at ON Article(edit_started_at);
CREATE INDEX IF NOT EXISTS idx_article_deleted_at ON Article(deleted_at);
