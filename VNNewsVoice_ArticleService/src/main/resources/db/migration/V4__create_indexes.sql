-- Create indexes for Article, ArticleBlock, and ArticleLike
-- FK indexes (PostgreSQL does not create them automatically)
CREATE INDEX IF NOT EXISTS idx_article_generator_id ON Article(generator_id);
CREATE INDEX IF NOT EXISTS idx_article_category_id ON Article(category_id);
CREATE INDEX IF NOT EXISTS idx_article_editor_id ON Article(editor_id);
CREATE INDEX IF NOT EXISTS idx_articleblock_article_id ON ArticleBlock(article_id);
CREATE INDEX IF NOT EXISTS idx_articlelike_article_id ON ArticleLike(article_id);
CREATE INDEX IF NOT EXISTS idx_articlelike_reader_id ON ArticleLike(reader_id);

-- Filter/sort columns
CREATE INDEX IF NOT EXISTS idx_article_published_date ON Article(published_date);
CREATE INDEX IF NOT EXISTS idx_article_is_active ON Article(is_active);
CREATE INDEX IF NOT EXISTS idx_article_created_at ON Article(created_at);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_article_active_published ON Article(is_active, published_date DESC);
