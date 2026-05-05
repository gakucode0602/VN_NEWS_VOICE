-- V10__convert_varchar_article_ids_to_uuid.sql
-- Bridge migration for environments that already applied an earlier V9 where article ids were VARCHAR.
-- If ids are already UUID, this migration is a no-op.

DO $$
DECLARE
    article_id_type TEXT;
    articleblock_article_id_type TEXT;
    articlelike_article_id_type TEXT;
BEGIN
    SELECT data_type
    INTO article_id_type
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'article' AND column_name = 'id';

    SELECT data_type
    INTO articleblock_article_id_type
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'articleblock' AND column_name = 'article_id';

    SELECT data_type
    INTO articlelike_article_id_type
    FROM information_schema.columns
    WHERE table_schema = 'public' AND table_name = 'articlelike' AND column_name = 'article_id';

    IF article_id_type <> 'uuid' OR articleblock_article_id_type <> 'uuid' OR articlelike_article_id_type <> 'uuid' THEN
        -- Validate all values are convertible before altering types.
        IF EXISTS (
            SELECT 1
            FROM article
            WHERE id IS NULL OR NOT (id ~* '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$' OR id ~ '^[0-9]+$')
        ) THEN
            RAISE EXCEPTION 'article.id contains non-convertible values for UUID migration';
        END IF;

        IF EXISTS (
            SELECT 1
            FROM articleblock
            WHERE article_id IS NULL OR NOT (article_id ~* '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$' OR article_id ~ '^[0-9]+$')
        ) THEN
            RAISE EXCEPTION 'articleblock.article_id contains non-convertible values for UUID migration';
        END IF;

        IF EXISTS (
            SELECT 1
            FROM articlelike
            WHERE article_id IS NULL OR NOT (article_id ~* '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$' OR article_id ~ '^[0-9]+$')
        ) THEN
            RAISE EXCEPTION 'articlelike.article_id contains non-convertible values for UUID migration';
        END IF;

        ALTER TABLE articleblock DROP CONSTRAINT IF EXISTS articleblock_article_id_fkey;
        ALTER TABLE articlelike DROP CONSTRAINT IF EXISTS articlelike_article_id_fkey;

        -- Ensure no sequence default remains from legacy BIGSERIAL.
        ALTER TABLE article ALTER COLUMN id DROP DEFAULT;

        IF article_id_type <> 'uuid' THEN
            ALTER TABLE article
                ALTER COLUMN id TYPE UUID
                USING (
                    CASE
                        WHEN id ~* '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$' THEN id::UUID
                        WHEN id ~ '^[0-9]+$' THEN lpad(to_hex(id::BIGINT), 32, '0')::UUID
                    END
                );
        END IF;

        IF articleblock_article_id_type <> 'uuid' THEN
            ALTER TABLE articleblock
                ALTER COLUMN article_id TYPE UUID
                USING (
                    CASE
                        WHEN article_id ~* '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$' THEN article_id::UUID
                        WHEN article_id ~ '^[0-9]+$' THEN lpad(to_hex(article_id::BIGINT), 32, '0')::UUID
                    END
                );
        END IF;

        IF articlelike_article_id_type <> 'uuid' THEN
            ALTER TABLE articlelike
                ALTER COLUMN article_id TYPE UUID
                USING (
                    CASE
                        WHEN article_id ~* '^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$' THEN article_id::UUID
                        WHEN article_id ~ '^[0-9]+$' THEN lpad(to_hex(article_id::BIGINT), 32, '0')::UUID
                    END
                );
        END IF;

        ALTER TABLE articleblock
            ADD CONSTRAINT articleblock_article_id_fkey
            FOREIGN KEY (article_id) REFERENCES article(id) ON DELETE CASCADE;

        ALTER TABLE articlelike
            ADD CONSTRAINT articlelike_article_id_fkey
            FOREIGN KEY (article_id) REFERENCES article(id) ON DELETE CASCADE;
    END IF;
END $$;
