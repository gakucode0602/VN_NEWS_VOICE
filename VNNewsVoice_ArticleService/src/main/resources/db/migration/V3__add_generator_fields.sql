-- Add RSS and scheduling fields to Generator
ALTER TABLE Generator ADD COLUMN IF NOT EXISTS rss_url VARCHAR(500);
ALTER TABLE Generator ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE Generator ADD COLUMN IF NOT EXISTS crawl_interval_minutes INT DEFAULT 5;
