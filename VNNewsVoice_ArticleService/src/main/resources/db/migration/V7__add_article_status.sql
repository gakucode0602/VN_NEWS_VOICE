-- Add status column to Article for detailed article state tracking
ALTER TABLE Article ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'PENDING';

CREATE INDEX IF NOT EXISTS idx_article_status ON Article(status);
