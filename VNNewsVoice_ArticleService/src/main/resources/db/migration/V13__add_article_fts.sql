-- ============================================================
-- V13: PostgreSQL Full-Text Search for article table
-- Scope: title (weight A) + summary (weight B)
-- Config: vn_unaccent — unaccent + simple so users can search
--         without diacritics ("kinh te" finds "kinh tế")
-- ============================================================

-- 1. Enable unaccent extension
CREATE EXTENSION IF NOT EXISTS unaccent;

-- 2. Create a text-search configuration that strips diacritics
--    before indexing (idempotent: DO block guards duplicate creation)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_ts_config WHERE cfgname = 'vn_unaccent'
  ) THEN
    CREATE TEXT SEARCH CONFIGURATION vn_unaccent (COPY = simple);
    ALTER TEXT SEARCH CONFIGURATION vn_unaccent
      ALTER MAPPING FOR hword, hword_part, word WITH unaccent, simple;
  END IF;
END
$$;

-- 3. Add the tsvector column (nullable; filled by trigger + backfill below)
ALTER TABLE article ADD COLUMN IF NOT EXISTS search_vector tsvector;

-- 4. GIN index for fast @@ lookups  (O(log n) vs O(n) sequential scan)
CREATE INDEX IF NOT EXISTS idx_article_search_vector
  ON article USING GIN(search_vector);

-- 5. Trigger function: keep search_vector in sync on INSERT / UPDATE
CREATE OR REPLACE FUNCTION article_search_vector_update()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  NEW.search_vector :=
    setweight(to_tsvector('vn_unaccent', coalesce(NEW.title,   '')), 'A') ||
    setweight(to_tsvector('vn_unaccent', coalesce(NEW.summary, '')), 'B');
  RETURN NEW;
END;
$$;

-- Drop and recreate to avoid duplicate trigger error on re-run
DROP TRIGGER IF EXISTS trg_article_search_vector ON article;
CREATE TRIGGER trg_article_search_vector
  BEFORE INSERT OR UPDATE OF title, summary
  ON article
  FOR EACH ROW EXECUTE FUNCTION article_search_vector_update();

-- 6. Backfill existing rows
UPDATE article
SET search_vector =
  setweight(to_tsvector('vn_unaccent', coalesce(title,   '')), 'A') ||
  setweight(to_tsvector('vn_unaccent', coalesce(summary, '')), 'B');
