-- Add top image URL to Article
ALTER TABLE Article ADD COLUMN IF NOT EXISTS top_image_url VARCHAR(500);

CREATE INDEX IF NOT EXISTS idx_article_top_image ON Article(top_image_url);
